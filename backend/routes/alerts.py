from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Restaurant, Device, SensorReading


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


# ------------------------------------------------------------
# GET ALL ALERTS
# ------------------------------------------------------------

@router.get("/")
def get_alerts(
    db: Session = Depends(get_db)
):
    alerts = db.query(Alert).order_by(
        Alert.timestamp.desc()
    ).all()

    result = []

    for alert in alerts:

        restaurant = db.query(Restaurant).filter(
            Restaurant.id == alert.restaurant_id
        ).first()

        result.append({
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "reason": alert.reason,
            "status": alert.status,
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "location": restaurant.location,
                "registration_id": restaurant.registration_id
            } if restaurant else None,
            "timestamp": alert.timestamp
        })

    return {
        "total_alerts": len(result),
        "alerts": result
    }


# ------------------------------------------------------------
# GET SINGLE ALERT — DETAILED INVESTIGATION VIEW
# ------------------------------------------------------------

@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):

    alert = db.query(Alert).filter(
        Alert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    # Restaurant
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == alert.restaurant_id
    ).first()

    # Devices belonging to restaurant
    devices = db.query(Device).filter(
        Device.restaurant_id == alert.restaurant_id
    ).all()

    # Recent sensor readings from those devices
    device_ids = [device.id for device in devices]

    recent_readings = []

    if device_ids:
        readings = db.query(SensorReading).filter(
            SensorReading.device_id.in_(device_ids)
        ).order_by(
            SensorReading.timestamp.desc()
        ).limit(10).all()

        recent_readings = [
            {
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "door_open": reading.door_open,
                "timestamp": reading.timestamp
            }
            for reading in readings
        ]

    return {
        "alert": {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "reason": alert.reason,
            "status": alert.status,
            "timestamp": alert.timestamp
        },

        "restaurant": {
            "id": restaurant.id,
            "name": restaurant.name,
            "location": restaurant.location,
            "registration_id": restaurant.registration_id
        } if restaurant else None,

        "devices": [
            {
                "id": device.id,
                "device_id": device.device_id,
                "device_type": device.device_type,
                "status": device.status
            }
            for device in devices
        ],

        "recent_sensor_readings": recent_readings
    }