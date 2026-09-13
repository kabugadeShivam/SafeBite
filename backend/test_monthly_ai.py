"""Small dependency-free checks for the SafeBite monthly AI rules."""

from services.monthly_ai_analyzer import analyze_monthly_performance
from services.monthly_notice_service import _compact_current_audit


# No GEMINI_API_KEY is required for these checks; the deterministic fallback is used.

def main() -> None:
    # Regression check: the monthly notice pipeline must pass the official
    # compliance score under the exact key expected by the AI analyzer.
    compact = _compact_current_audit({"compliance_score": 52})
    assert compact["compliance_score"] == 52
    assert "base_score" not in compact

    excellent = analyze_monthly_performance(
        current={"compliance_score": 95, "risk_trend": "IMPROVING"},
        history=[],
        audit_month="2026-09",
    )
    assert excellent["score"] == 95.0
    assert excellent["status"] == "EXCELLENT"

    warning = analyze_monthly_performance(
        current={
            "compliance_score": 52,
            "risk_trend": "DETERIORATING",
            "concerns": ["Repeated hygiene violations"],
        },
        history=[],
        audit_month="2026-09",
    )
    assert warning["score"] == 52.0
    assert warning["status"] == "POOR"
    assert warning["licence_review_recommended"] is False

    persistent = analyze_monthly_performance(
        current={"compliance_score": 55},
        history=[
            {"audit_month": "2026-08", "score": 58},
            {"audit_month": "2026-07", "score": 54},
        ],
        audit_month="2026-09",
    )
    assert persistent["persistent_failure"] is True
    assert persistent["licence_review_recommended"] is True

    recovered = analyze_monthly_performance(
        current={"compliance_score": 75},
        history=[
            {"audit_month": "2026-08", "score": 55},
            {"audit_month": "2026-07", "score": 52},
        ],
        audit_month="2026-09",
    )
    assert recovered["persistent_failure"] is False
    assert recovered["licence_review_recommended"] is False

    print("SafeBite monthly AI checks: PASS")


if __name__ == "__main__":
    main()
