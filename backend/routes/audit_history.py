from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    AIDetection,
    Alert,
    GovernmentOfficer,
    Investigation,
    Restaurant,
)
from ..models_citizen import CitizenReport
from ..security import get_token_payload


router = APIRouter(
    prefix="/government/audit-history",
    tags=["Audit History"],
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
            GovernmentOfficer.id
            == officer_id
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
# SCORE CALCULATION
# ============================================================

def calculate_period_score(
    db: Session,
    restaurant_id: int,
    start_time: datetime,
    end_time: datetime,
) -> dict:

    # --------------------------------------------------------
    # GOVERNMENT ALERTS
    # --------------------------------------------------------

    alerts = (
        db.query(Alert)
        .filter(
            Alert.restaurant_id == restaurant_id,
            Alert.timestamp >= start_time,
            Alert.timestamp < end_time,
        )
        .all()
    )

    # --------------------------------------------------------
    # INVESTIGATIONS
    # --------------------------------------------------------

    investigations = (
        db.query(Investigation)
        .join(Alert)
        .filter(
            Alert.restaurant_id == restaurant_id,
            Investigation.started_at >= start_time,
            Investigation.started_at < end_time,
        )
        .all()
    )

    # --------------------------------------------------------
    # AI FINDINGS
    # --------------------------------------------------------

    ai_detections = (
        db.query(AIDetection)
        .filter(
            AIDetection.restaurant_id
            == restaurant_id,
            AIDetection.timestamp >= start_time,
            AIDetection.timestamp < end_time,
        )
        .all()
    )

    # --------------------------------------------------------
    # VERIFIED CITIZEN REPORTS
    #
    # Unverified reports are not treated as official
    # violations. They are evidence for government review.
    # --------------------------------------------------------

    citizen_reports = (
        db.query(CitizenReport)
        .filter(
            CitizenReport.restaurant_id
            == restaurant_id,
            CitizenReport.submitted_at >= start_time,
            CitizenReport.submitted_at < end_time,
            CitizenReport.status == "VERIFIED",
        )
        .all()
    )

    # ========================================================
    # ALERT METRICS
    # ========================================================

    active_red = sum(
        1
        for alert in alerts
        if str(
            alert.severity
        ).upper() == "RED"
        and str(
            alert.status
        ).upper() != "CLOSED"
    )

    active_orange = sum(
        1
        for alert in alerts
        if str(
            alert.severity
        ).upper() == "ORANGE"
        and str(
            alert.status
        ).upper() != "CLOSED"
    )

    closed_alerts = sum(
        1
        for alert in alerts
        if str(
            alert.status
        ).upper() == "CLOSED"
    )

    # ========================================================
    # INVESTIGATION METRICS
    # ========================================================

    unresolved_investigations = sum(
        1
        for investigation in investigations
        if str(
            investigation.status
        ).upper() != "CLOSED"
    )

    closed_investigations = sum(
        1
        for investigation in investigations
        if str(
            investigation.status
        ).upper() == "CLOSED"
    )

    # ========================================================
    # AI METRICS
    # ========================================================

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
        for detection in ai_detections
        if str(
            detection.detection_type
        ).strip().lower()
        in (
            hygiene_labels
            | critical_labels
        )
    ]

    critical_ai_findings = [
        detection
        for detection in hygiene_findings
        if str(
            detection.detection_type
        ).strip().lower()
        in critical_labels
    ]

    # ========================================================
    # COMPLIANCE SCORE
    # ========================================================

    score = 100.0

    # Alerts
    red_penalty = min(
        active_red * 6,
        18,
    )

    orange_penalty = min(
        active_orange * 3,
        9,
    )

    score -= red_penalty
    score -= orange_penalty

    # Investigations
    investigation_penalty = min(
        unresolved_investigations * 5,
        10,
    )

    score -= investigation_penalty

    # Investigation closure
    closure_penalty = 0

    if investigations:

        closure_rate = (
            closed_investigations
            / len(investigations)
        )

        if closure_rate < 0.50:
            closure_penalty = 6

        elif closure_rate < 0.80:
            closure_penalty = 3

    score -= closure_penalty

    # AI hygiene
    ai_penalty = min(
        len(hygiene_findings) * 4,
        16,
    )

    score -= ai_penalty

    # AI contamination
    critical_ai_penalty = min(
        len(critical_ai_findings) * 8,
        16,
    )

    score -= critical_ai_penalty

    # Verified citizen reports
    citizen_penalty = min(
        len(citizen_reports) * 4,
        12,
    )

    score -= citizen_penalty

    score = round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        1,
    )

    # ========================================================
    # PERIOD PRIORITY
    # ========================================================

    priority = 0.0

    priority += min(
        active_red * 7,
        35,
    )

    priority += min(
        active_orange * 3,
        12,
    )

    priority += min(
        unresolved_investigations * 10,
        20,
    )

    priority += min(
        len(hygiene_findings) * 5,
        20,
    )

    priority += min(
        len(critical_ai_findings) * 10,
        25,
    )

    priority += min(
        len(citizen_reports) * 5,
        15,
    )

    priority = round(
        max(
            0,
            min(
                100,
                priority,
            ),
        ),
        1,
    )

    return {
        "score": score,

        "inspection_priority_score":
            priority,

        "alerts":
            len(alerts),

        "active_red":
            active_red,

        "active_orange":
            active_orange,

        "closed_alerts":
            closed_alerts,

        "investigations":
            len(investigations),

        "unresolved_investigations":
            unresolved_investigations,

        "closed_investigations":
            closed_investigations,

        "ai_detections":
            len(ai_detections),

        "hygiene_ai_findings":
            len(hygiene_findings),

        "critical_ai_findings":
            len(critical_ai_findings),

        "verified_citizen_reports":
            len(citizen_reports),
    }


