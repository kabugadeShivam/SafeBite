from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import MonthlyAuditNotice
from ..services.regional_auditor_intelligence import (
    audit_region_with_citizen_intelligence,
)
from ..services.blockchain_service import (
    create_audit_record,
)


APPRECIATION_STATUSES = {
    "EXCELLENT",
    "COMPLIANT",
}


def get_notice_type(
    compliance_status: str,
) -> str:

    if compliance_status in APPRECIATION_STATUSES:
        return "APPRECIATION"

    return "WARNING"


def get_notice_title(
    notice_type: str,
    audit_month: str,
) -> str:

    month_label = datetime.strptime(
        audit_month,
        "%Y-%m",
    ).strftime("%B %Y")

    if notice_type == "APPRECIATION":
        return (
            f"Monthly Food Safety Appreciation Notice - "
            f"{month_label}"
        )

    return (
        f"Monthly Food Safety Warning Notice - "
        f"{month_label}"
    )


def get_notice_message(
    notice_type: str,
    outlet: dict[str, Any],
    audit: dict[str, Any],
) -> str:

    outlet_name = outlet.get(
        "name",
        "Registered Food Outlet",
    )

    score = audit.get(
        "compliance_score",
        0,
    )

    status = audit.get(
        "status",
        "UNKNOWN",
    )

    recommendation = audit.get(
        "recommendation",
        "",
    )

    if notice_type == "APPRECIATION":
        return (
            f"Dear {outlet_name},\n\n"
            f"Your outlet received a food-safety compliance "
            f"score of {score}/100 for the {status} category "
            f"in the current monthly audit.\n\n"
            f"This notice records the positive government "
            f"assessment for the audit period.\n\n"
            f"Government recommendation: {recommendation}"
        )

    return (
        f"Dear {outlet_name},\n\n"
        f"Your outlet received a food-safety compliance "
        f"score of {score}/100 and the official status is "
        f"{status} for the current monthly audit.\n\n"
        f"This notice records areas requiring attention "
        f"and corrective action.\n\n"
        f"Government recommendation: {recommendation}"
    )


def generate_monthly_notices(
    db: Session,
    state: str | None = None,
    region: str | None = None,
    audit_month: str | None = None,
    actor_id: int | None = None,
) -> dict[str, Any]:

    if audit_month is None:
        audit_month = datetime.utcnow().strftime("%Y-%m")

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

    created_ids = []
    updated_ids = []

    for item in queue:

        outlet = item.get(
            "outlet",
            {},
        )

        restaurant_id = outlet.get(
            "id"
        )

        if restaurant_id is None:
            continue

        compliance_status = str(
            item.get(
                "status",
                "UNKNOWN",
            )
        ).upper()

        notice_type = get_notice_type(
            compliance_status
        )

        title = get_notice_title(
            notice_type,
            audit_month,
        )

        message = get_notice_message(
            notice_type,
            outlet,
            item,
        )

        existing = (
            db.query(
                MonthlyAuditNotice
            )
            .filter(
                MonthlyAuditNotice.restaurant_id
                == restaurant_id,

                MonthlyAuditNotice.audit_month
                == audit_month,
            )
            .first()
        )

        if existing:

            existing.notice_type = notice_type
            existing.title = title
            existing.message = message

            existing.compliance_score = float(
                item.get(
                    "compliance_score",
                    0,
                )
            )

            existing.compliance_status = (
                compliance_status
            )

            existing.inspection_priority = str(
                item.get(
                    "inspection_priority",
                    "UNKNOWN",
                )
            )

            existing.risk_trend = str(
                item.get(
                    "risk_trend",
                    "UNKNOWN",
                )
            )

            existing.strengths = json.dumps(
                item.get(
                    "strengths",
                    [],
                ),
                default=str,
            )

            existing.concerns = json.dumps(
                item.get(
                    "concerns",
                    [],
                ),
                default=str,
            )

            existing.recommendation = str(
                item.get(
                    "recommendation",
                    "",
                )
            )

            if actor_id is not None:
                existing.generated_by = actor_id

            updated_ids.append(
                existing.id
            )

            continue

        notice = MonthlyAuditNotice(
            restaurant_id=restaurant_id,
            audit_month=audit_month,
            notice_type=notice_type,
            title=title,
            message=message,
            compliance_score=float(
                item.get(
                    "compliance_score",
                    0,
                )
            ),
            compliance_status=compliance_status,
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
            delivery_status="IN_SYSTEM",
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
                "compliance_score":
                    notice.compliance_score,
                "compliance_status":
                    notice.compliance_status,
                "inspection_priority":
                    notice.inspection_priority,
            },
        )

        created_ids.append(
            notice.id
        )

    db.commit()

    return {
        "audit_month": audit_month,
        "scope": {
            "state": state or "ALL",
            "region": region or "ALL",
        },
        "total_outlets_audited": len(queue),
        "notices_created": len(created_ids),
        "notices_updated": len(updated_ids),
        "created_ids": created_ids,
        "updated_ids": updated_ids,
    }