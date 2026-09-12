from __future__ import annotations

import json
import os
import re
from typing import Any

import requests


PUBLIC_STATUS_THRESHOLDS = (
    (90, "EXCELLENT"),
    (75, "GOOD"),
    (60, "WATCH"),
    (40, "POOR"),
    (0, "CRITICAL"),
)

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
AI_SCORE_GUARDRAIL = 15.0
PERSISTENT_MONTHS = 3
PERSISTENT_SCORE_THRESHOLD = 60.0


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


def _fallback_comment(
    current: dict[str, Any],
) -> str:
    concerns = current.get("concerns") or []

    if concerns:
        first = " ".join(str(concerns[0]).split())
        return first[:180]

    trend = str(
        current.get("risk_trend") or "STABLE"
    ).replace("_", " ").lower()

    return f"Monthly food-safety performance is {trend}."


def _persistent_failure(
    history: list[dict[str, Any]],
    current_score: float,
) -> bool:
    scores = [float(current_score)]

    for item in history:
        try:
            scores.append(float(item.get("score", 100)))
        except (TypeError, ValueError):
            continue

    consecutive = 0

    for score in scores:
        if score <= PERSISTENT_SCORE_THRESHOLD:
            consecutive += 1
        else:
            break

    return consecutive >= PERSISTENT_MONTHS


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


def _call_gemini(
    payload: dict[str, Any],
) -> dict[str, Any]:
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

Your job is to analyze official SafeBite monthly audit evidence and
produce a compact public performance assessment.

Rules:
1. Use only the supplied data.
2. Do not invent incidents, evidence, or legal conclusions.
3. A citizen report is negative evidence only when its government status is VERIFIED.
4. The supplied base audit score is an official deterministic baseline.
5. Your recommended score must stay close to that baseline.
6. Public status must be one of: EXCELLENT, GOOD, WATCH, POOR, CRITICAL.
7. Comment must be one short sentence understandable to a citizen.
8. Licence review may be recommended only when there is a persistent pattern across
   multiple monthly assessments; the government authority still makes the decision.

Current official audit:
{json.dumps(payload.get('current'), ensure_ascii=False, default=str)}

Previous monthly assessments:
{json.dumps(payload.get('history'), ensure_ascii=False, default=str)}

Return ONLY JSON with exactly these fields:
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
    except ValueError as exc:
        raise MonthlyAIError("Gemini response was not JSON") from exc

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MonthlyAIError(
            "Gemini response did not contain generated text"
        ) from exc

    return _extract_json(text)


def analyze_monthly_performance(
    current: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    base_score = float(
        current.get("compliance_score", 0)
    )

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
        )

        requested_score = float(
            generated.get("score", base_score)
        )

        score = max(
            0.0,
            min(
                100.0,
                requested_score,
            ),
        )

        score = max(
            base_score - AI_SCORE_GUARDRAIL,
            min(
                base_score + AI_SCORE_GUARDRAIL,
                score,
            ),
        )

        comment = _clean_comment(
            generated.get("comment")
        )

        model_recommendation = bool(
            generated.get(
                "licence_review_recommended",
                False,
            )
        )

    except MonthlyAIError:
        score = base_score
        comment = _fallback_comment(current)
        model_recommendation = False

    status = public_status_from_score(score)

    persistent_failure = _persistent_failure(
        history,
        score,
    )

    licence_review_recommended = bool(
        persistent_failure
        and model_recommendation
    )

    # When the model is unavailable, the deterministic history guardrail
    # still surfaces a review warning after persistent failure.
    if ai_model == "RULE_BASED_FALLBACK" and persistent_failure:
        licence_review_recommended = True

    return {
        "score": round(score, 1),
        "status": status,
        "comment": comment,
        "licence_review_recommended":
            licence_review_recommended,
        "base_audit_score": round(base_score, 1),
        "ai_model": ai_model,
        "persistent_failure": persistent_failure,
    }
