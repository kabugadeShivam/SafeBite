from datetime import datetime
from pathlib import Path
import hashlib
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
from ..services.blockchain_service import create_audit_record, verify_audit_chain, anchor_record_to_evm

router = APIRouter(prefix="/government", tags=["Government"])
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "evidence"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ACTIVE_ALERT_STATUSES = {"OPEN", "UNDER_INVESTIGATION", "ACTION_REQUIRED"}


def current_officer(payload=Depends(get_token_payload), db: Session = Depends(get_db)):
    try:
        officer_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authorization token") from exc

    officer = db.query(GovernmentOfficer).filter(GovernmentOfficer.id == officer_id).first()
    if not officer or officer.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="Officer account is inactive or missing")
    return officer


def enforce_region(officer: GovernmentOfficer, restaurant: Restaurant):
    if officer.role == "CENTRAL_ADMIN":
        return

    same_state = officer.state.strip().lower() == restaurant.state.strip().lower()
    same_region = officer.region.strip().lower() == restaurant.region.strip().lower()
    if not same_state or not same_region:
        raise HTTPException(status_code=403, detail="You are not authorized for this region")


def scoped_restaurant_query(officer: GovernmentOfficer, db: Session):
    query = db.query(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )
    return query


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
    officer = db.query(GovernmentOfficer).filter(
        GovernmentOfficer.username == payload.username.strip()
    ).first()

    if not officer or not verify_password(payload.password, officer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if officer.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Officer account is inactive")

    token = create_access_token(
        officer.id,
        officer.role,
        officer.state,
        officer.region,
    )

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
def government_me(officer: GovernmentOfficer = Depends(current_officer)):
    return {
        "id": officer.id,
        "officer_id": officer.officer_id,
        "name": officer.name,
        "role": officer.role,
        "state": officer.state,
        "region": officer.region,
    }


@router.post("/officers")
def create_officer(
    payload: OfficerCreate,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    if officer.role != "CENTRAL_ADMIN":
        raise HTTPException(status_code=403, detail="Only Central Admin can create officers")

    if db.query(GovernmentOfficer).filter(
        GovernmentOfficer.username == payload.username.strip()
    ).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_officer = GovernmentOfficer(
        officer_id=payload.officer_id.strip(),
        name=payload.name.strip(),
        username=payload.username.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role.strip().upper(),
        state=payload.state.strip(),
        region=payload.region.strip(),
    )
    db.add(new_officer)
    db.commit()
    db.refresh(new_officer)

    return {
        "message": "Officer created",
        "officer_id": new_officer.officer_id,
    }


@router.get("/dashboard")
def dashboard(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    restaurants = scoped_restaurant_query(officer, db).all()
    ids = [r.id for r in restaurants]

    alerts = db.query(Alert).filter(Alert.restaurant_id.in_(ids)).all() if ids else []
    investigations = db.query(Investigation).join(Alert).filter(Alert.restaurant_id.in_(ids)).all() if ids else []
    devices = db.query(Device).filter(Device.restaurant_id.in_(ids)).all() if ids else []

    counts = {
        "establishments": len(restaurants),
        "devices": len(devices),
        "online_devices": sum(1 for d in devices if d.status == "ONLINE"),
        "offline_devices": sum(1 for d in devices if d.status != "ONLINE"),
        "critical_alerts": sum(1 for a in alerts if a.severity == "RED" and a.status in ACTIVE_ALERT_STATUSES),
        "high_risk_alerts": sum(1 for a in alerts if a.severity == "ORANGE" and a.status in ACTIVE_ALERT_STATUSES),
        "warning_alerts": sum(1 for a in alerts if a.severity == "AMBER" and a.status in ACTIVE_ALERT_STATUSES),
        "pending_investigations": sum(1 for i in investigations if i.status != "CLOSED"),
        "closed_investigations": sum(1 for i in investigations if i.status == "CLOSED"),
    }

    latest = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:10]
    return {
        "region": {
            "state": officer.state,
            "region": "ALL" if officer.role == "CENTRAL_ADMIN" else officer.region,
        },
        "counts": counts,
        "latest_alerts": [serialize_alert(a) for a in latest],
    }


@router.get("/alerts")
def alerts(
    status_filter: str | None = None,
    severity: str | None = None,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).join(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )
    if status_filter:
        query = query.filter(Alert.status == status_filter.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())

    results = query.order_by(Alert.timestamp.desc()).all()
    return {"total": len(results), "alerts": [serialize_alert(a) for a in results]}


@router.get("/alerts/{alert_id}")
def alert_details(
    alert_id: int,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    enforce_region(officer, alert.restaurant)

    readings = []
    if alert.device_id:
        readings = (
            db.query(SensorReading)
            .filter(SensorReading.device_id == alert.device_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(30)
            .all()
        )

    investigation = db.query(Investigation).filter(
        Investigation.alert_id == alert.id
    ).first()

    return {
        "alert": serialize_alert(alert),
        "sensor_evidence": [
            {
                "temperature": r.temperature,
                "humidity": r.humidity,
                "door_open": r.door_open,
                "timestamp": r.timestamp,
            }
            for r in readings
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
                }
                for e in investigation.evidence
            ],
        } if investigation else None,
    }


@router.post("/alerts/{alert_id}/investigate")
def start_investigation(
    alert_id: int,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    enforce_region(officer, alert.restaurant)

    if db.query(Investigation).filter(Investigation.alert_id == alert.id).first():
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
        db,
        "INVESTIGATION_STARTED",
        "INVESTIGATION",
        investigation.id,
        officer.id,
        {
            "alert_id": alert.id,
            "restaurant_id": alert.restaurant_id,
        },
    )

    db.commit()
    db.refresh(investigation)

    return {
        "message": "Investigation started",
        "investigation_id": investigation.id,
        "status": investigation.status,
    }


@router.get("/investigations")
def list_investigations(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    query = db.query(Investigation).join(Alert).join(Restaurant)
    if officer.role != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )

    results = query.order_by(Investigation.started_at.desc()).all()

    return {
        "total": len(results),
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
            for i in results
        ],
    }


@router.get("/investigations/{investigation_id}")
def investigation_details(
    investigation_id: int,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()

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
                "content_type": e.content_type,
                "sha256": e.sha256,
                "uploaded_at": e.uploaded_at,
            }
            for e in investigation.evidence
        ],
    }


