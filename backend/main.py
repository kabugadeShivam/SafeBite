from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine

from .routes.devices import router as devices_router
from .routes.government import router as government_router
from .routes.restaurants import router as restaurants_router
from .routes.sensors import router as sensors_router
from .routes.ai import router as ai_router
from .routes.auditor import router as auditor_router
from .routes.public_display import router as public_display_router
from .routes.citizen_reports import (
    public_router as citizen_public_router,
    government_router as citizen_government_router,
)
from .routes.audit_history import router as audit_history_router

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="SafeBite Government Food Safety Platform",
    description=(
        "IoT + AI food-safety monitoring with "
        "regional government alerts, auditable "
        "investigations, and blockchain-backed audit records."
    ),
    version="3.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROUTERS
# ============================================================

app.include_router(restaurants_router)
app.include_router(devices_router)
app.include_router(sensors_router)
app.include_router(government_router)
app.include_router(ai_router)
app.include_router(auditor_router)
app.include_router(public_display_router)
app.include_router(citizen_public_router)
app.include_router(citizen_government_router)
app.include_router(audit_history_router)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SafeBite API",
        "version": "3.0.0",
    }