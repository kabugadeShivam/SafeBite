
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Restaurant
from ..services.regional_auditor import audit_region


router = APIRouter(
    prefix="/public",
    tags=["Public SafeBite"]
)


@router.get("/outlets/{registration_id}")
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

    return {
        "source": "SafeBite Government Platform",

        "outlet": {
            "name": outlet.name,
            "registration_id":
                outlet.registration_id,
            "location":
                outlet.location,
            "state":
                outlet.state,
            "region":
                outlet.region,
        },

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
            "generated_at":
                audit["generated_at"],
        },

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

        "display_control": {
            "controlled_by":
                "Government SafeBite Platform",
            "owner_can_edit":
                False,
        },
    }

