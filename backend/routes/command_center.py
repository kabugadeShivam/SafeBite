
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AIDetection,
    Alert,
    BlockchainRecord,
    GovernmentOfficer,
    Investigation,
    Restaurant,
)
from ..models_citizen import CitizenReport
from ..security import get_token_payload


router = APIRouter(
    prefix="/government/command-center",
    tags=["Command Center"],
)


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_officer(
    payload=Depends(get_token_payload),
    db: Session = Depends(get_db),
):
    try:
        officer_id = int(
            payload["sub"]
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
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
            detail="Officer not found",
        )

    if officer.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=401,
            detail="Officer account is inactive",
        )

    return officer


# ============================================================
# HELPERS
# ============================================================

def _region_restaurants(
    db: Session,
    officer: GovernmentOfficer,
):
    query = db.query(Restaurant)

    if officer.role.upper() != "CENTRAL_ADMIN":

        query = query.filter(
            Restaurant.state == officer.state,
            Restaurant.region == officer.region,
        )

    return query.all()


def _priority(
    red: int,
    orange: int,
    investigations: int,
    citizen: int,
) -> str:

    score = (
        red * 10
        + orange * 4
        + investigations * 8
        + citizen * 3
    )

    if score >= 80:
        return "CRITICAL"

    if score >= 45:
        return "HIGH"

    if score >= 20:
        return "MEDIUM"

    return "LOW"


# ============================================================
# COMMAND CENTER
# ============================================================

