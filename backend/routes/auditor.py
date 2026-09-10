
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GovernmentOfficer
from ..services.regional_auditor_intelligence import (
    audit_region_with_citizen_intelligence,
)
from .government import get_current_officer


router = APIRouter(
    prefix="/government/auditor",
    tags=["AI Regional Auditor"],
)


@router.get("/regional")
def regional_audit(
    state: str | None = None,
    region: str | None = None,
    days: int = 30,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    # Regional officers can only audit their own region.
    if officer.role != "CENTRAL_ADMIN":
        state = officer.state
        region = officer.region

    return audit_region_with_citizen_intelligence(
        db=db,
        state=state,
        region=region,
        days=days,
    )
