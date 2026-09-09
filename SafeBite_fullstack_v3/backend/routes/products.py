from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, Restaurant
from ..schemas import ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])


def classify(expiry_date: str | None) -> str:
    if not expiry_date:
        return "UNKNOWN"
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            expiry = datetime.strptime(expiry_date.strip(), fmt).date()
            days = (expiry - datetime.utcnow().date()).days
            if days < 0:
                return "EXPIRED"
            if days <= 7:
                return "NEAR_EXPIRY"
            return "SAFE"
        except ValueError:
            continue
    return "UNKNOWN"


@router.post("/")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    product = Product(
        name=payload.name.strip(),
        batch_number=payload.batch_number,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        status=classify(payload.expiry_date),
        restaurant_id=restaurant.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Product created", "product": {
        "id": product.id,
        "name": product.name,
        "batch_number": product.batch_number,
        "manufacturing_date": product.manufacturing_date,
        "expiry_date": product.expiry_date,
        "status": product.status,
        "restaurant_id": product.restaurant_id,
    }}


@router.get("/")
def list_products(restaurant_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.restaurant_id == restaurant_id).all()
    return {"total": len(products), "products": [
        {
            "id": p.id,
            "name": p.name,
            "batch_number": p.batch_number,
            "expiry_date": p.expiry_date,
            "status": p.status,
        }
        for p in products
    ]}