@router.put("/investigations/{investigation_id}")
def update_investigation(
    investigation_id: int,
    payload: InvestigationUpdate,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_region(officer, investigation.alert.restaurant)

    if investigation.officer_id != officer.id and officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="You are not assigned to this case")

    status_value = payload.status.strip().upper()
    allowed = {"IN_PROGRESS", "ACTION_REQUIRED", "PENDING_VERIFICATION"}
    if status_value not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of {sorted(allowed)}",
        )

    investigation.findings = payload.findings.strip()
    investigation.action_taken = payload.action_taken.strip()
    investigation.corrective_action = payload.corrective_action.strip()
    investigation.status = status_value
    investigation.submitted_at = datetime.utcnow()

    investigation.alert.status = (
        "ACTION_REQUIRED"
        if status_value == "ACTION_REQUIRED"
        else "UNDER_INVESTIGATION"
    )

    create_audit_record(
        db,
        "FINDINGS_SUBMITTED",
        "INVESTIGATION",
        investigation.id,
        officer.id,
        {
            "findings": investigation.findings,
            "action_taken": investigation.action_taken,
            "corrective_action": investigation.corrective_action,
            "status": investigation.status,
        },
    )

    db.commit()

    return {
        "message": "Investigation updated",
        "status": investigation.status,
    }


@router.post("/investigations/{investigation_id}/evidence")
def upload_evidence(
    investigation_id: int,
    file: UploadFile = File(...),
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_region(officer, investigation.alert.restaurant)

    if investigation.officer_id != officer.id and officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(status_code=403, detail="You are not assigned to this investigation")

    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Evidence file is larger than 10 MB")

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
        db,
        "EVIDENCE_UPLOADED",
        "INVESTIGATION",
        investigation.id,
        officer.id,
        {
            "filename": evidence.original_filename,
            "sha256": evidence.sha256,
        },
    )

    db.commit()
    db.refresh(evidence)

    return {
        "message": "Evidence uploaded",
        "evidence_id": evidence.id,
        "sha256": evidence.sha256,
    }


