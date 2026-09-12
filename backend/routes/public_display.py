from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Alert,
    Investigation,
    Restaurant,
)
from ..models_monthly import MonthlyAIAnalysis
from ..services.monthly_ai_analyzer import public_status_from_score
from ..services.regional_auditor_intelligence import (
    audit_region_with_citizen_intelligence,
)


router = APIRouter(
    prefix="/public",
    tags=["Public SafeBite"],
)


@router.get("/outlets/{registration_id}")
def public_outlet_status(
    registration_id: str,
    db: Session = Depends(get_db),
):
    outlet = (
        db.query(Restaurant)
        .filter(
            Restaurant.registration_id == registration_id
        )
        .first()
    )

    if not outlet:
        raise HTTPException(
            status_code=404,
            detail="Outlet not found",
        )

    # This same official citizen-aware audit source feeds the monthly
    # assessment. It keeps public and government data grounded in the
    # same evidence while exposing only public-safe fields below.
    audit = audit_region_with_citizen_intelligence(
        db=db,
        state=outlet.state,
        region=outlet.region,
        days=30,
    )

    outlet_audit = next(
        (
            item
            for item in audit.get(
                "inspection_priority_queue",
                [],
            )
            if item.get("outlet", {}).get("id") == outlet.id
        ),
        None,
    )

    if not outlet_audit:
        raise HTTPException(
            status_code=404,
            detail="Audit data not available",
        )

    monthly_ai = (
        db.query(MonthlyAIAnalysis)
        .filter(
            MonthlyAIAnalysis.restaurant_id == outlet.id,
        )
        .order_by(
            MonthlyAIAnalysis.audit_month.desc(),
            MonthlyAIAnalysis.created_at.desc(),
        )
        .first()
    )

    if monthly_ai:
        public_score = float(monthly_ai.score)
        public_status = monthly_ai.public_status
        public_comment = monthly_ai.ai_comment
        public_audit_month = monthly_ai.audit_month
        public_assessment_at = monthly_ai.created_at
    else:
        public_score = float(
            outlet_audit.get("compliance_score", 0)
        )
        public_status = public_status_from_score(
            public_score
        )
        concerns = outlet_audit.get("concerns") or []
        public_comment = (
            " ".join(str(concerns[0]).split())
            if concerns
            else "Monthly food-safety assessment is pending."
        )
        public_audit_month = None
        public_assessment_at = audit.get("generated_at")

    # --------------------------------------------------------
    # Latest verified investigation outcome
    # --------------------------------------------------------
    verified_investigation = (
        db.query(Investigation)
        .join(
            Alert,
            Investigation.alert_id == Alert.id,
        )
        .filter(
            Alert.restaurant_id == outlet.id,
            Investigation.status == "CLOSED",
            Investigation.verified_at.isnot(None),
        )
        .order_by(
            Investigation.verified_at.desc()
        )
        .first()
    )

    latest_verified_outcome = None

    if verified_investigation:
        latest_verified_outcome = {
            "investigation_id": verified_investigation.id,
            "alert_id": verified_investigation.alert_id,
            "decision": "VERIFIED",
            "status": verified_investigation.status,
            "verified_at": verified_investigation.verified_at,
            "corrective_action": (
                verified_investigation.corrective_action
                or None
            ),
        }

    # --------------------------------------------------------
    # Public response
    # --------------------------------------------------------
    return {
        "source": "SafeBite Government Platform",
        "outlet": {
            "name": outlet.name,
            "registration_id": outlet.registration_id,
            "location": outlet.location,
            "state": outlet.state,
            "region": outlet.region,
        },
        "official_status": {
            "compliance_score": public_score,
            "status": public_status,
            "public_comment": public_comment,
            "audit_month": public_audit_month,
            "assessment_at": public_assessment_at,
            "latest_verified_outcome": latest_verified_outcome,
        },
        "public_summary": {
            "strengths": outlet_audit.get("strengths", []),
            "concerns": outlet_audit.get("concerns", []),
            "recommendation": outlet_audit.get(
                "recommendation",
                "Continue monitoring official food-safety status.",
            ),
        },
        "latest_monthly_assessment": (
            {
                "audit_month": monthly_ai.audit_month,
                "score": monthly_ai.score,
                "status": monthly_ai.public_status,
                "comment": monthly_ai.ai_comment,
            }
            if monthly_ai
            else None
        ),
        "latest_verified_outcome": latest_verified_outcome,
        "display_control": {
            "controlled_by": "Government SafeBite Platform",
            "owner_can_edit": False,
            "ai_is_final_authority": False,
        },
    }
