"""Explainable SafeBite risk scoring services.

Scores are project-defined monitoring scores, not official regulatory limits.
Higher score = safer monitoring condition.
"""


def calculate_risk_score(temperature: float, humidity: float, door_open: bool):
    score = 100
    reasons = []

    if temperature > 8:
        score -= 40
        reasons.append("High storage temperature")
    elif temperature > 6:
        score -= 20
        reasons.append("Elevated storage temperature")

    if humidity > 80:
        score -= 25
        reasons.append("High humidity")
    elif humidity > 70:
        score -= 10
        reasons.append("Elevated humidity")

    if door_open:
        score -= 10
        reasons.append("Cold-storage door is open")

    score = max(0, min(100, score))

    if score >= 85:
        severity = "GREEN"
    elif score >= 70:
        severity = "AMBER"
    elif score >= 50:
        severity = "ORANGE"
    else:
        severity = "RED"

    return {
        "risk_score": score,
        "severity": severity,
        "reasons": reasons,
    }


def calculate_ai_risk(event_type: str, confidence: float = 1.0):
    """Map a vision/OCR event to a monitoring score.

    Confidence is used as a multiplier so low-confidence detections are
    treated less aggressively. Thresholds remain project-defined.
    """
    confidence = max(0.0, min(1.0, float(confidence)))
    normalized = event_type.strip().upper()

    penalties = {
        "EXPIRED": 80,
        "UNCOVERED_FOOD": 50,
        "GARBAGE_OVERFLOW": 45,
        "PPE_NON_COMPLIANCE": 30,
    }

    base_penalty = penalties.get(normalized, 0)
    penalty = round(base_penalty * confidence)
    score = max(0, 100 - penalty)

    if score >= 85:
        severity = "GREEN"
    elif score >= 70:
        severity = "AMBER"
    elif score >= 50:
        severity = "ORANGE"
    else:
        severity = "RED"

    reason_map = {
        "EXPIRED": "Expired food product detected",
        "UNCOVERED_FOOD": "Uncovered food detected",
        "GARBAGE_OVERFLOW": "Garbage overflow detected",
        "PPE_NON_COMPLIANCE": "PPE non-compliance detected",
    }

    reasons = [reason_map[normalized]] if normalized in reason_map else []

    return {
        "risk_score": score,
        "severity": severity,
        "reasons": reasons,
    }
