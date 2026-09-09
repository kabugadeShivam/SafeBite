from datetime import datetime
from pathlib import Path
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Alert,
    BlockchainRecord,
    Device,
    Evidence,
    GovernmentOfficer,
    Investigation,
    Restaurant,
    SensorReading,
)
from ..schemas import InvestigationUpdate, InvestigationVerify, LoginRequest, OfficerCreate
from ..security import create_access_token, get_token_payload, hash_password, verify_password
from ..services.blockchain_service import create_audit_record, verify_audit_chain

router = APIRouter(prefix="/government", tags=["Government"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "evidence"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_current_officer(payload=Depends(get_token_payload), db: Session = Depends(get_db)):
    officer = db.query(GovernmentOfficer).filter(GovernmentOfficer.id == int(payload["sub"])).first()
    if not officer or officer.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="Officer account is inactive or missing")
    return officer


def enforce_region(officer: GovernmentOfficer, restaurant: Restaurant):
    if officer.role == "CENTRAL_ADMIN":
        return
    if officer.state.strip().lower() != restaurant.state.strip().lower() or officer.region.strip().lower() != restaurant.region.strip().lower():
        raise HTTPException(status_code=403, detail="You are not authorized for this region")


def serialize_alert(alert: Alert):
    return {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "risk_score": alert.risk_score,
        "reason": alert.reason,
        "source": alert.source,
        "status": alert.status,
        "timestamp": alert.timestamp,
        "restaurant": {
            "id": alert.restaurant.id,
            "name": alert.restaurant.name,
            "registration_id": alert.restaurant.registration_id,
            "location": alert.restaurant.location,
            "state": alert.restaurant.state,
            "region": alert.restaurant.region,
        },
        "device": {
            "id": alert.device.id,
            "device_id": alert.device.device_id,
            "device_type": alert.device.device_type,
            "status": alert.device.status,
            "last_seen_at": alert.device.last_seen_at,
        } if alert.device else None,
    }


@router.post("/login")
def government_login(payload: LoginRequest, db: Session = Depends(get_db)):
    officer = db.query(GovernmentOfficer).filter(GovernmentOfficer.username == payload.username).first()
    if not officer or not verify_password(payload.password, officer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if officer.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Officer account is inactive")

    token = create_access_token(officer.id, officer.role, officer.region)
    return {
        "access_token": token,
        "token_type": "bearer",
        "officer": {
            "id": officer.id,
            "officer_id": officer.officer_id,
            "name": officer.name,
            "role": officer.role,
            "state": officer.state,
            "region": officer.region,
        },
    }


@router.get("/me")
def government_me(officer: GovernmentOfficer = Depends(get_current_officer)):
    return {
        "officer_id": officer.officer_id,
        "name": officer.name,
        "role": officer.role,
        "state": officer.state,
        "region": officer.region,
    }


@router.post("/officers")
def create_officer(
    payload: OfficerCreate,
    current: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    if current.role != "CENTRAL_ADMIN":
        raise HTTPException(status_code=403, detail="Only Central Admin can create officers")

    if db.query(GovernmentOfficer).filter(GovernmentOfficer.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    officer = GovernmentOfficer(
        officer_id=payload.officer_id,
        name=payload.name,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        state=payload.state.strip(),
        region=payload.region.strip(),
    )
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return {"message": "Officer created", "officer_id": officer.officer_id}


@router.get("/dashboard")
def government_dashboard(officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    query = db.query(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(Restaurant.state == officer.state, Restaurant.region == officer.region)
    restaurants = query.all()
    restaurant_ids = [r.id for r in restaurants]

    alerts = []
    if restaurant_ids:
        alerts = db.query(Alert).filter(Alert.restaurant_id.in_(restaurant_ids)).all()

    active_statuses = {"OPEN", "UNDER_INVESTIGATION", "ACTION_REQUIRED"}
    critical = sum(1 for a in alerts if a.severity == "RED" and a.status in active_statuses)
    high = sum(1 for a in alerts if a.severity == "ORANGE" and a.status in active_statuses)
    investigations = db.query(Investigation).join(Alert).filter(Alert.restaurant_id.in_(restaurant_ids)).all() if restaurant_ids else []
    pending_investigations = sum(1 for i in investigations if i.status != "CLOSED")

    devices = db.query(Device).filter(Device.restaurant_id.in_(restaurant_ids)).all() if restaurant_ids else []
    online_devices = sum(1 for d in devices if d.status == "ONLINE")

    latest_alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:10]

    return {
        "region": {
            "state": officer.state,
            "region": "ALL" if officer.role == "CENTRAL_ADMIN" else officer.region,
        },
        "counts": {
            "establishments": len(restaurants),
            "devices": len(devices),
            "online_devices": online_devices,
            "critical_alerts": critical,
            "high_risk_alerts": high,
            "pending_investigations": pending_investigations,
        },
        "latest_alerts": [serialize_alert(a) for a in latest_alerts],
    }


@router.get("/alerts")
def government_alerts(
    status_filter: str | None = None,
    severity: str | None = None,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).join(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(Restaurant.state == officer.state, Restaurant.region == officer.region)
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())

    alerts = query.order_by(Alert.timestamp.desc()).all()
    return {"total": len(alerts), "alerts": [serialize_alert(a) for a in alerts]}


@router.get("/alerts/{alert_id}")
def government_alert_details(alert_id: int, officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    enforce_region(officer, alert.restaurant)

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == alert.device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(25)
        .all()
    ) if alert.device_id else []

    investigation = db.query(Investigation).filter(Investigation.alert_id == alert.id).first()

    return {
        "alert": serialize_alert(alert),
        "sensor_evidence": [
            {
                "temperature": r.temperature,
                "humidity": r.humidity,
                "door_open": r.door_open,
                "timestamp": r.timestamp,
            } for r in readings
        ],
        "investigation": {
            "id": investigation.id,
            "status": investigation.status,
            "findings": investigation.findings,
            "action_taken": investigation.action_taken,
            "corrective_action": investigation.corrective_action,
            "started_at": investigation.started_at,
            "submitted_at": investigation.submitted_at,
            "verified_at": investigation.verified_at,
            "officer": investigation.officer.name,
            "evidence": [
                {
                    "id": e.id,
                    "filename": e.original_filename,
                    "sha256": e.sha256,
                    "uploaded_at": e.uploaded_at,
                } for e in investigation.evidence
            ],
        } if investigation else None,
    }


@router.post("/alerts/{alert_id}/investigate")
def start_investigation(alert_id: int, officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    enforce_region(officer, alert.restaurant)

    existing = db.query(Investigation).filter(Investigation.alert_id == alert.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Investigation already exists")

    investigation = Investigation(
        alert_id=alert.id,
        officer_id=officer.id,
        status="IN_PROGRESS",
        findings="Investigation started",
        action_taken="Pending",
    )
    alert.status = "UNDER_INVESTIGATION"
    db.add(investigation)
    db.flush()

    create_audit_record(
        db=db,
        record_type="INVESTIGATION_STARTED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={"alert_id": alert.id, "restaurant_id": alert.restaurant_id},
    )
    db.commit()
    db.refresh(investigation)
    return {"message": "Investigation started", "investigation_id": investigation.id, "status": investigation.status}


@router.put("/investigations/{investigation_id}")
def update_investigation(
    investigation_id: int,
    payload: InvestigationUpdate,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    enforce_region(officer, investigation.alert.restaurant)

    if investigation.officer_id != officer.id and officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="You are not the assigned officer for this case")

    allowed_statuses = {"IN_PROGRESS", "ACTION_REQUIRED", "PENDING_VERIFICATION"}
    if payload.status.upper() not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(allowed_statuses)}")

    investigation.findings = payload.findings
    investigation.action_taken = payload.action_taken
    investigation.corrective_action = payload.corrective_action
    investigation.status = payload.status.upper()
    investigation.submitted_at = datetime.utcnow()
    investigation.alert.status = "ACTION_REQUIRED" if investigation.status == "ACTION_REQUIRED" else "UNDER_INVESTIGATION"

    create_audit_record(
        db=db,
        record_type="FINDINGS_SUBMITTED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "findings": investigation.findings,
            "action_taken": investigation.action_taken,
            "corrective_action": investigation.corrective_action,
            "status": investigation.status,
        },
    )
    db.commit()
    return {"message": "Investigation updated", "status": investigation.status}


@router.post("/investigations/{investigation_id}/evidence")
def upload_evidence(
    investigation_id: int,
    file: UploadFile = File(...),
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    enforce_region(officer, investigation.alert.restaurant)
    if investigation.officer_id != officer.id and officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="You are not assigned to this investigation")

    content = file.file.read()
    digest = hashlib.sha256(content).hexdigest()
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'evidence').name}"
    stored_path = UPLOAD_DIR / safe_name
    stored_path.write_bytes(content)

    evidence = Evidence(
        investigation_id=investigation.id,
        original_filename=file.filename or "evidence",
        stored_path=str(stored_path),
        content_type=file.content_type,
        sha256=digest,
        uploaded_by=officer.id,
    )
    db.add(evidence)
    db.flush()

    create_audit_record(
        db=db,
        record_type="EVIDENCE_UPLOADED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={"filename": evidence.original_filename, "sha256": evidence.sha256},
    )
    db.commit()
    return {"message": "Evidence uploaded", "evidence_id": evidence.id, "sha256": evidence.sha256}


@router.post("/investigations/{investigation_id}/verify")
def verify_investigation(
    investigation_id: int,
    payload: InvestigationVerify,
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    if officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="Only Supervisor or Central Admin can verify investigations")

    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    enforce_region(officer, investigation.alert.restaurant)

    if payload.decision.upper() != "APPROVE":
        investigation.status = "ACTION_REQUIRED"
        investigation.alert.status = "ACTION_REQUIRED"
        create_audit_record(
            db=db,
            record_type="INVESTIGATION_RETURNED",
            entity_type="INVESTIGATION",
            entity_id=investigation.id,
            actor_id=officer.id,
            payload={"remarks": payload.remarks},
        )
        db.commit()
        return {"message": "Investigation returned for correction", "status": investigation.status}

    investigation.status = "CLOSED"
    investigation.verified_at = datetime.utcnow()
    investigation.verified_by = officer.id
    investigation.alert.status = "CLOSED"

    audit = create_audit_record(
        db=db,
        record_type="INVESTIGATION_VERIFIED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "findings": investigation.findings,
            "action_taken": investigation.action_taken,
            "corrective_action": investigation.corrective_action,
            "remarks": payload.remarks,
        },
    )
    db.commit()
    return {
        "message": "Investigation verified and case closed",
        "status": investigation.status,
        "audit_record_id": audit.id,
        "record_hash": audit.record_hash,
    }


@router.get("/investigations")
def list_investigations(officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    query = db.query(Investigation).join(Alert).join(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(Restaurant.state == officer.state, Restaurant.region == officer.region)
    investigations = query.order_by(Investigation.started_at.desc()).all()

    return {
        "total": len(investigations),
        "investigations": [
            {
                "id": i.id,
                "status": i.status,
                "started_at": i.started_at,
                "submitted_at": i.submitted_at,
                "verified_at": i.verified_at,
                "officer": i.officer.name,
                "alert": {
                    "id": i.alert.id,
                    "severity": i.alert.severity,
                    "risk_score": i.alert.risk_score,
                    "reason": i.alert.reason,
                    "status": i.alert.status,
                },
                "restaurant": {
                    "id": i.alert.restaurant.id,
                    "name": i.alert.restaurant.name,
                    "region": i.alert.restaurant.region,
                },
            }
            for i in investigations
        ],
    }


@router.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: int, officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    enforce_region(officer, investigation.alert.restaurant)

    return {
        "id": investigation.id,
        "status": investigation.status,
        "started_at": investigation.started_at,
        "submitted_at": investigation.submitted_at,
        "verified_at": investigation.verified_at,
        "officer": investigation.officer.name,
        "findings": investigation.findings,
        "action_taken": investigation.action_taken,
        "corrective_action": investigation.corrective_action,
        "alert": serialize_alert(investigation.alert),
        "evidence": [
            {
                "id": e.id,
                "filename": e.original_filename,
                "sha256": e.sha256,
                "uploaded_at": e.uploaded_at,
            } for e in investigation.evidence
        ],
    }


@router.get("/investigations/{investigation_id}/audit")
def get_investigation_audit(investigation_id: int, officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    enforce_region(officer, investigation.alert.restaurant)

    records = (
        db.query(BlockchainRecord)
        .filter(
            BlockchainRecord.entity_type == "INVESTIGATION",
            BlockchainRecord.entity_id == investigation.id,
        )
        .order_by(BlockchainRecord.timestamp.asc())
        .all()
    )
    valid, message = verify_audit_chain(db)

    return {
        "investigation_id": investigation.id,
        "chain_verified": valid,
        "chain_message": message,
        "records": [
            {
                "id": r.id,
                "record_type": r.record_type,
                "timestamp": r.timestamp,
                "payload_hash": r.payload_hash,
                "previous_hash": r.previous_hash,
                "record_hash": r.record_hash,
                "blockchain_tx_id": r.blockchain_tx_id,
                "verification_status": r.verification_status,
            }
            for r in records
        ],
    }


@router.get("/establishments")
def establishments(officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    query = db.query(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(Restaurant.state == officer.state, Restaurant.region == officer.region)
    restaurants = query.order_by(Restaurant.name.asc()).all()

    result = []
    for r in restaurants:
        alerts = db.query(Alert).filter(Alert.restaurant_id == r.id).all()
        active = [a for a in alerts if a.status != "CLOSED"]
        result.append({
            "id": r.id,
            "name": r.name,
            "registration_id": r.registration_id,
            "location": r.location,
            "state": r.state,
            "region": r.region,
            "status": r.status,
            "active_alerts": len(active),
            "critical_alerts": sum(1 for a in active if a.severity == "RED"),
            "devices": len(r.devices),
        })
    return {"total": len(result), "establishments": result}


@router.get("/devices")
def government_devices(officer: GovernmentOfficer = Depends(get_current_officer), db: Session = Depends(get_db)):
    query = db.query(Device).join(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(Restaurant.state == officer.state, Restaurant.region == officer.region)
    devices = query.order_by(Device.last_seen_at.desc()).all()

    return {
        "total": len(devices),
        "devices": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "device_type": d.device_type,
                "status": d.status,
                "last_seen_at": d.last_seen_at,
                "restaurant": d.restaurant.name,
            } for d in devices
        ],
    }
