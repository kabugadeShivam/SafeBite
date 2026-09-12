from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..models import (
    Alert,
    MonthlyAuditNotice,
)
from ..models_monthly import MonthlyAIAnalysis
from ..services.blockchain_service import create_audit_record
from ..services.monthly_ai_analyzer import (
    analyze_monthly_performance,
)
from ..services.notification_service import (
    deliver_monthly_notice,
)
from ..services.regional_auditor_intelligence import (
    audit_region_with_citizen_intelligence,
)


APPRECIATION_STATUSES = {
    "EXCELLENT",
    "GOOD",
}


def _month_label(audit_month: str) -> str:
    return datetime.strptime(
        audit_month,
        "%Y-%m",
    ).strftime("%B %Y")


def get_notice_type(
    public_status: str,
) -> str:
    if public_status in APPRECIATION_STATUSES:
        return "APPRECIATION"

    return "WARNING"


def get_notice_title(
    notice_type: str,
    audit_month: str,
) -> str:
    month = _month_label(audit_month)

    if notice_type == "APPRECIATION":
        return f"SafeBite Monthly Appreciation - {month}"

    return f"SafeBite Monthly Warning - {month}"


def get_notice_message(
    notice_type: str,
    outlet: dict[str, Any],
    assessment: dict[str, Any],
) -> str:
    outlet_name = outlet.get(
        "name",
        "Registered Food Outlet",
    )

    score = float(
        assessment.get(
            "score",
            0,
        )
    )

    status = assessment.get(
        "status",
        "UNKNOWN",
    )

    comment = assessment.get(
        "comment",
        "Monthly food-safety performance reviewed.",
    )

    if notice_type == "APPRECIATION":
        return (
            f"Dear {outlet_name},\n\n"
            f"Your SafeBite monthly food-safety score is "
            f"{score:.0f}/100 and your public status is {status}.\n\n"
            f"Assessment: {comment}\n\n"
            "Thank you for maintaining strong food-safety practices."
        )

    return (
        f"Dear {outlet_name},\n\n"
        f"Your SafeBite monthly food-safety score is "
        f"{score:.0f}/100 and your public status is {status}.\n\n"
        f"Assessment: {comment}\n\n"
        "Please review the identified issues and take corrective action."
    )


def _compact_current_audit(
    item: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_score": item.get("compliance_score", 0),
        "internal_status": item.get("status", "UNKNOWN"),
        "inspection_priority": item.get(
            "inspection_priority",
            "UNKNOWN",
        ),
        "risk_trend": item.get(
            "risk_trend",
            "UNKNOWN",
        ),
        "metrics": item.get(
            "metrics",
            {},
        ),
        "citizen_intelligence": item.get(
            "citizen_intelligence",
            {},
        ),
        "strengths": item.get(
            "strengths",
            [],
        ),
        "concerns": item.get(
            "concerns",
            [],
        ),
        "recommendation": item.get(
            "recommendation",
            "",
        ),
    }


def _month_bounds(
    audit_month: str,
) -> tuple[datetime, datetime]:
    start = datetime.strptime(
        audit_month,
        "%Y-%m",
    )

    if start.month == 12:
        end = datetime(
            start.year + 1,
            1,
            1,
        )
    else:
        end = datetime(
            start.year,
            start.month + 1,
            1,
        )

    return start, end


def _create_license_review_alert(
    db: Session,
    restaurant_id: int,
    audit_month: str,
    assessment: dict[str, Any],
) -> int | None:
    start, end = _month_bounds(audit_month)

    existing = (
        db.query(Alert)
        .filter(
            Alert.restaurant_id == restaurant_id,
            Alert.alert_type == "LICENCE_REVIEW_RECOMMENDED",
            Alert.timestamp >= start,
            Alert.timestamp < end,
        )
        .first()
    )

    if existing:
        return existing.id

    history_message = (
        "Persistent non-compliance detected across monthly assessments. "
        "AI recommends a physical government review before any licence action."
    )

    alert = Alert(
        alert_type="LICENCE_REVIEW_RECOMMENDED",
        severity="RED",
        risk_score=100.0,
        reason=(
            f"{history_message} "
            f"Current public score: {assessment['score']:.0f}/100. "
            f"Assessment: {assessment['comment']}"
        ),
        source="AI",
        status="OPEN",
        timestamp=datetime.utcnow(),
        restaurant_id=restaurant_id,
        device_id=None,
        sensor_reading_id=None,
    )

    db.add(alert)
    db.flush()

    create_audit_record(
        db=db,
        record_type="LICENCE_REVIEW_RECOMMENDED",
        entity_type="ALERT",
        entity_id=alert.id,
        actor_id=None,
        payload={
            "restaurant_id": restaurant_id,
            "audit_month": audit_month,
            "score": assessment["score"],
            "status": assessment["status"],
            "comment": assessment["comment"],
        },
    )

    return alert.id


