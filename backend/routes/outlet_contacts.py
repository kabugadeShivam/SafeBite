from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GovernmentOfficer, Restaurant
from ..models_monthly import OutletContact
from ..security import get_token_payload


router = APIRouter(
    prefix="/government/outlet-contacts",
    tags=["Outlet Contacts"],
)


class OutletContactPayload(BaseModel):
    official_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    active: bool = True



def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> GovernmentOfficer:
    try:
        officer_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
        ) from exc

    officer = (
        db.query(GovernmentOfficer)
        .filter(GovernmentOfficer.id == officer_id)
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



def _get_outlet_for_officer(
    db: Session,
    officer: GovernmentOfficer,
    restaurant_id: int,
) -> Restaurant:
    outlet = (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )

    if not outlet:
        raise HTTPException(
            status_code=404,
            detail="Outlet not found",
        )

    if officer.role.upper() != "CENTRAL_ADMIN":
        if (
            outlet.state.strip().lower()
            != officer.state.strip().lower()
            or outlet.region.strip().lower()
            != officer.region.strip().lower()
        ):
            raise HTTPException(
                status_code=403,
                detail="Outlet is outside your authorized region",
            )

    return outlet


@router.get("/{restaurant_id}")
def get_outlet_contact(
    restaurant_id: int,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    outlet = _get_outlet_for_officer(
        db,
        officer,
        restaurant_id,
    )

    contact = (
        db.query(OutletContact)
        .filter(
            OutletContact.restaurant_id == restaurant_id
        )
        .first()
    )

    return {
        "outlet": {
            "id": outlet.id,
            "name": outlet.name,
            "registration_id": outlet.registration_id,
        },
        "contact": (
            {
                "id": contact.id,
                "official_name": contact.official_name,
                "email": contact.email,
                "phone": contact.phone,
                "active": contact.active,
                "updated_at": contact.updated_at,
            }
            if contact
            else None
        ),
    }


@router.put("/{restaurant_id}")
def upsert_outlet_contact(
    restaurant_id: int,
    payload: OutletContactPayload,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    outlet = _get_outlet_for_officer(
        db,
        officer,
        restaurant_id,
    )

    email = (payload.email or "").strip() or None
    phone = (payload.phone or "").strip() or None

    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="At least one email or phone number is required",
        )

    contact = (
        db.query(OutletContact)
        .filter(
            OutletContact.restaurant_id == restaurant_id
        )
        .first()
    )

    if contact is None:
        contact = OutletContact(
            restaurant_id=restaurant_id,
            official_name=payload.official_name.strip(),
            email=email,
            phone=phone,
            active=payload.active,
            updated_at=datetime.utcnow(),
        )
        db.add(contact)
    else:
        contact.official_name = payload.official_name.strip()
        contact.email = email
        contact.phone = phone
        contact.active = payload.active
        contact.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(contact)

    return {
        "message": "Outlet contact saved",
        "outlet": {
            "id": outlet.id,
            "name": outlet.name,
            "registration_id": outlet.registration_id,
        },
        "contact": {
            "id": contact.id,
            "official_name": contact.official_name,
            "email": contact.email,
            "phone": contact.phone,
            "active": contact.active,
            "updated_at": contact.updated_at,
        },
    }