@router.post("/investigations/{investigation_id}/verify")
def verify_investigation(
    investigation_id: int,
    payload: InvestigationVerify,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    if officer.role not in {"SUPERVISOR", "CENTRAL_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Only Supervisor or Central Admin can verify investigations",
        )

    investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_region(officer, investigation.alert.restaurant)

    decision = payload.decision.strip().upper()

    if decision != "APPROVE":
        investigation.status = "ACTION_REQUIRED"
        investigation.alert.status = "ACTION_REQUIRED"

        create_audit_record(
            db,
            "INVESTIGATION_RETURNED",
            "INVESTIGATION",
            investigation.id,
            officer.id,
            {"remarks": payload.remarks},
        )

        db.commit()

        return {
            "message": "Investigation returned for correction",
            "status": investigation.status,
        }

    if not investigation.findings.strip() or not investigation.action_taken.strip():
        raise HTTPException(
            status_code=400,
            detail="Findings and action taken must be submitted before approval",
        )

    investigation.status = "CLOSED"
    investigation.verified_at = datetime.utcnow()
    investigation.verified_by = officer.id
    investigation.alert.status = "CLOSED"

    audit = create_audit_record(
        db,
        "INVESTIGATION_VERIFIED",
        "INVESTIGATION",
        investigation.id,
        officer.id,
        {
            "findings": investigation.findings,
            "action_taken": investigation.action_taken,
            "corrective_action": investigation.corrective_action,
            "remarks": payload.remarks,
        },
    )

    db.commit()

    # Optional on-chain anchoring. Local audit remains valid if the EVM node
    # is not configured or temporarily unavailable.
    try:
        tx_id = anchor_record_to_evm(
            audit.record_hash,
            "INVESTIGATION",
            investigation.id,
        )
    except Exception:
        tx_id = None

    if tx_id:
        audit.blockchain_tx_id = tx_id
        audit.verification_status = "EVM_ANCHORED"
        db.commit()

    return {
        "message": "Investigation verified and case closed",
        "status": investigation.status,
        "audit_record_id": audit.id,
        "record_hash": audit.record_hash,
        "blockchain_tx_id": tx_id,
        "verification_status": audit.verification_status,
    }


@router.get("/establishments")
def establishments(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    results = scoped_restaurant_query(officer, db).order_by(Restaurant.name.asc()).all()

    return {
        "total": len(results),
        "establishments": [
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "registration_id": restaurant.registration_id,
                "location": restaurant.location,
                "state": restaurant.state,
                "region": restaurant.region,
                "status": restaurant.status,
                "devices": [
                    {
                        "device_id": d.device_id,
                        "device_type": d.device_type,
                        "status": d.status,
                        "last_seen_at": d.last_seen_at,
                    }
                    for d in restaurant.devices
                ],
            }
            for restaurant in results
        ],
    }


@router.get("/devices")
def devices(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    restaurants = scoped_restaurant_query(officer, db).all()
    ids = [r.id for r in restaurants]
    results = db.query(Device).filter(Device.restaurant_id.in_(ids)).all() if ids else []

    return {
        "total": len(results),
        "devices": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "device_type": d.device_type,
                "status": d.status,
                "last_seen_at": d.last_seen_at,
                "restaurant": {
                    "id": d.restaurant.id,
                    "name": d.restaurant.name,
                    "region": d.restaurant.region,
                },
            }
            for d in results
        ],
    }


@router.get("/reports/summary")
def report_summary(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    restaurants = scoped_restaurant_query(officer, db).all()
    ids = [r.id for r in restaurants]
    alerts = db.query(Alert).filter(Alert.restaurant_id.in_(ids)).all() if ids else []
    investigations = db.query(Investigation).join(Alert).filter(Alert.restaurant_id.in_(ids)).all() if ids else []

    severity_counts = {"GREEN": 0, "AMBER": 0, "ORANGE": 0, "RED": 0}
    source_counts = {"IOT": 0, "AI": 0}

    for alert in alerts:
        severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        source_counts[alert.source] = source_counts.get(alert.source, 0) + 1

    return {
        "jurisdiction": {
            "state": officer.state,
            "region": "ALL" if officer.role == "CENTRAL_ADMIN" else officer.region,
        },
        "establishments": len(restaurants),
        "alerts": {
            "total": len(alerts),
            "severity": severity_counts,
            "source": source_counts,
        },
        "investigations": {
            "total": len(investigations),
            "open": sum(1 for i in investigations if i.status != "CLOSED"),
            "closed": sum(1 for i in investigations if i.status == "CLOSED"),
        },
    }


@router.get("/audit/verify")
def verify_global_audit(
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    verified, message = verify_audit_chain(db)
    total = db.query(BlockchainRecord).count()
    return {
        "verified": verified,
        "message": message,
        "total_records": total,
    }


@router.get("/investigations/{investigation_id}/audit")
def investigation_audit(
    investigation_id: int,
    officer: GovernmentOfficer = Depends(current_officer),
    db: Session = Depends(get_db),
):
    investigation = db.query(Investigation).filter(
        Investigation.id == investigation_id
    ).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    enforce_region(officer, investigation.alert.restaurant)

    records = db.query(BlockchainRecord).filter(
        BlockchainRecord.entity_type == "INVESTIGATION",
        BlockchainRecord.entity_id == investigation_id,
    ).order_by(BlockchainRecord.timestamp.asc()).all()

    verified, message = verify_audit_chain(db)

    return {
        "investigation_id": investigation.id,
        "chain_verified": verified,
        "chain_message": message,
        "records": [
            {
                "id": r.id,
                "record_type": r.record_type,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "actor_id": r.actor_id,
                "payload_hash": r.payload_hash,
                "previous_hash": r.previous_hash,
                "record_hash": r.record_hash,
                "timestamp": r.timestamp,
                "blockchain_tx_id": r.blockchain_tx_id,
                "verification_status": r.verification_status,
            }
            for r in records
        ],
    }
