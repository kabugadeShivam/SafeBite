from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class SensorReadingCreate(BaseModel):
    device_id: str
    temperature: float
    humidity: float
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


class ProductCreate(BaseModel):
    name: str
    batch_number: str | None = None
    manufacturing_date: str | None = None
    expiry_date: str | None = None
    restaurant_id: int
