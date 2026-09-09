from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Device, Restaurant
from ..schemas import DeviceCreate

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/")
def register_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    if db.query(Device).filter(Device.device_id == payload.device_id).first():
        raise HTTPException(status_code=400, detail="Device ID already registered")

    device = Device(
        device_id=payload.device_id,
        device_type=payload.device_type,
        restaurant_id=restaurant.id,
        status="OFFLINE",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return {"message": "Device registered", "device": {
        "id": device.id,
        "device_id": device.device_id,
        "device_type": device.device_type,
        "restaurant_id": device.restaurant_id,
        "status": device.status,
    }}