def generate_monthly_notices(
    db: Session,
    state: str | None = None,
    region: str | None = None,
    audit_month: str | None = None,
    actor_id: int | None = None,
) -> dict[str, Any]:
    if audit_month is None:
        audit_month = datetime.utcnow().strftime("%Y-%m")

    datetime.strptime(
        audit_month,
        "%Y-%m",
    )

    audit = audit_region_with_citizen_intelligence(
        db=db,
        state=state,
        region=region,
        days=30,
    )

    queue = audit.get(
        "inspection_priority_queue",
        [],
    )

    created_ids: list[int] = []
    updated_ids: list[int] = []
    licence_review_alerts: list[int] = []
    delivery_results: list[dict[str, Any]] = []

    for item in queue:
        outlet = item.get("outlet", {})
        restaurant_id = outlet.get("id")

        if restaurant_id is None:
            continue

        history_rows = (
            db.query(MonthlyAIAnalysis)
            .filter(
                MonthlyAIAnalysis.restaurant_id == restaurant_id,
                MonthlyAIAnalysis.audit_month != audit_month,
            )
            .order_by(
                MonthlyAIAnalysis.audit_month.desc()
            )
            .limit(6)
            .all()
        )

        history = [
            {
                "audit_month": row.audit_month,
                "score": row.score,
                "status": row.public_status,
            }
            for row in history_rows
        ]

        current_input = _compact_current_audit(
            item
        )

        assessment = analyze_monthly_performance(
            current=current_input,
            history=history,
        )

        snapshot = json.dumps(
            {
                "current": current_input,
                "history": history,
            },
            default=str,
            separators=(",", ":"),
        )

        ai_record = (
            db.query(MonthlyAIAnalysis)
            .filter(
                MonthlyAIAnalysis.restaurant_id == restaurant_id,
                MonthlyAIAnalysis.audit_month == audit_month,
            )
            .first()
        )

        is_new_assessment = ai_record is None

        if ai_record is None:
            ai_record = MonthlyAIAnalysis(
                restaurant_id=restaurant_id,
                audit_month=audit_month,
                score=assessment["score"],
                public_status=assessment["status"],
                ai_comment=assessment["comment"],
                base_audit_score=assessment[
                    "base_audit_score"
                ],
                licence_review_recommended=assessment[
                    "licence_review_recommended"
                ],
                ai_model=assessment["ai_model"],
                input_snapshot=snapshot,
                generated_by=actor_id,
            )
            db.add(ai_record)
            db.flush()

            create_audit_record(
                db=db,
                record_type="MONTHLY_AI_ASSESSMENT_CREATED",
                entity_type="MONTHLY_AI_ANALYSIS",
                entity_id=ai_record.id,
                actor_id=actor_id,
                payload={
                    "restaurant_id": restaurant_id,
                    "audit_month": audit_month,
                    "score": assessment["score"],
                    "status": assessment["status"],
                    "comment": assessment["comment"],
                    "licence_review_recommended": assessment[
                        "licence_review_recommended"
                    ],
                    "ai_model": assessment["ai_model"],
                },
            )

            created_ids.append(ai_record.id)

        else:
            ai_record.score = assessment["score"]
            ai_record.public_status = assessment["status"]
            ai_record.ai_comment = assessment["comment"]
            ai_record.base_audit_score = assessment[
                "base_audit_score"
            ]
            ai_record.licence_review_recommended = assessment[
                "licence_review_recommended"
            ]
            ai_record.ai_model = assessment["ai_model"]
            ai_record.input_snapshot = snapshot

            if actor_id is not None:
                ai_record.generated_by = actor_id

            updated_ids.append(ai_record.id)

        if assessment["licence_review_recommended"]:
            alert_id = _create_license_review_alert(
                db=db,
                restaurant_id=restaurant_id,
                audit_month=audit_month,
                assessment=assessment,
            )

            if alert_id is not None:
                licence_review_alerts.append(alert_id)

        notice_type = get_notice_type(
            assessment["status"]
        )

        notice_title = get_notice_title(
            notice_type,
            audit_month,
        )

        notice_message = get_notice_message(
            notice_type,
            outlet,
            assessment,
        )

        notice = (
            db.query(MonthlyAuditNotice)
            .filter(
                MonthlyAuditNotice.restaurant_id == restaurant_id,
                MonthlyAuditNotice.audit_month == audit_month,
            )
            .first()
        )

        notice_is_new = notice is None

        if notice is None:
            notice = MonthlyAuditNotice(
                restaurant_id=restaurant_id,
                audit_month=audit_month,
                notice_type=notice_type,
                title=notice_title,
                message=notice_message,
                compliance_score=assessment["score"],
                compliance_status=assessment["status"],
                inspection_priority=str(
                    item.get(
                        "inspection_priority",
                        "UNKNOWN",
                    )
                ),
                risk_trend=str(
                    item.get(
                        "risk_trend",
                        "UNKNOWN",
                    )
                ),
                strengths=json.dumps(
                    item.get(
                        "strengths",
                        [],
                    ),
                    default=str,
                ),
                concerns=json.dumps(
                    item.get(
                        "concerns",
                        [],
                    ),
                    default=str,
                ),
                recommendation=str(
                    item.get(
                        "recommendation",
                        "",
                    )
                ),
                delivery_status="PENDING_CONTACT",
                generated_by=actor_id,
            )
            db.add(notice)
            db.flush()

            create_audit_record(
                db=db,
                record_type="MONTHLY_AUDIT_NOTICE_ISSUED",
                entity_type="MONTHLY_AUDIT_NOTICE",
                entity_id=notice.id,
                actor_id=actor_id,
                payload={
                    "restaurant_id": restaurant_id,
                    "audit_month": audit_month,
                    "notice_type": notice_type,
                    "score": assessment["score"],
                    "status": assessment["status"],
                    "comment": assessment["comment"],
                },
            )

        else:
            notice.notice_type = notice_type
            notice.title = notice_title
            notice.message = notice_message
            notice.compliance_score = assessment["score"]
            notice.compliance_status = assessment["status"]
            notice.inspection_priority = str(
                item.get(
                    "inspection_priority",
                    "UNKNOWN",
                )
            )
            notice.risk_trend = str(
                item.get(
                    "risk_trend",
                    "UNKNOWN",
                )
            )
            notice.strengths = json.dumps(
                item.get(
                    "strengths",
                    [],
                ),
                default=str,
            )
            notice.concerns = json.dumps(
                item.get(
                    "concerns",
                    [],
                ),
                default=str,
            )
            notice.recommendation = str(
                item.get(
                    "recommendation",
                    "",
                )
            )

            if actor_id is not None:
                notice.generated_by = actor_id

        # ----------------------------------------------------
        # Deliver exactly once automatically when possible.
        # Manual regeneration can retry a failed/not-configured
        # delivery after contact or provider configuration changes.
        # ----------------------------------------------------

        if notice_is_new or notice.delivery_status != "SENT":
            delivery = deliver_monthly_notice(
                db=db,
                notice=notice,
            )
            delivery_results.append(
                {
                    "notice_id": notice.id,
                    **delivery,
                }
            )

            if delivery["delivery_status"] in {
                "SENT",
                "PARTIAL",
            }:
                create_audit_record(
                    db=db,
                    record_type="MONTHLY_NOTICE_DELIVERY",
                    entity_type="MONTHLY_AUDIT_NOTICE",
                    entity_id=notice.id,
                    actor_id=actor_id,
                    payload={
                        "restaurant_id": restaurant_id,
                        "audit_month": audit_month,
                        "delivery": delivery,
                    },
                )

    db.commit()

    return {
        "audit_month": audit_month,
        "scope": {
            "state": state or "ALL",
            "region": region or "ALL",
        },
        "total_outlets_audited": len(queue),
        "assessments_created": len(created_ids),
        "assessments_updated": len(updated_ids),
        "created_assessment_ids": created_ids,
        "updated_assessment_ids": updated_ids,
        "licence_review_alerts": sorted(
            set(licence_review_alerts)
        ),
        "delivery": delivery_results,
    }
