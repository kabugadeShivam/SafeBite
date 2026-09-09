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
from ..schemas import (
    InvestigationUpdate,
    InvestigationVerify,
    LoginRequest,
    OfficerCreate,
)
from ..security import (
    create_access_token,
    get_token_payload,
    hash_password,
    verify_password,
)
from ..services.blockchain_service import (
    blockchain_status,
    create_audit_record,
    verify_audit_chain,
    verify_blockchain_record,
)

router = APIRouter(
    prefix="/government",
    tags=["Government"],
)

UPLOAD_DIR = (
    Path(__file__).resolve().parents[1]
    / "uploads"
    / "evidence"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
        )

    officer = (
        db.query(GovernmentOfficer)
        .filter(
            GovernmentOfficer.id == officer_id
        )
        .first()
    )

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Officer account not found",
        )

    if officer.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=401,
            detail="Officer account is inactive",
        )

    return officer


def enforce_region(
    officer: GovernmentOfficer,
    restaurant: Restaurant,
):
    if officer.role.upper() == "CENTRAL_ADMIN":
        return

    if (
        officer.state.strip().lower()
        != restaurant.state.strip().lower()
        or officer.region.strip().lower()
        != restaurant.region.strip().lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized for this region",
        )


# ============================================================
# SERIALIZATION
# ============================================================

def serialize_alert(
    alert: Alert,
):
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
            "registration_id":
                alert.restaurant.registration_id,
            "location": alert.restaurant.location,
            "state": alert.restaurant.state,
            "region": alert.restaurant.region,
        },
        "device": (
            {
                "id": alert.device.id,
                "device_id":
                    alert.device.device_id,
                "device_type":
                    alert.device.device_type,
                "status":
                    alert.device.status,
                "last_seen_at":
                    alert.device.last_seen_at,
            }
            if alert.device
            else None
        ),
    }


def serialize_audit_record(
    record: BlockchainRecord,
):
    blockchain_verification = None

    if record.blockchain_tx_id:
        blockchain_verification = verify_blockchain_record(
            record
        )

    return {
        "id": record.id,
        "record_type":
            record.record_type,
        "entity_type":
            record.entity_type,
        "entity_id":
            record.entity_id,
        "actor_id":
            record.actor_id,
        "payload_hash":
            record.payload_hash,
        "previous_hash":
            record.previous_hash,
        "record_hash":
            record.record_hash,
        "timestamp":
            record.timestamp,
        "blockchain_tx_id":
            record.blockchain_tx_id,
        "verification_status":
            record.verification_status,
        "blockchain_verification":
            blockchain_verification,
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def government_login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    officer = (
        db.query(GovernmentOfficer)
        .filter(
            GovernmentOfficer.username
            == payload.username
        )
        .first()
    )

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        payload.password,
        officer.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if officer.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Officer account is inactive",
        )

    token = create_access_token(
        officer.id,
        officer.role,
        officer.region,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "officer": {
            "id": officer.id,
            "officer_id":
                officer.officer_id,
            "name": officer.name,
            "role": officer.role,
            "state": officer.state,
            "region": officer.region,
        },
    }


# ============================================================
# CURRENT OFFICER
# ============================================================

@router.get("/me")
def government_me(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
):
    return {
        "officer_id":
            officer.officer_id,
        "name":
            officer.name,
        "role":
            officer.role,
        "state":
            officer.state,
        "region":
            officer.region,
    }


# ============================================================
# CREATE GOVERNMENT OFFICER
# ============================================================

