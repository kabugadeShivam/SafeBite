from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Device, GovernmentOfficer, Restaurant
from .security import hash_password

Base.metadata.create_all(bind=engine)

db: Session = SessionLocal()
try:
    admin = db.query(GovernmentOfficer).filter(GovernmentOfficer.username == "admin").first()
    if not admin:
        admin = GovernmentOfficer(
            officer_id="SB-ADMIN-001",
            name="SafeBite Central Administrator",
            username="admin",
            password_hash=hash_password("Admin@12345"),
            role="CENTRAL_ADMIN",
            state="Maharashtra",
            region="All",
        )
        db.add(admin)

    officer = db.query(GovernmentOfficer).filter(GovernmentOfficer.username == "officer_nm").first()
    if not officer:
        officer = GovernmentOfficer(
            officer_id="MH-NM-001",
            name="Navi Mumbai Regional Food Safety Officer",
            username="officer_nm",
            password_hash=hash_password("SafeBite@123"),
            role="REGIONAL_OFFICER",
            state="Maharashtra",
            region="Navi Mumbai",
        )
        db.add(officer)

    supervisor = db.query(GovernmentOfficer).filter(GovernmentOfficer.username == "supervisor_nm").first()
    if not supervisor:
        supervisor = GovernmentOfficer(
            officer_id="MH-NM-SUP-001",
            name="Navi Mumbai Supervising Officer",
            username="supervisor_nm",
            password_hash=hash_password("SafeBite@123"),
            role="SUPERVISOR",
            state="Maharashtra",
            region="Navi Mumbai",
        )
        db.add(supervisor)

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
        device = Device(
            device_id="SB-MGM-ESP32-001",
            device_type="ESP32",
            restaurant_id=restaurant.id,
            status="OFFLINE",
        )
        db.add(device)

    db.commit()
    print("Demo seed complete.")
    print("Admin      : admin / Admin@12345")
    print("Regional   : officer_nm / SafeBite@123")
    print("Supervisor : supervisor_nm / SafeBite@123")
finally:
    db.close()
