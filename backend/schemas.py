from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class SensorReadingCreate(BaseModel):
    device_id: str
    temperature: float
    humidity: Optional[float] = None
    door_open: bool = False


class RestaurantCreate(BaseModel):
    name: str
    location: str
    state: str
    region: str
    registration_id: str


class DeviceCreate(BaseModel):
    device_id: str
    device_type: str = "ESP32"
    restaurant_id: int


class OfficerCreate(BaseModel):
    officer_id: str
    name: str
    username: str
    password: str = Field(min_length=8)
    role: str = "REGIONAL_OFFICER"
    state: str
    region: str


class InvestigationUpdate(BaseModel):
    findings: str
    action_taken: str
    corrective_action: str = ""
    status: str


class InvestigationVerify(BaseModel):
    decision: str = "APPROVE"
    remarks: str = ""
