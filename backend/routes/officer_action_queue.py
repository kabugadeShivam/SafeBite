from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, GovernmentOfficer, Restaurant
from ..models_citizen import CitizenReport
from ..routes.government import get_current_officer


router = APIRouter(
    prefix="/government/action-queue",
    tags=["Officer Action Queue"],
)


@router.get("")
def officer_action_queue(
    officer: GovernmentOfficer = Depends(get_current_officer),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).join(Restaurant)

    if officer.role.upper() != "CENTRAL_ADMIN":
        query = query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )

    active_alerts = (
        query
        .filter(
            Alert.status.in_([
                "OPEN",
                "UNDER_INVESTIGATION",
                "ACTION_REQUIRED",
            ])
        )
        .order_by(Alert.timestamp.desc())
        .all()
    )

    items = []

    for alert in active_alerts:
        alert_type = str(alert.alert_type or "").upper()
        severity = str(alert.severity or "").upper()

        if alert_type == "LICENCE_REVIEW_RECOMMENDED":
            action = "LICENCE_REVIEW"
            priority = "CRITICAL"
        elif severity == "RED":
            action = "PHYSICAL_INSPECTION"
            priority = "CRITICAL"
        elif severity == "ORANGE":
            action = "FOLLOW_UP"
            priority = "HIGH"
        else:
            action = "MONITOR"
            priority = "MEDIUM"

        items.append({
            "kind": "ALERT",
            "id": alert.id,
            "priority": priority,
            "action": action,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "status": alert.status,
            "reason": alert.reason,
            "source": alert.source,
            "timestamp": alert.timestamp,
            "outlet": {
                "id": alert.restaurant.id,
                "name": alert.restaurant.name,
                "registration_id": alert.restaurant.registration_id,
                "state": alert.restaurant.state,
                "region": alert.restaurant.region,
            },
        })

    reports_query = db.query(CitizenReport).join(Restaurant)

    if officer.role.upper() != "CENTRAL_ADMIN":
        reports_query = reports_query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )

    reports = (
        reports_query
        .filter(CitizenReport.status == "NEEDS_INVESTIGATION")
        .order_by(CitizenReport.submitted_at.desc())
        .limit(20)
        .all()
    )

    for report in reports:
        report_severity = str(report.ai_severity or "").upper()
        items.append({
            "kind": "CITIZEN_REPORT",
            "id": report.id,
            "priority": "HIGH" if report_severity in {"CRITICAL", "HIGH"} else "MEDIUM",
            "action": "PHYSICAL_INSPECTION",
            "alert_type": "CITIZEN_REPORT",
            "severity": report.ai_severity,
            "risk_score": report.ai_relevance,
            "status": report.status,
            "reason": report.description,
            "source": "CITIZEN",
            "timestamp": report.submitted_at,
            "outlet": {
                "id": report.restaurant.id,
                "name": report.restaurant.name,
                "registration_id": report.restaurant.registration_id,
                "state": report.restaurant.state,
                "region": report.restaurant.region,
            },
        })

    priority_rank = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
    }

    # Stable two-pass sort: highest priority first, newest first within priority.
    items.sort(
        key=lambda item: item["timestamp"] or datetime.min,
        reverse=True,
    )
    items.sort(
        key=lambda item: priority_rank.get(
            str(item["priority"]).upper(),
            3,
        )
    )

    return {
        "generated_at": datetime.utcnow(),
        "total": len(items),
        "critical": sum(
            1
            for item in items
            if item["priority"] == "CRITICAL"
        ),
        "high": sum(
            1
            for item in items
            if item["priority"] == "HIGH"
        ),
        "requires_physical_action": sum(
            1
            for item in items
            if item["action"] in {
                "PHYSICAL_INSPECTION",
                "LICENCE_REVIEW",
            }
        ),
        "items": items[:30],
    }
