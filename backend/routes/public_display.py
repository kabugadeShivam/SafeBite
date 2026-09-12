from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Alert,
    Investigation,
    Restaurant,
)
from ..services.regional_auditor import audit_region


router = APIRouter(
    prefix="/public",
    tags=["Public SafeBite"],
)


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
    # --------------------------------------------------------
    # Find outlet
    # --------------------------------------------------------

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
    # Existing official regional audit
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
            for item
            in audit[
                "inspection_priority_queue"
            ]
            if item[
                "outlet"
            ][
                "id"
            ]
            == outlet.id
        ),
        None,
    )

    if not outlet_audit:

        raise HTTPException(
            status_code=404,
            detail="Audit data not available",
        )

    # ========================================================
    # LATEST VERIFIED INVESTIGATION
    # ========================================================

    verified_investigation = (
        db.query(Investigation)
        .join(
            Alert,
            Investigation.alert_id
            == Alert.id,
        )
        .filter(
            Alert.restaurant_id
            == outlet.id,

            Investigation.status
            == "CLOSED",

            Investigation.verified_at
            .isnot(None),
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

            # Only expose the official corrective/action
            # outcome intended for public transparency.
            #
            # Do NOT expose:
            # - officer ID
            # - verified_by ID
            # - internal audit hashes
            # - internal government notes
            #
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
            "name":
                outlet.name,

            "registration_id":
                outlet.registration_id,

            "location":
                outlet.location,

            "state":
                outlet.state,

            "region":
                outlet.region,
        },

        # ----------------------------------------------------
        # Existing official status
        # ----------------------------------------------------

        "official_status": {
            "compliance_score":
                outlet_audit[
                    "compliance_score"
                ],

            "status":
                outlet_audit[
                    "status"
                ],

            "inspection_priority":
                outlet_audit[
                    "inspection_priority"
                ],

            "risk_trend":
                outlet_audit[
                    "risk_trend"
                ],

            "generated_at":
                audit[
                    "generated_at"
                ],

            "latest_verified_outcome":
                latest_verified_outcome,
        },

        # ----------------------------------------------------
        # Public government summary
        # ----------------------------------------------------

        "public_summary": {
            "strengths":
                outlet_audit[
                    "strengths"
                ],

            "concerns":
                outlet_audit[
                    "concerns"
                ],

            "recommendation":
                outlet_audit[
                    "recommendation"
                ],
        },

        # ----------------------------------------------------
        # Official investigation outcome
        #
        # This is deliberately separate from AI status.
        # ----------------------------------------------------

        "latest_verified_outcome":
            latest_verified_outcome,

        # ----------------------------------------------------
        # Display control
        # ----------------------------------------------------

        "display_control": {
            "controlled_by":
                "Government SafeBite Platform",

            "owner_can_edit":
                False,

            "ai_is_final_authority":
                False,
        },
    }