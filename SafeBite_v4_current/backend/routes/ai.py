from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai.hygiene.hygiene_detector import normalize_detection
from ai.ocr.expiry_detector import classify_expiry, extract_expiry_date

from ..database import get_db
from ..models import AIDetection, Alert, Device, Restaurant
from ..schemas import ExpiryDetectionRequest, HygieneDetectionRequest
from ..services.blockchain_service import create_audit_record
from ..services.risk_service import calculate_ai_risk

router = APIRouter(prefix="/ai", tags=["AI"])


def resolve_restaurant_and_device(db: Session, restaurant_id: int, device_id: str | None):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    device = None
    if device_id:
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.restaurant_id == restaurant_id,
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found for restaurant")

    return restaurant, device


@router.post("/expiry")
def expiry_detection(payload: ExpiryDetectionRequest, db: Session = Depends(get_db)):
    restaurant, device = resolve_restaurant_and_device(db, payload.restaurant_id, payload.device_id)
    expiry_date = extract_expiry_date(payload.text)
    status = classify_expiry(expiry_date)

    detection = AIDetection(
        detection_type=f"EXPIRY_{status}",
        confidence=payload.confidence,
        description=f"OCR text: {payload.text}",
        image_path=payload.image_path,
        restaurant_id=restaurant.id,
        device_id=device.id if device else None,
    )
    db.add(detection)
    db.flush()

    if status == "EXPIRED":
        risk = calculate_ai_risk("EXPIRED", payload.confidence)
    elif status == "NEAR_EXPIRY":
        risk = {"risk_score": 70, "severity": "AMBER", "reasons": ["Product approaching expiry"]}
    else:
        risk = {"risk_score": 100, "severity": "GREEN", "reasons": []}

    alert = None
    if risk["severity"] in {"ORANGE", "RED"}:
        alert = Alert(
            alert_type="EXPIRY_RISK",
            severity=risk["severity"],
            risk_score=risk["risk_score"],
            reason=", ".join(risk["reasons"]),
            source="AI",
            status="OPEN",
            restaurant_id=restaurant.id,
            device_id=device.id if device else None,
        )
        db.add(alert)
        db.flush()
        create_audit_record(
            db,
            "AI_ALERT_CREATED",
            "ALERT",
            alert.id,
            None,
            {
                "restaurant_id": restaurant.id,
                "detection_id": detection.id,
                "detection_status": status,
            },
        )

    db.commit()

    return {
        "detection": {
            "id": detection.id,
            "status": status,
            "expiry_date": expiry_date,
            "confidence": detection.confidence,
        },
        "risk": risk,
        "alert": {
            "id": alert.id,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
        } if alert else None,
    }


@router.post("/hygiene")
def hygiene_detection(payload: HygieneDetectionRequest, db: Session = Depends(get_db)):
    restaurant, device = resolve_restaurant_and_device(db, payload.restaurant_id, payload.device_id)
    normalized = normalize_detection(payload.label, payload.confidence)

    detection = AIDetection(
        detection_type=normalized["label"],
        confidence=normalized["confidence"],
        description=payload.description,
        image_path=payload.image_path,
        restaurant_id=restaurant.id,
        device_id=device.id if device else None,
    )
    db.add(detection)
    db.flush()

    risk = calculate_ai_risk(normalized["label"], normalized["confidence"])

    alert = None
    if normalized["is_actionable"] and risk["severity"] in {"ORANGE", "RED"}:
        alert = Alert(
            alert_type="HYGIENE_RISK",
            severity=risk["severity"],
            risk_score=risk["risk_score"],
            reason=", ".join(risk["reasons"]),
            source="AI",
            status="OPEN",
            restaurant_id=restaurant.id,
            device_id=device.id if device else None,
        )
        db.add(alert)
        db.flush()
        create_audit_record(
            db,
            "AI_HYGIENE_ALERT_CREATED",
            "ALERT",
            alert.id,
            None,
            {
                "restaurant_id": restaurant.id,
                "detection_id": detection.id,
                "label": normalized["label"],
            },
        )

    db.commit()

    return {
        "detection": normalized,
        "risk": risk,
        "alert": {
            "id": alert.id,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
        } if alert else None,
    }
