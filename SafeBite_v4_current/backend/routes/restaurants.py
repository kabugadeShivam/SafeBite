from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Restaurant
from ..schemas import RestaurantCreate

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.post("/")
def create_restaurant(payload: RestaurantCreate, db: Session = Depends(get_db)):
    if db.query(Restaurant).filter(Restaurant.registration_id == payload.registration_id).first():
        raise HTTPException(status_code=400, detail="Registration ID already exists")

    restaurant = Restaurant(
        name=payload.name,
        location=payload.location,
        state=payload.state.strip(),
        region=payload.region.strip(),
        registration_id=payload.registration_id.strip(),
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return {"message": "Restaurant registered", "restaurant": {
        "id": restaurant.id,
        "name": restaurant.name,
        "location": restaurant.location,
        "state": restaurant.state,
        "region": restaurant.region,
        "registration_id": restaurant.registration_id,
        "status": restaurant.status,
    }}