@router.post("/officers")
def create_officer(
    payload: OfficerCreate,
    current: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    if current.role.upper() != "CENTRAL_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only Central Admin can create officers",
        )

    existing = (
        db.query(GovernmentOfficer)
        .filter(
            GovernmentOfficer.username
            == payload.username
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    officer = GovernmentOfficer(
        officer_id=payload.officer_id,
        name=payload.name,
        username=payload.username,
        password_hash=hash_password(
            payload.password
        ),
        role=payload.role,
        state=payload.state.strip(),
        region=payload.region.strip(),
        status="ACTIVE",
    )

    db.add(officer)
    db.commit()
    db.refresh(officer)

    return {
        "message": "Officer created",
        "officer_id":
            officer.officer_id,
    }


# ============================================================
# BLOCKCHAIN STATUS
# ============================================================

@router.get("/blockchain/status")
def government_blockchain_status(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
):
    return blockchain_status()


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
def government_dashboard(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state
            == officer.state,
            Restaurant.region
            == officer.region,
        )

    restaurants = query.all()

    restaurant_ids = [
        restaurant.id
        for restaurant in restaurants
    ]

    alerts = []

    if restaurant_ids:
        alerts = (
            db.query(Alert)
            .filter(
                Alert.restaurant_id.in_(
                    restaurant_ids
                )
            )
            .all()
        )

    active_statuses = {
        "OPEN",
        "UNDER_INVESTIGATION",
        "ACTION_REQUIRED",
    }

    critical = sum(
        1
        for alert in alerts
        if alert.severity == "RED"
        and alert.status in active_statuses
    )

    high = sum(
        1
        for alert in alerts
        if alert.severity == "ORANGE"
        and alert.status in active_statuses
    )

    investigations = []

    if restaurant_ids:
        investigations = (
            db.query(Investigation)
            .join(Alert)
            .filter(
                Alert.restaurant_id.in_(
                    restaurant_ids
                )
            )
            .all()
        )

    pending_investigations = sum(
        1
        for investigation in investigations
        if investigation.status
        not in {
            "CLOSED",
        }
    )

    devices = []

    if restaurant_ids:
        devices = (
            db.query(Device)
            .filter(
                Device.restaurant_id.in_(
                    restaurant_ids
                )
            )
            .all()
        )

    online_devices = sum(
        1
        for device in devices
        if device.status.upper()
        == "ONLINE"
    )

    latest_alerts = sorted(
        alerts,
        key=lambda item: item.timestamp,
        reverse=True,
    )[:10]

    return {
        "region": {
            "state":
                officer.state,
            "region": (
                "ALL"
                if officer.role.upper()
                == "CENTRAL_ADMIN"
                else officer.region
            ),
        },
        "counts": {
            "establishments":
                len(restaurants),
            "devices":
                len(devices),
            "online_devices":
                online_devices,
            "critical_alerts":
                critical,
            "high_risk_alerts":
                high,
            "pending_investigations":
                pending_investigations,
        },
        "latest_alerts": [
            serialize_alert(alert)
            for alert in latest_alerts
        ],
        "blockchain":
            blockchain_status(),
    }


# ============================================================
# ALERT LIST
# ============================================================

@router.get("/alerts")
def government_alerts(
    status_filter: str | None = None,
    severity: str | None = None,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Alert)
        .join(Restaurant)
    )

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state
            == officer.state,
            Restaurant.region
            == officer.region,
        )

    if status_filter:
        query = query.filter(
            Alert.status
            == status_filter.upper()
        )

    if severity:
        query = query.filter(
            Alert.severity
            == severity.upper()
        )

    alerts = (
        query
        .order_by(
            Alert.timestamp.desc()
        )
        .all()
    )

    return {
        "total":
            len(alerts),
        "alerts": [
            serialize_alert(alert)
            for alert in alerts
        ],
    }


# ============================================================
# ALERT DETAILS
# ============================================================

@router.get("/alerts/{alert_id}")
def government_alert_details(
    alert_id: int,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id
        )
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    enforce_region(
        officer,
        alert.restaurant,
    )

    readings = []

    if alert.device_id:
        readings = (
            db.query(SensorReading)
            .filter(
                SensorReading.device_id
                == alert.device_id
            )
            .order_by(
                SensorReading.timestamp.desc()
            )
            .limit(25)
            .all()
        )

    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id
            == alert.id
        )
        .first()
    )

    return {
        "alert":
            serialize_alert(alert),
        "sensor_evidence": [
            {
                "temperature":
                    reading.temperature,
                "humidity":
                    reading.humidity,
                "door_open":
                    reading.door_open,
                "timestamp":
                    reading.timestamp,
            }
            for reading in readings
        ],
        "investigation": (
            {
                "id":
                    investigation.id,
                "status":
                    investigation.status,
                "findings":
                    investigation.findings,
                "action_taken":
                    investigation.action_taken,
                "corrective_action":
                    investigation.corrective_action,
                "started_at":
                    investigation.started_at,
                "submitted_at":
                    investigation.submitted_at,
                "verified_at":
                    investigation.verified_at,
                "officer":
                    investigation.officer.name,
                "evidence": [
                    {
                        "id":
                            evidence.id,
                        "filename":
                            evidence.original_filename,
                        "sha256":
                            evidence.sha256,
                        "uploaded_at":
                            evidence.uploaded_at,
                    }
                    for evidence
                    in investigation.evidence
                ],
            }
            if investigation
            else None
        ),
    }


