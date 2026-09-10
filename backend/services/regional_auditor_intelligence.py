from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..models_citizen import CitizenReport
from .regional_auditor import audit_region


def _status(score: float) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 80:
        return "COMPLIANT"
    if score >= 65:
        return "WATCHLIST"
    if score >= 50:
        return "WARNING"
    return "CRITICAL"


def _priority(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _clamp(value: float) -> float:
    return round(
        max(
            0,
            min(
                100,
                value,
            ),
        ),
        1,
    )


def audit_region_with_citizen_intelligence(
    db: Session,
    state: str | None = None,
    region: str | None = None,
    days: int = 30,
) -> dict[str, Any]:

    result = audit_region(
        db=db,
        state=state,
        region=region,
        days=days,
    )

    cutoff = (
        datetime.utcnow()
        - timedelta(days=days)
    )

    # --------------------------------------------------------
    # Add citizen intelligence to every outlet.
    # --------------------------------------------------------

    for item in result["inspection_priority_queue"]:

        outlet_id = item["outlet"]["id"]

        reports = (
            db.query(CitizenReport)
            .filter(
                CitizenReport.restaurant_id
                == outlet_id,

                CitizenReport.submitted_at
                >= cutoff,
            )
            .all()
        )

        active_reports = [
            report
            for report in reports
            if report.status
            not in {
                "DISMISSED",
            }
        ]

        relevant_reports = [
            report
            for report in active_reports
            if float(
                report.ai_relevance
                or 0
            ) >= 0.50
            or report.status
            == "VERIFIED"
        ]

        verified_reports = [
            report
            for report in active_reports
            if report.status
            == "VERIFIED"
        ]

        # ----------------------------------------------------
        # Recent report cluster.
        # ----------------------------------------------------

        cluster_cutoff = (
            datetime.utcnow()
            - timedelta(hours=72)
        )

        recent_relevant = [
            report
            for report in relevant_reports
            if report.submitted_at
            >= cluster_cutoff
        ]

        cluster_detected = (
            len(recent_relevant) >= 3
        )

        # ----------------------------------------------------
        # Compliance effect.
        #
        # UNVERIFIED citizen reports do not directly punish
        # the outlet.
        #
        # VERIFIED reports can reduce compliance modestly.
        # ----------------------------------------------------

        compliance_penalty = min(
            len(verified_reports) * 4,
            12,
        )

        item["compliance_score"] = _clamp(
            item["compliance_score"]
            - compliance_penalty
        )

        item["status"] = _status(
            item["compliance_score"]
        )

        # ----------------------------------------------------
        # Inspection priority effect.
        #
        # Relevant citizen evidence can increase priority
        # before an official violation is confirmed.
        # ----------------------------------------------------

        citizen_priority = min(
            len(relevant_reports) * 3,
            12,
        )

        verified_priority = min(
            len(verified_reports) * 5,
            15,
        )

        cluster_priority = (
            8
            if cluster_detected
            else 0
        )

        citizen_priority_total = (
            citizen_priority
            + verified_priority
            + cluster_priority
        )

        item["inspection_priority_score"] = _clamp(
            item["inspection_priority_score"]
            + citizen_priority_total
        )

        item["inspection_priority"] = _priority(
            item["inspection_priority_score"]
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        item["metrics"].update(
            {
                "citizen_reports":
                    len(reports),

                "active_citizen_reports":
                    len(active_reports),

                "relevant_citizen_reports":
                    len(relevant_reports),

                "verified_citizen_reports":
                    len(verified_reports),

                "recent_citizen_cluster":
                    len(recent_relevant),
            }
        )

        # ----------------------------------------------------
        # Citizen summary
        # ----------------------------------------------------

        item["citizen_intelligence"] = {
            "total_reports":
                len(reports),

            "active_reports":
                len(active_reports),

            "relevant_reports":
                len(relevant_reports),

            "verified_reports":
                len(verified_reports),

            "cluster_detected":
                cluster_detected,

            "cluster_size":
                len(recent_relevant),

            "categories": [
                report.concern_category
                for report
                in relevant_reports
            ],

            "preliminary_findings": [
                {
                    "report_id":
                        report.id,

                    "category":
                        report.concern_category,

                    "ai_status":
                        report.ai_status,

                    "relevance":
                        report.ai_relevance,

                    "severity":
                        report.ai_severity,

                    "status":
                        report.status,
                }
                for report
                in relevant_reports
            ],
        }

        # ----------------------------------------------------
        # Explainability
        # ----------------------------------------------------

        if relevant_reports:

            item["concerns"].append(
                f"{len(relevant_reports)} "
                "relevant citizen report(s)"
            )

        if verified_reports:

            item["concerns"].append(
                f"{len(verified_reports)} "
                "government-verified citizen report(s)"
            )

        if cluster_detected:

            item["concerns"].append(
                "Citizen report cluster detected within 72 hours"
            )

        # ----------------------------------------------------
        # Data-source flag
        # ----------------------------------------------------

        item["data_sources"][
            "citizen_reports"
        ] = len(reports) > 0

        # ----------------------------------------------------
        # Recommendation
        # ----------------------------------------------------

        if item["inspection_priority"] == "CRITICAL":

            item["recommendation"] = (
                "Priority government inspection recommended."
            )

        elif item["inspection_priority"] == "HIGH":

            item["recommendation"] = (
                "Follow-up inspection recommended; "
                "review citizen evidence and corrective action."
            )

    # ========================================================
    # Rebuild regional summary after citizen adjustments.
    # ========================================================

    audits = result[
        "inspection_priority_queue"
    ]

    result["summary"] = {
        "total_outlets":
            len(audits),

        "excellent":
            sum(
                1
                for x in audits
                if x["status"]
                == "EXCELLENT"
            ),

        "compliant":
            sum(
                1
                for x in audits
                if x["status"]
                == "COMPLIANT"
            ),

        "watchlist":
            sum(
                1
                for x in audits
                if x["status"]
                == "WATCHLIST"
            ),

        "warning":
            sum(
                1
                for x in audits
                if x["status"]
                == "WARNING"
            ),

        "critical":
            sum(
                1
                for x in audits
                if x["status"]
                == "CRITICAL"
            ),

        "critical_priority":
            sum(
                1
                for x in audits
                if x["inspection_priority"]
                == "CRITICAL"
            ),

        "high_priority":
            sum(
                1
                for x in audits
                if x["inspection_priority"]
                == "HIGH"
            ),

        "medium_priority":
            sum(
                1
                for x in audits
                if x["inspection_priority"]
                == "MEDIUM"
            ),

        "citizen_reports":
            sum(
                x["metrics"].get(
                    "citizen_reports",
                    0,
                )
                for x in audits
            ),

        "relevant_citizen_reports":
            sum(
                x["metrics"].get(
                    "relevant_citizen_reports",
                    0,
                )
                for x in audits
            ),

        "verified_citizen_reports":
            sum(
                x["metrics"].get(
                    "verified_citizen_reports",
                    0,
                )
                for x in audits
            ),

        "citizen_clusters":
            sum(
                1
                for x in audits
                if x.get(
                    "citizen_intelligence",
                    {}
                ).get(
                    "cluster_detected",
                    False,
                )
            ),
    }

    # --------------------------------------------------------
    # Rebuild queues.
    # --------------------------------------------------------

    result["inspection_priority_queue"] = sorted(
        audits,
        key=lambda x: (
            {
                "CRITICAL": 0,
                "HIGH": 1,
                "MEDIUM": 2,
                "LOW": 3,
            }[
                x["inspection_priority"]
            ],
            -x["inspection_priority_score"],
            x["compliance_score"],
        ),
    )

    result["appreciation_candidates"] = [
        x
        for x in audits
        if x["status"]
        == "EXCELLENT"
        and x["inspection_priority"]
        == "LOW"
    ]

    result["warning_candidates"] = [
        x
        for x in audits
        if x["status"]
        in {
            "WARNING",
            "CRITICAL",
        }
    ]

    result["audit_engine"] = (
        "SafeBite Regional Auditor v3 "
        "+ Citizen Intelligence"
    )

    return result