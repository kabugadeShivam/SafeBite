from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes.devices import router as devices_router
from .routes.government import router as government_router
from .routes.restaurants import router as restaurants_router
from .routes.sensors import router as sensors_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SafeBite Government Food Safety Platform",
    description="IoT + AI food-safety monitoring with regional government alerts and auditable investigations",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(restaurants_router)
app.include_router(devices_router)
app.include_router(sensors_router)
app.include_router(government_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "SafeBite API", "version": "2.0.0"}
