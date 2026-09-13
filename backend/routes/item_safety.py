from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ai.hygiene.hygiene_detector import analyze_hygiene
from ai.ocr.expiry_detector import analyze_expiry

from ..database import get_db
from ..models import AIDetection, Device, GovernmentOfficer, Investigation, Restaurant, SensorReading
from ..security import get_token_payload
from ..services.blockchain_service import create_audit_record
from ..services.item_safety_service import assess_item


router = APIRouter(
    prefix="/ai/item-safety",
    tags=["AI Item Safety"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads" / "ai"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authorization token") from exc

    officer = db.query(GovernmentOfficer).filter(GovernmentOfficer.id == officer_id).first()
    if not officer or officer.status.upper() != "ACTIVE":
        raise HTTPException(status_code=401, detail="Officer account is unavailable")
    return officer


def _save_image(file: UploadFile) -> Path:
    suffix = Path(file.filename or "item.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
        raise HTTPException(status_code=400, detail="Allowed image types: jpg, jpeg, png, webp, bmp")

    destination = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    destination.write_bytes(content)
    return destination


def _latest_storage_reading(db: Session, restaurant_id: int):
    return (
        db.query(SensorReading)
        .join(Device, SensorReading.device_id == Device.id)
        .filter(Device.restaurant_id == restaurant_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )


def _authorized_restaurant(
    db: Session,
    officer: GovernmentOfficer,
    restaurant_id: int,
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if officer.role.upper() != "CENTRAL_ADMIN":
        if restaurant.state != officer.state or restaurant.region != officer.region:
            raise HTTPException(status_code=403, detail="Outlet is outside your authorized region")

    return restaurant


@router.post("")
def item_safety_scan(
    file: UploadFile = File(...),
    restaurant_id: int | None = None,
    investigation_id: int | None = None,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    investigation = None
    if investigation_id is not None:
        investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        restaurant_id = investigation.alert.restaurant_id

    restaurant = None
    if restaurant_id is not None:
        restaurant = _authorized_restaurant(db, officer, restaurant_id)

    image_path = _save_image(file)

    try:
        expiry = analyze_expiry(image_path)
        vision = analyze_hygiene(image_path)

        reading = _latest_storage_reading(db, restaurant.id) if restaurant else None

        assessment = assess_item(
            expiry=expiry,
            vision=vision,
            temperature=reading.temperature if reading else None,
            humidity=reading.humidity if reading else None,
            door_open=reading.door_open if reading else None,
        )

        stored_detection_id = None
        if restaurant:
            expiry_status = str(expiry.get("status") or "NOT_FOUND").upper()
            detection = AIDetection(
                detection_type=f"item_expiry_{expiry_status.lower()}",
                confidence=None,
                description=json.dumps(
                    {
                        "expiry": expiry,
                        "assessment": assessment,
                    },
                    default=str,
                ),
                image_path=None,
                restaurant_id=restaurant.id,
                device_id=reading.device_id if reading else None,
            )
            db.add(detection)
            db.flush()
            stored_detection_id = detection.id

        audit = None
        if investigation:
            audit = create_audit_record(
                db=db,
                record_type="AI_ITEM_SAFETY_SCAN",
                entity_type="INVESTIGATION",
                entity_id=investigation.id,
                actor_id=officer.id,
                payload={
                    "filename": file.filename,
                    "restaurant_id": restaurant_id,
                    "expiry": expiry,
                    "vision": vision,
                    "assessment": assessment,
                },
            )

        if stored_detection_id is not None or audit is not None:
            db.commit()

        return {
            "service": "item_safety",
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "registration_id": restaurant.registration_id,
            } if restaurant else None,
            "investigation_id": investigation_id,
            "assessment": assessment,
            "expiry": expiry,
            "vision": {
                "success": vision.get("success", False),
                "status": vision.get("status"),
                "risk_score": vision.get("risk_score"),
                "detections": vision.get("detections", []),
                "message": vision.get("message"),
            },
            "storage": {
                "available": reading is not None,
                "temperature": reading.temperature if reading else None,
                "humidity": reading.humidity if reading else None,
                "door_open": reading.door_open if reading else None,
                "timestamp": reading.timestamp if reading else None,
            },
            "stored_detection_id": stored_detection_id,
            "audit": {
                "id": audit.id,
                "record_hash": audit.record_hash,
                "blockchain_tx_id": audit.blockchain_tx_id,
                "verification_status": audit.verification_status,
            } if audit else None,
        }
    finally:
        image_path.unlink(missing_ok=True)