# ============================================================
# TREND
# ============================================================

def trend_label(
    first_score: float,
    last_score: float,
) -> str:

    difference = (
        last_score
        - first_score
    )

    if difference >= 5:
        return "IMPROVING"

    if difference <= -5:
        return "DETERIORATING"

    return "STABLE"


# ============================================================
# OUTLET AUDIT HISTORY
# ============================================================

@router.get(
    "/outlets/{registration_id}"
)
def get_outlet_audit_history(
    registration_id: str,

    days: int = 30,

    officer: GovernmentOfficer = Depends(
        get_current_officer
    ),

    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Keep history between 7 and 90 days.
    # --------------------------------------------------------

    days = max(
        7,
        min(
            90,
            days,
        ),
    )

    # --------------------------------------------------------
    # Find outlet.
    # --------------------------------------------------------

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.registration_id
            == registration_id
        )
        .first()
    )

    if not restaurant:

        raise HTTPException(
            status_code=404,
            detail="Outlet not found",
        )

    # --------------------------------------------------------
    # Regional access control.
    # --------------------------------------------------------

    if (
        officer.role.upper()
        != "CENTRAL_ADMIN"
    ):

        if (
            restaurant.state.lower()
            != officer.state.lower()
            or restaurant.region.lower()
            != officer.region.lower()
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Outlet is outside your authorized region"
                ),
            )

    # --------------------------------------------------------
    # Build historical periods.
    # --------------------------------------------------------

    now = datetime.utcnow()

    number_of_points = min(
        6,
        max(
            2,
            days // 7,
        ),
    )

    period_days = max(
        1,
        days // number_of_points,
    )

    history = []

    for index in range(
        number_of_points
    ):

        period_start = (
            now
            - timedelta(
                days=(
                    days
                    - (
                        index
                        * period_days
                    )
                )
            )
        )

        period_end = (
            period_start
            + timedelta(
                days=period_days
            )
        )

        # Last period ends exactly at now.
        if (
            index
            == number_of_points - 1
        ):

            period_end = now

        metrics = calculate_period_score(
            db=db,

            restaurant_id=
                restaurant.id,

            start_time=
                period_start,

            end_time=
                period_end,
        )

        history.append(
            {
                "period_start":
                    period_start.isoformat(),

                "period_end":
                    period_end.isoformat(),

                "score":
                    metrics["score"],

                "inspection_priority_score":
                    metrics[
                        "inspection_priority_score"
                    ],

                "alerts":
                    metrics["alerts"],

                "active_red":
                    metrics["active_red"],

                "active_orange":
                    metrics["active_orange"],

                "closed_alerts":
                    metrics["closed_alerts"],

                "investigations":
                    metrics["investigations"],

                "unresolved_investigations":
                    metrics[
                        "unresolved_investigations"
                    ],

                "ai_detections":
                    metrics["ai_detections"],

                "hygiene_ai_findings":
                    metrics[
                        "hygiene_ai_findings"
                    ],

                "critical_ai_findings":
                    metrics[
                        "critical_ai_findings"
                    ],

                "verified_citizen_reports":
                    metrics[
                        "verified_citizen_reports"
                    ],
            }
        )

    # ========================================================
    # CURRENT / TREND VALUES
    # ========================================================

    scores = [
        point["score"]
        for point in history
    ]

    priority_scores = [
        point[
            "inspection_priority_score"
        ]
        for point in history
    ]

    first_score = (
        scores[0]
        if scores
        else 0
    )

    current_score = (
        scores[-1]
        if scores
        else 0
    )

    first_priority = (
        priority_scores[0]
        if priority_scores
        else 0
    )

    current_priority = (
        priority_scores[-1]
        if priority_scores
        else 0
    )

    score_change = round(
        current_score
        - first_score,
        1,
    )

    priority_change = round(
        current_priority
        - first_priority,
        1,
    )

    trend = trend_label(
        first_score,
        current_score,
    )

    # ========================================================
    # CURRENT PERIOD EVIDENCE
    # ========================================================

    current_period = (
        history[-1]
        if history
        else {}
    )

    return {
        "outlet": {
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
        },

        "period_days":
            days,

        "current_score":
            current_score,

        "score_change":
            score_change,

        "current_inspection_priority":
            current_priority,

        "inspection_priority_change":
            priority_change,

        "trend":
            trend,

        "current_evidence": {
            "alerts":
                current_period.get(
                    "alerts",
                    0,
                ),

            "active_red":
                current_period.get(
                    "active_red",
                    0,
                ),

            "active_orange":
                current_period.get(
                    "active_orange",
                    0,
                ),

            "investigations":
                current_period.get(
                    "investigations",
                    0,
                ),

            "unresolved_investigations":
                current_period.get(
                    "unresolved_investigations",
                    0,
                ),

            "ai_detections":
                current_period.get(
                    "ai_detections",
                    0,
                ),

            "hygiene_ai_findings":
                current_period.get(
                    "hygiene_ai_findings",
                    0,
                ),

            "critical_ai_findings":
                current_period.get(
                    "critical_ai_findings",
                    0,
                ),

            "verified_citizen_reports":
                current_period.get(
                    "verified_citizen_reports",
                    0,
                ),
        },

        "history":
            history,

        "generated_at":
            now.isoformat(),

        "data_sources": {
            "government_alerts":
                True,

            "investigations":
                True,

            "hygiene_ai":
                any(
                    point[
                        "ai_detections"
                    ] > 0
                    for point
                    in history
                ),

            "verified_citizen_reports":
                any(
                    point[
                        "verified_citizen_reports"
                    ] > 0
                    for point
                    in history
                ),
        },

        "explanation": (
            "Historical compliance indicators combine "
            "government alerts, investigations, stored "
            "AI hygiene findings, and government-verified "
            "citizen reports for each audit period."
        ),
    }