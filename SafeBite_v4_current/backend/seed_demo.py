from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Device, GovernmentOfficer, Restaurant
from .security import hash_password

Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()
try:
    accounts = [
        ("SB-ADMIN-001", "SafeBite Central Administrator", "admin", "Admin@12345", "CENTRAL_ADMIN", "Maharashtra", "All"),
        ("MH-NM-001", "Navi Mumbai Regional Food Safety Officer", "officer_nm", "SafeBite@123", "REGIONAL_OFFICER", "Maharashtra", "Navi Mumbai"),
        ("MH-NM-SUP-001", "Navi Mumbai Supervising Officer", "supervisor_nm", "SafeBite@123", "SUPERVISOR", "Maharashtra", "Navi Mumbai"),
    ]

    for officer_id, name, username, password, role, state, region in accounts:
        existing = db.query(GovernmentOfficer).filter(GovernmentOfficer.username == username).first()
        if not existing:
            db.add(GovernmentOfficer(
                officer_id=officer_id,
                name=name,
                username=username,
                password_hash=hash_password(password),
                role=role,
                state=state,
                region=region,
            ))

    restaurant = db.query(Restaurant).filter(Restaurant.registration_id == "SB-MGM-001").first()
    if not restaurant:
        restaurant = Restaurant(
            name="MGM College Canteen",
            location="MGM College Campus",
            state="Maharashtra",
            region="Navi Mumbai",
            registration_id="SB-MGM-001",
        )
        db.add(restaurant)
        db.flush()

    device = db.query(Device).filter(Device.device_id == "SB-MGM-ESP32-001").first()
    if not device:
        db.add(Device(
            device_id="SB-MGM-ESP32-001",
            device_type="ESP32",
            restaurant_id=restaurant.id,
            status="OFFLINE",
        ))

    db.commit()
    print("Demo seed complete.")
    print("Admin      : admin / Admin@12345")
    print("Regional   : officer_nm / SafeBite@123")
    print("Supervisor : supervisor_nm / SafeBite@123")
finally:
    db.close()