# ============================================================
# START INVESTIGATION
# ============================================================

@router.post(
    "/alerts/{alert_id}/investigate"
)
def start_investigation(
    alert_id: int,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id
        )
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    enforce_region(
        officer,
        alert.restaurant,
    )

    existing = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id
            == alert.id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Investigation already exists",
        )

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

    audit = create_audit_record(
        db=db,
        record_type="INVESTIGATION_STARTED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "alert_id":
                alert.id,
            "restaurant_id":
                alert.restaurant_id,
            "officer_id":
                officer.id,
        },
    )

    db.commit()
    db.refresh(investigation)
    db.refresh(audit)

    return {
        "message":
            "Investigation started",
        "investigation_id":
            investigation.id,
        "status":
            investigation.status,
        "audit": serialize_audit_record(
            audit
        ),
    }


# ============================================================
# UPDATE INVESTIGATION
# ============================================================

@router.put(
    "/investigations/{investigation_id}"
)
def update_investigation(
    investigation_id: int,
    payload: InvestigationUpdate,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    enforce_region(
        officer,
        investigation.alert.restaurant,
    )

    if (
        investigation.officer_id
        != officer.id
        and officer.role.upper()
        not in {
            "SUPERVISOR",
            "CENTRAL_ADMIN",
        }
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not the assigned "
                "officer for this case"
            ),
        )

    allowed_statuses = {
        "IN_PROGRESS",
        "ACTION_REQUIRED",
        "PENDING_VERIFICATION",
    }

    requested_status = (
        payload.status.upper()
    )

    if requested_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be one of "
                f"{sorted(allowed_statuses)}"
            ),
        )

    investigation.findings = (
        payload.findings
    )

    investigation.action_taken = (
        payload.action_taken
    )

    investigation.corrective_action = (
        payload.corrective_action
    )

    investigation.status = requested_status
    investigation.submitted_at = (
        datetime.utcnow()
    )

    if requested_status == "ACTION_REQUIRED":
        investigation.alert.status = (
            "ACTION_REQUIRED"
        )
    else:
        investigation.alert.status = (
            "UNDER_INVESTIGATION"
        )

    audit = create_audit_record(
        db=db,
        record_type="FINDINGS_SUBMITTED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "findings":
                investigation.findings,
            "action_taken":
                investigation.action_taken,
            "corrective_action":
                investigation.corrective_action,
            "status":
                investigation.status,
        },
    )

    db.commit()
    db.refresh(audit)

    return {
        "message":
            "Investigation updated",
        "status":
            investigation.status,
        "audit": serialize_audit_record(
            audit
        ),
    }


# ============================================================
# EVIDENCE UPLOAD
# ============================================================

@router.post(
    "/investigations/{investigation_id}/evidence"
)
def upload_evidence(
    investigation_id: int,
    file: UploadFile = File(...),
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    enforce_region(
        officer,
        investigation.alert.restaurant,
    )

    if (
        investigation.officer_id
        != officer.id
        and officer.role.upper()
        not in {
            "SUPERVISOR",
            "CENTRAL_ADMIN",
        }
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not assigned "
                "to this investigation"
            ),
        )

    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    digest = hashlib.sha256(
        content
    ).hexdigest()

    original_name = (
        file.filename
        or "evidence"
    )

    safe_name = (
        f"{uuid.uuid4().hex}_"
        f"{Path(original_name).name}"
    )

    stored_path = (
        UPLOAD_DIR
        / safe_name
    )

    stored_path.write_bytes(
        content
    )

    evidence = Evidence(
        investigation_id=
            investigation.id,
        original_filename=
            original_name,
        stored_path=
            str(stored_path),
        content_type=
            file.content_type,
        sha256=
            digest,
        uploaded_by=
            officer.id,
    )

    db.add(evidence)
    db.flush()

    audit = create_audit_record(
        db=db,
        record_type="EVIDENCE_UPLOADED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "evidence_id":
                evidence.id,
            "filename":
                evidence.original_filename,
            "sha256":
                evidence.sha256,
        },
    )

    db.commit()
    db.refresh(evidence)
    db.refresh(audit)

    return {
        "message":
            "Evidence uploaded",
        "evidence_id":
            evidence.id,
        "sha256":
            evidence.sha256,
        "audit":
            serialize_audit_record(audit),
    }


