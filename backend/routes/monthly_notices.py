from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    GovernmentOfficer,
    MonthlyAuditNotice,
    Restaurant,
)
from ..security import get_token_payload
from ..services.monthly_notice_service import (
    generate_monthly_notices,
)


router = APIRouter(
    prefix="/government/monthly-notices",
    tags=["Monthly Audit Notices"],
)


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(
            payload["sub"]
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
        )

    officer = (
        db.query(GovernmentOfficer)
        .filter(
            GovernmentOfficer.id
            == officer_id
        )
        .first()
    )

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Officer not found",
        )

    if officer.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=401,
            detail="Officer account is inactive",
        )

    return officer


# ============================================================
# GENERATE MONTHLY NOTICES
# ============================================================

@router.post("/generate")
def generate_notices(
    audit_month: str | None = None,
    state: str | None = None,
    region: str | None = None,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Default to current UTC month.
    # --------------------------------------------------------

    if audit_month is None:
        audit_month = (
            datetime.utcnow()
            .strftime("%Y-%m")
        )

    # --------------------------------------------------------
    # Validate month format.
    # --------------------------------------------------------

    try:
        datetime.strptime(
            audit_month,
            "%Y-%m",
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="audit_month must use YYYY-MM format",
        )

    # --------------------------------------------------------
    # Regional officers are restricted to their own scope.
    # Central Admin may specify another scope.
    # --------------------------------------------------------

    if officer.role.upper() != "CENTRAL_ADMIN":
        state = officer.state
        region = officer.region

    result = generate_monthly_notices(
        db=db,
        state=state,
        region=region,
        audit_month=audit_month,
        actor_id=officer.id,
    )

    return result


# ============================================================
# LIST MONTHLY NOTICES
# ============================================================

@router.get("")
def list_monthly_notices(
    audit_month: str | None = None,
    notice_type: str | None = None,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    if audit_month is None:
        audit_month = (
            datetime.utcnow()
            .strftime("%Y-%m")
        )

    try:
        datetime.strptime(
            audit_month,
            "%Y-%m",
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="audit_month must use YYYY-MM format",
        )

    query = (
        db.query(
            MonthlyAuditNotice
        )
        .join(
            Restaurant,
            MonthlyAuditNotice.restaurant_id
            == Restaurant.id,
        )
        .filter(
            MonthlyAuditNotice.audit_month
            == audit_month,
        )
    )

    # --------------------------------------------------------
    # Restrict regional officers.
    # --------------------------------------------------------

    if officer.role.upper() != "CENTRAL_ADMIN":

        query = query.filter(
            Restaurant.state
            == officer.state,

            Restaurant.region
            == officer.region,
        )

    # --------------------------------------------------------
    # Optional notice-type filter.
    # --------------------------------------------------------

    if notice_type:

        normalized_type = (
            notice_type
            .strip()
            .upper()
        )

        if normalized_type not in {
            "APPRECIATION",
            "WARNING",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "notice_type must be "
                    "APPRECIATION or WARNING"
                ),
            )

        query = query.filter(
            MonthlyAuditNotice.notice_type
            == normalized_type
        )

    notices = (
        query
        .order_by(
            MonthlyAuditNotice.issued_at.desc()
        )
        .all()
    )

    result = []

    for notice in notices:

        restaurant = (
            db.query(Restaurant)
            .filter(
                Restaurant.id
                == notice.restaurant_id
            )
            .first()
        )

        try:
            strengths = json.loads(
                notice.strengths
                or "[]"
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            strengths = []

        try:
            concerns = json.loads(
                notice.concerns
                or "[]"
            )

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            concerns = []

        result.append(
            {
                "id":
                    notice.id,

                "audit_month":
                    notice.audit_month,

                "notice_type":
                    notice.notice_type,

                "title":
                    notice.title,

                "message":
                    notice.message,

                "outlet": {
                    "id":
                        restaurant.id
                        if restaurant
                        else notice.restaurant_id,

                    "name":
                        restaurant.name
                        if restaurant
                        else "Unknown outlet",

                    "registration_id":
                        (
                            restaurant.registration_id
                            if restaurant
                            else None
                        ),

                    "state":
                        (
                            restaurant.state
                            if restaurant
                            else None
                        ),

                    "region":
                        (
                            restaurant.region
                            if restaurant
                            else None
                        ),
                },

                "audit": {
                    "compliance_score":
                        notice.compliance_score,

                    "status":
                        notice.compliance_status,

                    "inspection_priority":
                        notice.inspection_priority,

                    "risk_trend":
                        notice.risk_trend,

                    "strengths":
                        strengths,

                    "concerns":
                        concerns,

                    "recommendation":
                        notice.recommendation,
                },

                "delivery_status":
                    notice.delivery_status,

                "issued_at":
                    notice.issued_at,
            }
        )

    return {
        "audit_month":
            audit_month,

        "count":
            len(result),

        "notices":
            result,
    }


# ============================================================
# GET ONE NOTICE
# ============================================================

@router.get("/{notice_id}")
def get_monthly_notice(
    notice_id: int,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    notice = (
        db.query(
            MonthlyAuditNotice
        )
        .filter(
            MonthlyAuditNotice.id
            == notice_id
        )
        .first()
    )

    if not notice:
        raise HTTPException(
            status_code=404,
            detail="Monthly notice not found",
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == notice.restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Associated outlet not found",
        )

    # --------------------------------------------------------
    # Regional authorization
    # --------------------------------------------------------

    if officer.role.upper() != "CENTRAL_ADMIN":

        if (
            restaurant.state
            != officer.state
            or restaurant.region
            != officer.region
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Notice is outside your "
                    "authorized region"
                ),
            )

    try:
        strengths = json.loads(
            notice.strengths
            or "[]"
        )

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        strengths = []

    try:
        concerns = json.loads(
            notice.concerns
            or "[]"
        )

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        concerns = []

    return {
        "id":
            notice.id,

        "audit_month":
            notice.audit_month,

        "notice_type":
            notice.notice_type,

        "title":
            notice.title,

        "message":
            notice.message,

        "outlet": {
            "id":
                restaurant.id,

            "name":
                restaurant.name,

            "registration_id":
                restaurant.registration_id,

            "location":
                restaurant.location,

            "state":
                restaurant.state,

            "region":
                restaurant.region,
        },

        "audit": {
            "compliance_score":
                notice.compliance_score,

            "status":
                notice.compliance_status,

            "inspection_priority":
                notice.inspection_priority,

            "risk_trend":
                notice.risk_trend,

            "strengths":
                strengths,

            "concerns":
                concerns,

            "recommendation":
                notice.recommendation,
        },

        "delivery_status":
            notice.delivery_status,

        "issued_at":
            notice.issued_at,
    }