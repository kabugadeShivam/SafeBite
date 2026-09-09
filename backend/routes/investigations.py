from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Investigation
from ..services.blockchain_service import create_audit_record


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


# ============================================================
# LIST INVESTIGATIONS
# ============================================================

@router.get("/")
def list_investigations(
    db: Session = Depends(get_db),
):
    investigations = (
        db.query(Investigation)
        .order_by(
            Investigation.investigation_date.desc()
        )
        .all()
    )

    return {
        "count": len(investigations),
        "investigations": [
            {
                "id": item.id,
                "officer_name": item.officer_name,
                "findings": item.findings,
                "action_taken": item.action_taken,
                "status": item.status,
                "investigation_date": item.investigation_date,
                "alert_id": item.alert_id,
            }
            for item in investigations
        ],
    }


# ============================================================
# GET SINGLE INVESTIGATION
# ============================================================

@router.get("/{investigation_id}")
def get_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    alert = None

    if investigation.alert_id:
        alert = (
            db.query(Alert)
            .filter(
                Alert.id == investigation.alert_id
            )
            .first()
        )

    return {
        "id": investigation.id,
        "officer_name": investigation.officer_name,
        "findings": investigation.findings,
        "action_taken": investigation.action_taken,
        "status": investigation.status,
        "investigation_date":
            investigation.investigation_date,
        "alert_id": investigation.alert_id,
        "alert": (
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "risk_score": alert.risk_score,
                "reason": alert.reason,
                "status": alert.status,
                "timestamp": alert.timestamp,
                "restaurant_id": alert.restaurant_id,
            }
            if alert
            else None
        ),
    }


# ============================================================
# CREATE INVESTIGATION
# ============================================================

@router.post("/")
def create_investigation(
    alert_id: int,
    officer_name: str,
    db: Session = Depends(get_db),
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    existing = (
        db.query(Investigation)
        .filter(
            Investigation.alert_id == alert_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Investigation already exists for this alert",
        )

    investigation = Investigation(
        officer_name=officer_name,
        findings=None,
        action_taken=None,
        status="in_progress",
        investigation_date=datetime.utcnow(),
        alert_id=alert_id,
    )

    db.add(investigation)

    # Mark alert as under investigation.
    alert.status = "investigating"

    db.commit()
    db.refresh(investigation)

    return {
        "message": "Investigation started",
        "investigation": {
            "id": investigation.id,
            "officer_name": investigation.officer_name,
            "status": investigation.status,
            "investigation_date":
                investigation.investigation_date,
            "alert_id": investigation.alert_id,
        },
    }


# ============================================================
# UPDATE INVESTIGATION
# ============================================================

@router.put("/{investigation_id}")
def update_investigation(
    investigation_id: int,
    officer_name: str | None = None,
    findings: str | None = None,
    action_taken: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    if officer_name is not None:
        investigation.officer_name = officer_name

    if findings is not None:
        investigation.findings = findings

    if action_taken is not None:
        investigation.action_taken = action_taken

    if status is not None:
        allowed_statuses = {
            "pending",
            "in_progress",
            "completed",
            "verified",
            "closed",
            "rejected",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid status. Allowed values: "
                    + ", ".join(sorted(allowed_statuses))
                ),
            )

        investigation.status = status

    db.commit()
    db.refresh(investigation)

    return {
        "message": "Investigation updated",
        "investigation": {
            "id": investigation.id,
            "officer_name":
                investigation.officer_name,
            "findings":
                investigation.findings,
            "action_taken":
                investigation.action_taken,
            "status":
                investigation.status,
            "investigation_date":
                investigation.investigation_date,
            "alert_id":
                investigation.alert_id,
        },
    }


# ============================================================
# COMPLETE INVESTIGATION + BLOCKCHAIN AUDIT
# ============================================================

@router.post("/{investigation_id}/complete")
def complete_investigation(
    investigation_id: int,
    officer_name: str,
    findings: str,
    action_taken: str,
    db: Session = Depends(get_db),
):
    investigation = (
        db.query(Investigation)
        .filter(
            Investigation.id == investigation_id
        )
        .first()
    )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    investigation.officer_name = officer_name
    investigation.findings = findings
    investigation.action_taken = action_taken
    investigation.status = "completed"

    alert = None

    if investigation.alert_id:
        alert = (
            db.query(Alert)
            .filter(
                Alert.id == investigation.alert_id
            )
            .first()
        )

    # --------------------------------------------------------
    # Save investigation first.
    # --------------------------------------------------------

    db.commit()
    db.refresh(investigation)

    # --------------------------------------------------------
    # Create tamper-evident audit record.
    # --------------------------------------------------------

    payload = {
        "investigation_id": investigation.id,
        "alert_id": investigation.alert_id,
        "officer_name": investigation.officer_name,
        "findings": investigation.findings,
        "action_taken": investigation.action_taken,
        "status": investigation.status,
        "investigation_date":
            investigation.investigation_date,
    }

    audit_record = create_audit_record(
        db=db,
        record_type="INVESTIGATION_COMPLETED",
        entity_type="investigation",
        entity_id=investigation.id,
        actor_id=None,
        payload=payload,
    )

    # --------------------------------------------------------
    # Close the alert after investigation completion.
    # --------------------------------------------------------

    if alert:
        alert.status = "closed"

    db.commit()
    db.refresh(audit_record)

    return {
        "message": "Investigation completed",
        "investigation": {
            "id": investigation.id,
            "officer_name":
                investigation.officer_name,
            "findings":
                investigation.findings,
            "action_taken":
                investigation.action_taken,
            "status":
                investigation.status,
            "alert_id":
                investigation.alert_id,
        },
        "audit": {
            "id": audit_record.id,
            "record_type":
                audit_record.record_type,
            "entity_type":
                audit_record.entity_type,
            "entity_id":
                audit_record.entity_id,
            "record_hash":
                audit_record.record_hash,
            "payload_hash":
                audit_record.payload_hash,
            "previous_hash":
                audit_record.previous_hash,
            "blockchain_tx_id":
                audit_record.blockchain_tx_id,
            "verification_status":
                audit_record.verification_status,
            "timestamp":
                audit_record.timestamp,
        },
    }


# ============================================================
# CLOSE INVESTIGATION
# ============================================================

@router.post("/{investigation_id}/close")
def close_investigation(
    investigation_id: int,
    officer_name: str,
    findings: str,
    action_taken: str,
    db: Session = Depends(get_db),
):
    return complete_investigation(
        investigation_id=investigation_id,
        officer_name=officer_name,
        findings=findings,
        action_taken=action_taken,
        db=db,
    )