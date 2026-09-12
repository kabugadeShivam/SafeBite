from __future__ import annotations

import json
import os
import re
from datetime import date
from typing import Any

import requests


PUBLIC_STATUS_THRESHOLDS = (
    (90, "EXCELLENT"),
    (75, "GOOD"),
    (60, "WATCH"),
    (40, "POOR"),
    (0, "CRITICAL"),
)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
AI_SCORE_GUARDRAIL = 15.0
PERSISTENT_MONTHS = int(
    os.getenv("SAFEBITE_PERSISTENT_MONTHS", "3")
)
PERSISTENT_SCORE_THRESHOLD = float(
    os.getenv("SAFEBITE_PERSISTENT_SCORE_THRESHOLD", "60")
)


class MonthlyAIError(RuntimeError):
    pass


def public_status_from_score(score: float) -> str:
    score = max(0.0, min(100.0, float(score)))

    for threshold, status in PUBLIC_STATUS_THRESHOLDS:
        if score >= threshold:
            return status

    return "CRITICAL"


def _clean_comment(value: Any) -> str:
    comment = " ".join(str(value or "").split())

    if not comment:
        return "Monthly food-safety performance reviewed."

    return comment[:180]


def _fallback_comment(current: dict[str, Any]) -> str:
    concerns = current.get("concerns") or []

    if concerns:
        return " ".join(str(concerns[0]).split())[:180]

    trend = str(
        current.get("risk_trend") or "STABLE"
    ).replace("_", " ").lower()

    return f"Monthly food-safety performance is {trend}."


def _persistent_failure(
    history: list[dict[str, Any]],
    current_score: float,
) -> bool:
    """Count consecutive low monthly assessments from newest to oldest."""
    scores = [current_score]

    for item in history:
        try:
            scores.append(float(item.get("score", 100)))
        except (TypeError, ValueError):
            continue

    consecutive = 0

    for score in scores:
        if score > PERSISTENT_SCORE_THRESHOLD:
            break

        consecutive += 1

        if consecutive >= PERSISTENT_MONTHS:
            return True

    return False


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise MonthlyAIError("AI response did not contain JSON")

    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise MonthlyAIError("AI response contained invalid JSON") from exc

    if not isinstance(value, dict):
        raise MonthlyAIError("AI response was not a JSON object")

    return value


def _call_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise MonthlyAIError("GEMINI_API_KEY is not configured")

    model = os.getenv(
        "GEMINI_MODEL",
        DEFAULT_GEMINI_MODEL,
    ).strip() or DEFAULT_GEMINI_MODEL

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    prompt = f"""
You are the SafeBite Monthly Food-Safety Performance Analyst.

Analyze only the official SafeBite evidence supplied below.

Rules:
1. Do not invent incidents, evidence, or legal conclusions.
2. A citizen report is negative evidence only when it is VERIFIED by government.
3. The base audit score is the official deterministic baseline.
4. Keep the AI score within 15 points of that baseline.
5. Public status must be exactly one of: EXCELLENT, GOOD, WATCH, POOR, CRITICAL.
6. Comment must be one short citizen-friendly sentence.
7. Persistent failure means repeated low monthly assessments; SafeBite will enforce the persistence rule.
8. Licence review is a government decision; only recommend a physical review.

CURRENT OFFICIAL AUDIT:
{json.dumps(payload.get('current'), ensure_ascii=False, default=str)}

PREVIOUS MONTHLY ASSESSMENTS:
{json.dumps(payload.get('history'), ensure_ascii=False, default=str)}

Return ONLY JSON:
{{
  "score": 0,
  "status": "GOOD",
  "comment": "Short reason.",
  "licence_review_recommended": false
}}
""".strip()

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json=body,
            timeout=25,
        )
    except requests.RequestException as exc:
        raise MonthlyAIError(
            f"Gemini request failed: {exc}"
        ) from exc

    if not response.ok:
        raise MonthlyAIError(
            f"Gemini API returned HTTP {response.status_code}"
        )

    try:
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise MonthlyAIError(
            "Gemini response did not contain usable generated text"
        ) from exc

    return _extract_json(text)


def analyze_monthly_performance(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    audit_month: str | None = None,
) -> dict[str, Any]:
    base_score = float(
        current.get("compliance_score", 0)
    )
    _ = audit_month or date.today().strftime("%Y-%m")

    payload = {
        "current": current,
        "history": history,
    }

    ai_model = "RULE_BASED_FALLBACK"

    try:
        generated = _call_gemini(payload)
        ai_model = os.getenv(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL,
        ).strip() or DEFAULT_GEMINI_MODEL

        requested_score = float(
            generated.get("score", base_score)
        )

        score = max(
            base_score - AI_SCORE_GUARDRAIL,
            min(
                base_score + AI_SCORE_GUARDRAIL,
                requested_score,
            ),
        )
        score = max(0.0, min(100.0, score))
        comment = _clean_comment(
            generated.get("comment")
        )

    except (MonthlyAIError, TypeError, ValueError):
        score = max(0.0, min(100.0, base_score))
        comment = _fallback_comment(current)

    status = public_status_from_score(score)

    persistent_failure = _persistent_failure(
        history,
        score,
    )

    # Persistence is deterministic. The AI supplies the score/comment,
    # while repeated official failures trigger the licence-review alert.
    licence_review_recommended = persistent_failure

    return {
        "score": round(score, 1),
        "status": status,
        "comment": comment,
        "licence_review_recommended": licence_review_recommended,
        "base_audit_score": round(base_score, 1),
        "ai_model": ai_model,
        "persistent_failure": persistent_failure,
        "persistent_months": PERSISTENT_MONTHS,
        "persistent_threshold": PERSISTENT_SCORE_THRESHOLD,
    }
