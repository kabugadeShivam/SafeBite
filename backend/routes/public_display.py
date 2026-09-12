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
from ..services.regional_auditor import audit_region


router = APIRouter(
    prefix="/public",
    tags=["Public SafeBite"],
)


PUBLIC_STATUS_MAP = {
    "EXCELLENT": "EXCELLENT",
    "COMPLIANT": "GOOD",
    "WATCHLIST": "WATCH",
    "WARNING": "POOR",
    "CRITICAL": "CRITICAL",
}


# ============================================================
# PUBLIC OUTLET STATUS
# ============================================================

@router.get(
    "/outlets/{registration_id}"
)
def public_outlet_status(
    registration_id: str,
    db: Session = Depends(get_db),
):
    outlet = (
        db.query(Restaurant)
        .filter(
            Restaurant.registration_id
            == registration_id
        )
        .first()
    )

    if not outlet:
        raise HTTPException(
            status_code=404,
            detail="Outlet not found",
        )

    # --------------------------------------------------------
    # Deterministic official audit remains the fallback.
    # --------------------------------------------------------

    audit = audit_region(
        db=db,
        state=outlet.state,
        region=outlet.region,
        days=30,
    )

    outlet_audit = next(
        (
            item
            for item in audit["inspection_priority_queue"]
            if item["outlet"]["id"] == outlet.id
        ),
        None,
    )

    if not outlet_audit:
        raise HTTPException(
            status_code=404,
            detail="Audit data not available",
        )

    # --------------------------------------------------------
    # Latest monthly AI assessment.
    #
    # This is the public-facing cleanliness/performance result.
    # The AI result is advisory and derived from official audit
    # evidence; it never becomes the legal authority.
    # --------------------------------------------------------

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

    public_score = outlet_audit["compliance_score"]
    public_status = PUBLIC_STATUS_MAP.get(
        str(outlet_audit["status"]).upper(),
        "WATCH",
    )
    public_comment = (
        "Monthly food-safety performance is being monitored."
    )
    public_audit_month = None
    public_ai_model = None
    public_assessment_at = None

    if monthly_ai:
        public_score = monthly_ai.score
        public_status = monthly_ai.public_status
        public_comment = monthly_ai.ai_comment
        public_audit_month = monthly_ai.audit_month
        public_ai_model = monthly_ai.ai_model
        public_assessment_at = monthly_ai.created_at

    # ========================================================
    # LATEST VERIFIED INVESTIGATION
    # ========================================================

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
            "investigation_id":
                verified_investigation.id,
            "alert_id":
                verified_investigation.alert_id,
            "decision":
                "VERIFIED",
            "status":
                verified_investigation.status,
            "verified_at":
                verified_investigation.verified_at,
            "corrective_action":
                verified_investigation.corrective_action
                or None,
        }

    # ========================================================
    # PUBLIC RESPONSE
    # ========================================================

    return {
        "source":
            "SafeBite Government Platform",

        "outlet": {
            "name": outlet.name,
            "registration_id": outlet.registration_id,
            "location": outlet.location,
            "state": outlet.state,
            "region": outlet.region,
        },

        "official_status": {
            # Citizen-friendly monthly AI score.
            "compliance_score": public_score,
            "status": public_status,
            "public_comment": public_comment,
            "audit_month": public_audit_month,
            "ai_model": public_ai_model,
            "assessment_at": public_assessment_at,

            # Internal government monitoring signals remain
            # available only as the non-public operational layer.
            "inspection_priority":
                outlet_audit["inspection_priority"],
            "risk_trend":
                outlet_audit["risk_trend"],
            "generated_at":
                audit["generated_at"],
            "latest_verified_outcome":
                latest_verified_outcome,
        },

        "public_summary": {
            "strengths":
                outlet_audit["strengths"],
            "concerns":
                outlet_audit["concerns"],
            "recommendation":
                outlet_audit["recommendation"],
        },

        "latest_verified_outcome":
            latest_verified_outcome,

        "display_control": {
            "controlled_by":
                "Government SafeBite Platform",
            "owner_can_edit": False,
            "ai_is_final_authority": False,
        },
    }
