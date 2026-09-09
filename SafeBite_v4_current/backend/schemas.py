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
    findings: str = Field(min_length=3)
    action_taken: str = Field(min_length=3)
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


class ExpiryDetectionRequest(BaseModel):
    restaurant_id: int
    device_id: str | None = None
    text: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    image_path: str | None = None


class HygieneDetectionRequest(BaseModel):
    restaurant_id: int
    device_id: str | None = None
    label: str = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str = ""
    image_path: str | None = None