@router.get("")
def command_center(
    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),
    db: Session = Depends(get_db),
):

    restaurants = _region_restaurants(
        db,
        officer,
    )

    restaurant_ids = [
        restaurant.id
        for restaurant in restaurants
    ]

    now = datetime.utcnow()

    last_30_days = (
        now - timedelta(days=30)
    )

    last_24_hours = (
        now - timedelta(hours=24)
    )

    # ========================================================
    # NO ACCESSIBLE OUTLETS
    # ========================================================

    if not restaurant_ids:

        return {
            "region": {
                "state":
                    officer.state,

                "region":
                    officer.region,

                "role":
                    officer.role,
            },

            "generated_at":
                now.isoformat(),

            "summary": {
                "outlets": 0,
                "active_red_alerts": 0,
                "active_orange_alerts": 0,
                "unresolved_investigations": 0,
                "citizen_reports_30d": 0,
                "verified_citizen_reports_30d": 0,
                "ai_hygiene_findings_30d": 0,
                "blockchain_anchored_audits": 0,
            },

            "priority":
                "LOW",

            "message":
                "No registered outlets are currently assigned to your jurisdiction.",
        }

    # ========================================================
    # ALERTS
    # ========================================================

    alerts = (
        db.query(Alert)
        .filter(
            Alert.restaurant_id.in_(
                restaurant_ids
            )
        )
        .all()
    )

    active_red_alerts = sum(
        1
        for alert in alerts
        if str(
            alert.severity
        ).upper() == "RED"
        and str(
            alert.status
        ).upper()
        not in {
            "CLOSED",
            "RESOLVED",
        }
    )

    active_orange_alerts = sum(
        1
        for alert in alerts
        if str(
            alert.severity
        ).upper() == "ORANGE"
        and str(
            alert.status
        ).upper()
        not in {
            "CLOSED",
            "RESOLVED",
        }
    )

    last_24_alerts = [
        alert
        for alert in alerts
        if alert.timestamp
        and alert.timestamp >= last_24_hours
    ]

    # ========================================================
    # INVESTIGATIONS
    # ========================================================

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

    unresolved_investigations = sum(
        1
        for investigation
        in investigations
        if str(
            investigation.status
        ).upper()
        not in {
            "CLOSED",
            "VERIFIED",
        }
    )

    investigations_started_30d = sum(
        1
        for investigation
        in investigations
        if investigation.started_at
        and investigation.started_at >= last_30_days
    )

    # ========================================================
    # CITIZEN REPORTS
    # ========================================================

    citizen_reports = (
        db.query(CitizenReport)
        .filter(
            CitizenReport.restaurant_id.in_(
                restaurant_ids
            ),
            CitizenReport.submitted_at
            >= last_30_days,
        )
        .all()
    )

    verified_citizen_reports = [
        report
        for report in citizen_reports
        if str(
            report.status
        ).upper() == "VERIFIED"
    ]

    investigation_citizen_reports = [
        report
        for report in citizen_reports
        if str(
            report.status
        ).upper()
        == "NEEDS_INVESTIGATION"
    ]

    critical_citizen_reports = [
        report
        for report in citizen_reports
        if str(
            report.ai_severity
        ).upper() == "CRITICAL"
    ]

    # ========================================================
    # AI DETECTIONS
    # ========================================================

    ai_detections = (
        db.query(AIDetection)
        .filter(
            AIDetection.restaurant_id.in_(
                restaurant_ids
            ),
            AIDetection.timestamp
            >= last_30_days,
        )
        .all()
    )

    hygiene_labels = {
        "no_apron",
        "no_gloves",
        "no_hairnet",
    }

    critical_labels = {
        "cockroach",
        "rat",
        "lizard",
    }

    hygiene_findings = [
        detection
        for detection
        in ai_detections
        if str(
            detection.detection_type
        ).lower()
        in (
            hygiene_labels
            | critical_labels
        )
    ]

    critical_ai_findings = [
        detection
        for detection
        in hygiene_findings
        if str(
            detection.detection_type
        ).lower()
        in critical_labels
    ]

    # ========================================================
    # BLOCKCHAIN
    # ========================================================

    blockchain_records = (
        db.query(BlockchainRecord)
        .filter(
            BlockchainRecord.timestamp
            >= last_30_days,
            BlockchainRecord.entity_id.in_(
                restaurant_ids
            ),
        )
        .all()
    )

    # The audit records are generally entity-linked to
    # investigations/reports rather than directly to outlets.
    # Therefore use the overall anchored count as a
    # system-integrity indicator for the jurisdiction.

    anchored_audits = sum(
        1
        for record
        in db.query(BlockchainRecord)
        .filter(
            BlockchainRecord.timestamp
            >= last_30_days
        )
        .all()
        if str(
            record.verification_status
        ).upper()
        == "BLOCKCHAIN_ANCHORED"
    )

    local_chain_audits = sum(
        1
        for record
        in db.query(BlockchainRecord)
        .filter(
            BlockchainRecord.timestamp
            >= last_30_days
        )
        .all()
        if str(
            record.verification_status
        ).upper()
        == "LOCAL_HASH_CHAIN"
    )

    # ========================================================
    # OUTLET RISK DISTRIBUTION
    # ========================================================

    outlet_risk = []

    for restaurant in restaurants:

        restaurant_alerts = [
            alert
            for alert
            in alerts
            if alert.restaurant_id
            == restaurant.id
        ]

        restaurant_investigations = [
            investigation
            for investigation
            in investigations
            if investigation.alert
            and investigation.alert.restaurant_id
            == restaurant.id
        ]

        restaurant_citizen = [
            report
            for report
            in citizen_reports
            if report.restaurant_id
            == restaurant.id
        ]

        restaurant_red = sum(
            1
            for alert
            in restaurant_alerts
            if str(
                alert.severity
            ).upper() == "RED"
            and str(
                alert.status
            ).upper()
            not in {
                "CLOSED",
                "RESOLVED",
            }
        )

        restaurant_orange = sum(
            1
            for alert
            in restaurant_alerts
            if str(
                alert.severity
            ).upper() == "ORANGE"
            and str(
                alert.status
            ).upper()
            not in {
                "CLOSED",
                "RESOLVED",
            }
        )

        restaurant_unresolved = sum(
            1
            for investigation
            in restaurant_investigations
            if str(
                investigation.status
            ).upper()
            not in {
                "CLOSED",
                "VERIFIED",
            }
        )

        restaurant_verified_citizen = sum(
            1
            for report
            in restaurant_citizen
            if str(
                report.status
            ).upper() == "VERIFIED"
        )

        risk_score = (
            restaurant_red * 10
            + restaurant_orange * 4
            + restaurant_unresolved * 8
            + restaurant_verified_citizen * 5
        )

        outlet_risk.append(
            {
                "id":
                    restaurant.id,

                "name":
                    restaurant.name,

                "registration_id":
                    restaurant.registration_id,

                "risk_score":
                    risk_score,

                "red_alerts":
                    restaurant_red,

                "orange_alerts":
                    restaurant_orange,

                "unresolved_investigations":
                    restaurant_unresolved,

                "verified_citizen_reports":
                    restaurant_verified_citizen,
            }
        )

    outlet_risk.sort(
        key=lambda item:
            item["risk_score"],
        reverse=True,
    )

    # ========================================================
    # COMMAND PRIORITY
    # ========================================================

    command_priority = _priority(
        red=active_red_alerts,
        orange=active_orange_alerts,
        investigations=unresolved_investigations,
        citizen=len(
            verified_citizen_reports
        ),
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "region": {
            "state":
                officer.state,

            "region":
                officer.region,

            "role":
                officer.role,
        },

        "generated_at":
            now.isoformat(),

        "summary": {
            "outlets":
                len(restaurants),

            "active_red_alerts":
                active_red_alerts,

            "active_orange_alerts":
                active_orange_alerts,

            "unresolved_investigations":
                unresolved_investigations,

            "investigations_started_30d":
                investigations_started_30d,

            "citizen_reports_30d":
                len(citizen_reports),

            "verified_citizen_reports_30d":
                len(
                    verified_citizen_reports
                ),

            "citizen_reports_needing_investigation":
                len(
                    investigation_citizen_reports
                ),

            "critical_citizen_reports":
                len(
                    critical_citizen_reports
                ),

            "ai_hygiene_findings_30d":
                len(
                    hygiene_findings
                ),

            "critical_ai_findings_30d":
                len(
                    critical_ai_findings
                ),

            "alerts_last_24h":
                len(
                    last_24_alerts
                ),

            "blockchain_anchored_audits_30d":
                anchored_audits,

            "local_hash_audits_30d":
                local_chain_audits,
        },

        "priority":
            command_priority,

        "risk_distribution": {
            "critical":
                sum(
                    1
                    for item
                    in outlet_risk
                    if item["risk_score"]
                    >= 80
                ),

            "high":
                sum(
                    1
                    for item
                    in outlet_risk
                    if 45
                    <= item["risk_score"]
                    < 80
                ),

            "medium":
                sum(
                    1
                    for item
                    in outlet_risk
                    if 20
                    <= item["risk_score"]
                    < 45
                ),

            "low":
                sum(
                    1
                    for item
                    in outlet_risk
                    if item["risk_score"]
                    < 20
                ),
        },

        "top_risk_outlets":
            outlet_risk[:5],

        "data_sources": {
            "iot_alerts":
                True,

            "investigations":
                True,

            "hygiene_ai":
                len(
                    ai_detections
                ) > 0,

            "citizen_reports":
                len(
                    citizen_reports
                ) > 0,

            "blockchain":
                True,
        },

        "system_message": (
            "SafeBite Command Center combines "
            "government alerts, investigations, "
            "AI hygiene findings, citizen evidence, "
            "and audit-integrity indicators."
        ),
    }