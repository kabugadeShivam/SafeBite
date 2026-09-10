from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..models import Alert, Device, Investigation, Restaurant


DEFAULT_DAYS = 30


# ============================================================
# STATUS HELPERS
# ============================================================

def _compliance_status(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "COMPLIANT"
    if score >= 65:
        return "WATCHLIST"
    if score >= 50:
        return "WARNING"
    return "CRITICAL"


def _priority_status(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _risk_trend(
    previous_pressure: int,
    recent_pressure: int,
) -> str:

    difference = recent_pressure - previous_pressure

    if difference >= 3:
        return "DETERIORATING"

    if difference <= -3:
        return "IMPROVING"

    return "STABLE"


# ============================================================
# ALERT PRESSURE
# ============================================================

def _alert_pressure(
    alerts: list[Any],
) -> int:

    pressure = 0

    for alert in alerts:

        severity = str(
            getattr(
                alert,
                "severity",
                "",
            )
        ).upper()

        status = str(
            getattr(
                alert,
                "status",
                "",
            )
        ).upper()

        multiplier = 0

        if severity == "RED":
            multiplier = 3

        elif severity == "ORANGE":
            multiplier = 1

        if status != "CLOSED":
            multiplier += 1

        pressure += multiplier

    return pressure


# ============================================================
# OUTLET AUDIT
# ============================================================

def _build_outlet_audit(
    db: Session,
    restaurant: Restaurant,
    cutoff: datetime,
    days: int,
) -> dict[str, Any]:

    alerts = (
        db.query(Alert)
        .filter(
            Alert.restaurant_id == restaurant.id,
            Alert.timestamp >= cutoff,
        )
        .all()
    )

    investigations = (
        db.query(Investigation)
        .join(Alert)
        .filter(
            Alert.restaurant_id == restaurant.id,
            Investigation.started_at >= cutoff,
        )
        .all()
    )

    devices = (
        db.query(Device)
        .filter(
            Device.restaurant_id == restaurant.id
        )
        .all()
    )

    # --------------------------------------------------------
    # Basic metrics
    # --------------------------------------------------------

    active_red = sum(
        1
        for alert in alerts
        if str(alert.severity).upper() == "RED"
        and str(alert.status).upper() != "CLOSED"
    )

    active_orange = sum(
        1
        for alert in alerts
        if str(alert.severity).upper() == "ORANGE"
        and str(alert.status).upper() != "CLOSED"
    )

    closed_alerts = sum(
        1
        for alert in alerts
        if str(alert.status).upper() == "CLOSED"
    )

    unresolved_investigations = sum(
        1
        for investigation in investigations
        if str(investigation.status).upper() != "CLOSED"
    )

    completed_investigations = sum(
        1
        for investigation in investigations
        if str(investigation.status).upper() == "CLOSED"
    )

    action_required = sum(
        1
        for investigation in investigations
        if str(investigation.status).upper()
        == "ACTION_REQUIRED"
    )

    online_devices = sum(
        1
        for device in devices
        if str(device.status).upper() == "ONLINE"
    )

    # --------------------------------------------------------
    # Trend window
    # --------------------------------------------------------

    midpoint = cutoff + timedelta(
        days=max(1, days // 2)
    )

    previous_alerts = [
        alert
        for alert in alerts
        if alert.timestamp < midpoint
    ]

    recent_alerts = [
        alert
        for alert in alerts
        if alert.timestamp >= midpoint
    ]

    previous_pressure = _alert_pressure(
        previous_alerts
    )

    recent_pressure = _alert_pressure(
        recent_alerts
    )

    trend = _risk_trend(
        previous_pressure,
        recent_pressure,
    )

    # ========================================================
    # COMPLIANCE SCORE
    #
    # Measures outlet compliance quality.
    # Repeated alerts are NOT counted one-for-one.
    # ========================================================

    compliance_score = 100.0

    compliance_breakdown = []

    # Active critical conditions
    red_penalty = min(
        active_red * 6,
        18,
    )

    compliance_score -= red_penalty

    compliance_breakdown.append(
        {
            "factor": "Active RED alerts",
            "penalty": red_penalty,
        }
    )

    # Active medium/high conditions
    orange_penalty = min(
        active_orange * 3,
        9,
    )

    compliance_score -= orange_penalty

    compliance_breakdown.append(
        {
            "factor": "Active ORANGE alerts",
            "penalty": orange_penalty,
        }
    )

    # Open investigations
    investigation_penalty = min(
        unresolved_investigations * 5,
        10,
    )

    compliance_score -= investigation_penalty

    compliance_breakdown.append(
        {
            "factor": "Unresolved investigations",
            "penalty": investigation_penalty,
        }
    )

    # Corrective action problems
    action_penalty = min(
        action_required * 4,
        8,
    )

    compliance_score -= action_penalty

    compliance_breakdown.append(
        {
            "factor": "Corrective actions required",
            "penalty": action_penalty,
        }
    )

    # IoT availability
    device_penalty = 0

    if devices:

        availability = (
            online_devices / len(devices)
        )

        if availability < 0.50:
            device_penalty = 10

        elif availability < 0.75:
            device_penalty = 7

        elif availability < 0.90:
            device_penalty = 4

    elif devices == []:
        availability = None

    compliance_score -= device_penalty

    compliance_breakdown.append(
        {
            "factor": "IoT availability",
            "penalty": device_penalty,
        }
    )

    # Investigation closure performance
    closure_penalty = 0

    if investigations:

        closure_rate = (
            completed_investigations
            / len(investigations)
        )

        if closure_rate < 0.50:
            closure_penalty = 6

        elif closure_rate < 0.80:
            closure_penalty = 3

    else:
        closure_rate = None

    compliance_score -= closure_penalty

    compliance_breakdown.append(
        {
            "factor": "Investigation closure performance",
            "penalty": closure_penalty,
        }
    )

    # Trend effect is intentionally small.
    trend_penalty = 0

    if trend == "DETERIORATING":
        trend_penalty = 5

    elif trend == "IMPROVING":
        compliance_score += 3

    compliance_score -= trend_penalty

    compliance_breakdown.append(
        {
            "factor": "Risk trend",
            "penalty": trend_penalty,
            "bonus": 3 if trend == "IMPROVING" else 0,
        }
    )

    compliance_score = round(
        max(
            0,
            min(
                100,
                compliance_score,
            ),
        ),
        1,
    )

    # ========================================================
    # INSPECTION PRIORITY
    #
    # Measures urgency for government intervention.
    # ========================================================

    priority_score = 0.0

    priority_breakdown = []

    red_priority = min(
        active_red * 7,
        35,
    )

    priority_score += red_priority

    priority_breakdown.append(
        {
            "factor": "Active RED alerts",
            "points": red_priority,
        }
    )

    orange_priority = min(
        active_orange * 3,
        12,
    )

    priority_score += orange_priority

    priority_breakdown.append(
        {
            "factor": "Active ORANGE alerts",
            "points": orange_priority,
        }
    )

    unresolved_priority = min(
        unresolved_investigations * 10,
        20,
    )

    priority_score += unresolved_priority

    priority_breakdown.append(
        {
            "factor": "Unresolved investigations",
            "points": unresolved_priority,
        }
    )

    # Incident volume
    volume_priority = 0

    if len(alerts) >= 15:
        volume_priority = 10

    elif len(alerts) >= 10:
        volume_priority = 7

    elif len(alerts) >= 5:
        volume_priority = 4

    priority_score += volume_priority

    priority_breakdown.append(
        {
            "factor": "Recent incident volume",
            "points": volume_priority,
        }
    )

    # Deterioration
    trend_priority = 0

    if trend == "DETERIORATING":
        trend_priority = 10

    elif trend == "STABLE":
        trend_priority = 2

    priority_score += trend_priority

    priority_breakdown.append(
        {
            "factor": "Risk trend",
            "points": trend_priority,
        }
    )

    priority_score = round(
        max(
            0,
            min(
                100,
                priority_score,
            ),
        ),
        1,
    )

    compliance_status = _compliance_status(
        compliance_score
    )

    inspection_priority = _priority_status(
        priority_score
    )

    # ========================================================
    # EXPLANATION
    # ========================================================

    strengths = []

    concerns = []

    if not active_red:
        strengths.append(
            "No active RED alerts"
        )

    if not active_orange:
        strengths.append(
            "No active ORANGE alerts"
        )

    if devices and online_devices == len(devices):
        strengths.append(
            "All registered IoT devices are online"
        )

    if closed_alerts and (
        closed_alerts >= len(alerts) * 0.75
    ):
        strengths.append(
            "Most recent alerts have been resolved"
        )

    if closure_rate is not None and closure_rate >= 0.80:
        strengths.append(
            "Strong investigation closure performance"
        )

    if trend == "IMPROVING":
        strengths.append(
            "Risk pressure is improving"
        )

    if active_red:
        concerns.append(
            f"{active_red} active RED alert(s)"
        )

    if active_orange:
        concerns.append(
            f"{active_orange} active ORANGE alert(s)"
        )

    if unresolved_investigations:
        concerns.append(
            f"{unresolved_investigations} unresolved investigation(s)"
        )

    if action_required:
        concerns.append(
            f"{action_required} case(s) requiring corrective action"
        )

    if trend == "DETERIORATING":
        concerns.append(
            "Recent risk pressure is deteriorating"
        )

    if devices and online_devices < len(devices):
        concerns.append(
            "Some IoT devices are offline"
        )

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    if inspection_priority == "CRITICAL":

        recommendation = (
            "Priority government inspection recommended."
        )

    elif inspection_priority == "HIGH":

        recommendation = (
            "Follow-up inspection and corrective-action review recommended."
        )

    elif compliance_status == "EXCELLENT":

        recommendation = (
            "Eligible for government appreciation, "
            "subject to officer review."
        )

    elif compliance_status in {
        "COMPLIANT",
        "WATCHLIST",
    }:

        recommendation = (
            "Continue monitoring and maintain compliance."
        )

    else:

        recommendation = (
            "Corrective action and follow-up monitoring recommended."
        )

    return {
        "outlet": {
            "id": restaurant.id,
            "name": restaurant.name,
            "registration_id":
                restaurant.registration_id,
            "location":
                restaurant.location,
            "state":
                restaurant.state,
            "region":
                restaurant.region,
        },

        "audit_period_days": days,

        # Main public compliance result
        "compliance_score":
            compliance_score,

        "status":
            compliance_status,

        # Government-only urgency
        "inspection_priority_score":
            priority_score,

        "inspection_priority":
            inspection_priority,

        "risk_trend":
            trend,

        "metrics": {
            "alerts":
                len(alerts),
            "active_red_alerts":
                active_red,
            "active_orange_alerts":
                active_orange,
            "closed_alerts":
                closed_alerts,
            "investigations":
                len(investigations),
            "unresolved_investigations":
                unresolved_investigations,
            "action_required":
                action_required,
            "devices":
                len(devices),
            "online_devices":
                online_devices,
        },

        "trend_metrics": {
            "previous_alert_pressure":
                previous_pressure,
            "recent_alert_pressure":
                recent_pressure,
        },

        "score_breakdown":
            compliance_breakdown,

        "priority_breakdown":
            priority_breakdown,

        "strengths":
            strengths,

        "concerns":
            concerns,

        "recommendation":
            recommendation,

        "data_sources": {
            "iot":
                len(devices) > 0,
            "government_alerts":
                len(alerts) > 0,
            "investigations":
                len(investigations) > 0,
            "hygiene_ai":
                False,
            "expiry_ai":
                False,
            "citizen_reports":
                False,
        },
    }


# ============================================================
# REGIONAL AUDIT
# ============================================================

def audit_region(
    db: Session,
    state: str | None = None,
    region: str | None = None,
    days: int = DEFAULT_DAYS,
) -> dict[str, Any]:

    days = max(
        1,
        min(
            365,
            days,
        ),
    )

    cutoff = (
        datetime.utcnow()
        - timedelta(days=days)
    )

    query = db.query(Restaurant)

    if state:
        query = query.filter(
            Restaurant.state == state
        )

    if region:
        query = query.filter(
            Restaurant.region == region
        )

    restaurants = (
        query
        .order_by(Restaurant.name.asc())
        .all()
    )

    audits = [
        _build_outlet_audit(
            db=db,
            restaurant=restaurant,
            cutoff=cutoff,
            days=days,
        )
        for restaurant in restaurants
    ]

    # Lowest compliance first for government attention.
    audits.sort(
        key=lambda item: (
            {
                "CRITICAL": 0,
                "WARNING": 1,
                "WATCHLIST": 2,
                "COMPLIANT": 3,
                "EXCELLENT": 4,
            }[
                item["status"]
            ],
            -item[
                "inspection_priority_score"
            ],
        )
    )

    summary = {
        "total_outlets":
            len(audits),

        "excellent":
            sum(
                1
                for item in audits
                if item["status"]
                == "EXCELLENT"
            ),

        "compliant":
            sum(
                1
                for item in audits
                if item["status"]
                == "COMPLIANT"
            ),

        "watchlist":
            sum(
                1
                for item in audits
                if item["status"]
                == "WATCHLIST"
            ),

        "warning":
            sum(
                1
                for item in audits
                if item["status"]
                == "WARNING"
            ),

        "critical":
            sum(
                1
                for item in audits
                if item["status"]
                == "CRITICAL"
            ),

        "critical_priority":
            sum(
                1
                for item in audits
                if item["inspection_priority"]
                == "CRITICAL"
            ),

        "high_priority":
            sum(
                1
                for item in audits
                if item["inspection_priority"]
                == "HIGH"
            ),

        "deteriorating":
            sum(
                1
                for item in audits
                if item["risk_trend"]
                == "DETERIORATING"
            ),

        "improving":
            sum(
                1
                for item in audits
                if item["risk_trend"]
                == "IMPROVING"
            ),

        "stable":
            sum(
                1
                for item in audits
                if item["risk_trend"]
                == "STABLE"
            ),
    }

    appreciation_candidates = [
        item
        for item in audits
        if item["status"] == "EXCELLENT"
        and item["inspection_priority"]
        == "LOW"
    ]

    warning_candidates = [
        item
        for item in audits
        if item["status"]
        in {
            "WARNING",
            "CRITICAL",
        }
    ]

    inspection_queue = sorted(
        audits,
        key=lambda item: (
            {
                "CRITICAL": 0,
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
            }[
                item["inspection_priority"]
            ],
            -item[
                "inspection_priority_score"
            ],
        ),
    )

    return {
        "audit_engine":
            "SafeBite Regional Auditor v2",

        "audit_period_days":
            days,

        "scope": {
            "state":
                state or "ALL",
            "region":
                region or "ALL",
        },

        "summary":
            summary,

        "appreciation_candidates":
            appreciation_candidates,

        "warning_candidates":
            warning_candidates,

        "inspection_priority_queue":
            inspection_queue,

        "generated_at":
            datetime.utcnow().isoformat(),
    }