# ============================================================
# VERIFY INVESTIGATION
# ============================================================

@router.post(
    "/investigations/{investigation_id}/verify"
)
def verify_investigation(
    investigation_id: int,
    payload: InvestigationVerify,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    if officer.role.upper() not in {
        "SUPERVISOR",
        "CENTRAL_ADMIN",
    }:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only Supervisor or "
                "Central Admin can verify "
                "investigations"
            ),
        )

    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    enforce_region(
        officer,
        investigation.alert.restaurant,
    )

    decision = (
        payload.decision.upper()
    )

    if decision != "APPROVE":
        investigation.status = (
            "ACTION_REQUIRED"
        )

        investigation.alert.status = (
            "ACTION_REQUIRED"
        )

        audit = create_audit_record(
            db=db,
            record_type="INVESTIGATION_RETURNED",
            entity_type="INVESTIGATION",
            entity_id=investigation.id,
            actor_id=officer.id,
            payload={
                "remarks":
                    payload.remarks,
                "decision":
                    decision,
            },
        )

        db.commit()
        db.refresh(audit)

        return {
            "message":
                "Investigation returned "
                "for correction",
            "status":
                investigation.status,
            "audit":
                serialize_audit_record(audit),
        }

    investigation.status = "CLOSED"

    investigation.verified_at = (
        datetime.utcnow()
    )

    investigation.verified_by = (
        officer.id
    )

    investigation.alert.status = (
        "CLOSED"
    )

    audit = create_audit_record(
        db=db,
        record_type="INVESTIGATION_VERIFIED",
        entity_type="INVESTIGATION",
        entity_id=investigation.id,
        actor_id=officer.id,
        payload={
            "findings":
                investigation.findings,
            "action_taken":
                investigation.action_taken,
            "corrective_action":
                investigation.corrective_action,
            "remarks":
                payload.remarks,
            "decision":
                decision,
        },
    )

    db.commit()
    db.refresh(audit)

    return {
        "message":
            "Investigation verified "
            "and case closed",
        "status":
            investigation.status,
        "audit_record_id":
            audit.id,
        "record_hash":
            audit.record_hash,
        "blockchain_tx_id":
            audit.blockchain_tx_id,
        "verification_status":
            audit.verification_status,
        "blockchain_verification":
            (
                verify_blockchain_record(audit)
                if audit.blockchain_tx_id
                else {
                    "verified": False,
                    "message":
                        "Blockchain transaction "
                        "not available",
                }
            ),
    }


# ============================================================
# LIST INVESTIGATIONS
# ============================================================

@router.get("/investigations")
def list_investigations(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Investigation)
        .join(Alert)
        .join(Restaurant)
    )

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state
            == officer.state,
            Restaurant.region
            == officer.region,
        )

    investigations = (
        query
        .order_by(
            Investigation.started_at.desc()
        )
        .all()
    )

    return {
        "total":
            len(investigations),
        "investigations": [
            {
                "id":
                    investigation.id,
                "status":
                    investigation.status,
                "started_at":
                    investigation.started_at,
                "submitted_at":
                    investigation.submitted_at,
                "verified_at":
                    investigation.verified_at,
                "officer":
                    investigation.officer.name,
                "alert": {
                    "id":
                        investigation.alert.id,
                    "severity":
                        investigation.alert.severity,
                    "risk_score":
                        investigation.alert.risk_score,
                    "reason":
                        investigation.alert.reason,
                    "status":
                        investigation.alert.status,
                },
                "restaurant": {
                    "id":
                        investigation.alert.restaurant.id,
                    "name":
                        investigation.alert.restaurant.name,
                    "region":
                        investigation.alert.restaurant.region,
                },
            }
            for investigation
            in investigations
        ],
    }


# ============================================================
# INVESTIGATION DETAILS
# ============================================================

