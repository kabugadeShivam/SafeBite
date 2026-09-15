import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models_monthly  # noqa: F401
from .routes.devices import router as devices_router
from .routes.government import router as government_router
from .routes.restaurants import router as restaurants_router
from .routes.sensors import router as sensors_router
from .routes.ai import router as ai_router
from .routes.auditor import router as auditor_router
from .routes.public_display import router as public_display_router
from .routes.item_safety import router as item_safety_router
from .routes.citizen_reports import public_router as citizen_public_router, government_router as citizen_government_router, investigation_router as citizen_investigation_router
from .routes.audit_history import router as audit_history_router
from .routes.command_center import router as command_center_router
from .routes.monthly_notices import router as monthly_notices_router
from .routes.outlet_contacts import router as outlet_contacts_router
from .routes.officer_action_queue import router as officer_action_queue_router
from .services.monthly_scheduler import start_monthly_scheduler

Base.metadata.create_all(bind=engine)

# Prototype bootstrap: Render starts from an empty Postgres database, so the
# registered demo officer, outlet, and ESP32 device are seeded only when the
# environment flag is explicitly enabled. The seed script is idempotent.
if os.getenv("SAFEBITE_BOOTSTRAP_DEMO", "false").lower() == "true":
    from . import seed_demo  # noqa: F401,E402

app = FastAPI(
    title="SafeBite Government Food Safety Platform",
    description="IoT + AI food-safety monitoring with regional government alerts, auditable investigations, citizen evidence, automated monthly AI assessments, item-level checks, outlet notices, and blockchain-backed audit records.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(.+)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "SafeBite API", "status": "online", "version": "3.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "SafeBite API", "version": "3.0.0"}

app.include_router(restaurants_router)
app.include_router(devices_router)
app.include_router(sensors_router)
app.include_router(government_router)
app.include_router(ai_router)
app.include_router(item_safety_router)
app.include_router(auditor_router)
app.include_router(public_display_router)
app.include_router(citizen_public_router)
app.include_router(citizen_government_router)
app.include_router(citizen_investigation_router)
app.include_router(audit_history_router)
app.include_router(command_center_router)
app.include_router(monthly_notices_router)
app.include_router(outlet_contacts_router)
app.include_router(officer_action_queue_router)

@app.on_event("startup")
def start_background_services():
    start_monthly_scheduler()
