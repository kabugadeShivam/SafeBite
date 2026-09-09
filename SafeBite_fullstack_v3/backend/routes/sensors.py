from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Device, SensorReading
from ..schemas import SensorReadingCreate
from ..services.risk_service import calculate_risk_score
from ..services.blockchain_service import create_audit_record

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post("/readings")
def submit_sensor_reading(payload: SensorReadingCreate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = datetime.utcnow()
    device.status = "ONLINE"
    device.last_seen_at = now

    reading = SensorReading(
        temperature=payload.temperature,
        humidity=payload.humidity,
        door_open=payload.door_open,
        timestamp=now,
        device_id=device.id,
    )
    db.add(reading)
    db.flush()

    risk = calculate_risk_score(payload.temperature, payload.humidity, payload.door_open)
    alert = None

    if risk["severity"] in {"ORANGE", "RED"}:
        cutoff = now - timedelta(minutes=10)
        alert = (
            db.query(Alert)
            .filter(
                Alert.device_id == device.id,
                Alert.alert_type == "ENVIRONMENTAL_RISK",
                Alert.status.in_(["OPEN", "UNDER_INVESTIGATION", "ACTION_REQUIRED"]),
                Alert.timestamp >= cutoff,
            )
            .order_by(Alert.timestamp.desc())
            .first()
        )

        if not alert:
            alert = Alert(
                alert_type="ENVIRONMENTAL_RISK",
                severity=risk["severity"],
                risk_score=risk["risk_score"],
                reason=", ".join(risk["reasons"]),
                source="IOT",
                status="OPEN",
                timestamp=now,
                restaurant_id=device.restaurant_id,
                device_id=device.id,
                sensor_reading_id=reading.id,
            )
            db.add(alert)
            db.flush()

            create_audit_record(
                db,
                "ALERT_CREATED",
                "ALERT",
                alert.id,
                None,
                {
                    "restaurant_id": device.restaurant_id,
                    "device_id": device.id,
                    "severity": alert.severity,
                    "risk_score": alert.risk_score,
                    "reason": alert.reason,
                },
            )

    db.commit()
    db.refresh(reading)
    if alert:
        db.refresh(alert)

    return {
        "message": "Sensor reading received",
        "reading": {
            "id": reading.id,
            "device_id": device.device_id,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "door_open": reading.door_open,
            "timestamp": reading.timestamp,
        },
        "risk": risk,
        "alert": {
            "id": alert.id,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "status": alert.status,
        } if alert else None,
    }