@router.get(
    "/investigations/{investigation_id}"
)
def get_investigation(
    investigation_id: int,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    enforce_region(
        officer,
        investigation.alert.restaurant,
    )

    return {
        "id":
            investigation.id,
        "status":
            investigation.status,
        "started_at":
            investigation.started_at,
        "submitted_at":
            investigation.submitted_at,
        "verified_at":
            investigation.verified_at,
        "officer":
            investigation.officer.name,
        "findings":
            investigation.findings,
        "action_taken":
            investigation.action_taken,
        "corrective_action":
            investigation.corrective_action,
        "alert":
            serialize_alert(
                investigation.alert
            ),
        "evidence": [
            {
                "id":
                    evidence.id,
                "filename":
                    evidence.original_filename,
                "sha256":
                    evidence.sha256,
                "uploaded_at":
                    evidence.uploaded_at,
            }
            for evidence
            in investigation.evidence
        ],
    }


# ============================================================
# INVESTIGATION AUDIT
# ============================================================

@router.get(
    "/investigations/{investigation_id}/audit"
)
def get_investigation_audit(
    investigation_id: int,
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id
            == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    enforce_region(
        officer,
        investigation.alert.restaurant,
    )

    records = (
        db.query(BlockchainRecord)
        .filter(
            BlockchainRecord.entity_type
            == "INVESTIGATION",
            BlockchainRecord.entity_id
            == investigation.id,
        )
        .order_by(
            BlockchainRecord.timestamp.asc()
        )
        .all()
    )

    local_chain_valid, chain_message = (
        verify_audit_chain(db)
    )

    blockchain_records = []

    for record in records:

        blockchain_result = None

        if record.blockchain_tx_id:
            blockchain_result = (
                verify_blockchain_record(
                    record
                )
            )

        blockchain_records.append(
            {
                "id":
                    record.id,
                "record_type":
                    record.record_type,
                "timestamp":
                    record.timestamp,
                "payload_hash":
                    record.payload_hash,
                "previous_hash":
                    record.previous_hash,
                "record_hash":
                    record.record_hash,
                "blockchain_tx_id":
                    record.blockchain_tx_id,
                "verification_status":
                    record.verification_status,
                "blockchain_verification":
                    blockchain_result,
            }
        )

    return {
        "investigation_id":
            investigation.id,
        "chain_verified":
            local_chain_valid,
        "chain_message":
            chain_message,
        "blockchain":
            blockchain_status(),
        "records":
            blockchain_records,
    }


# ============================================================
# ESTABLISHMENTS
# ============================================================

@router.get("/establishments")
def establishments(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state
            == officer.state,
            Restaurant.region
            == officer.region,
        )

    restaurants = (
        query
        .order_by(
            Restaurant.name.asc()
        )
        .all()
    )

    result = []

    for restaurant in restaurants:

        alerts = (
            db.query(Alert)
            .filter(
                Alert.restaurant_id
                == restaurant.id
            )
            .all()
        )

        active = [
            alert
            for alert in alerts
            if alert.status != "CLOSED"
        ]

        result.append(
            {
                "id":
                    restaurant.id,
                "name":
                    restaurant.name,
                "registration_id":
                    restaurant.registration_id,
                "location":
                    restaurant.location,
                "state":
                    restaurant.state,
                "region":
                    restaurant.region,
                "status":
                    restaurant.status,
                "active_alerts":
                    len(active),
                "critical_alerts":
                    sum(
                        1
                        for alert in active
                        if alert.severity == "RED"
                    ),
                "devices":
                    len(restaurant.devices),
            }
        )

    return {
        "total":
            len(result),
        "establishments":
            result,
    }


# ============================================================
# DEVICES
# ============================================================

@router.get("/devices")
def government_devices(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Device)
        .join(Restaurant)
    )

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state
            == officer.state,
            Restaurant.region
            == officer.region,
        )

    devices = (
        query
        .order_by(
            Device.last_seen_at.desc()
        )
        .all()
    )

    return {
        "total":
            len(devices),
        "devices": [
            {
                "id":
                    device.id,
                "device_id":
                    device.device_id,
                "device_type":
                    device.device_type,
                "status":
                    device.status,
                "last_seen_at":
                    device.last_seen_at,
                "restaurant":
                    device.restaurant.name,
            }
            for device in devices
        ],
    }