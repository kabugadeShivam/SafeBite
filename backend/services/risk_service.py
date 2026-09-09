"""
SafeBite Risk Engine

Calculates an environmental food-safety risk score from:
- Refrigerator/cold-storage temperature
- Humidity
- Door-open state

Score:
    0  - 39   GREEN
    40 - 69   AMBER
    70 - 89   ORANGE
    90 - 100  RED
"""

from __future__ import annotations

from typing import Any


# ============================================================
# THRESHOLDS
# ============================================================

IDEAL_TEMP_MAX = 5.0
ELEVATED_TEMP_MAX = 8.0
HIGH_TEMP_MAX = 12.0

IDEAL_HUMIDITY_MAX = 70.0
HIGH_HUMIDITY_MAX = 85.0

DOOR_OPEN_LIMIT_SECONDS = 120


# ============================================================
# HELPERS
# ============================================================

def _clamp_score(score: int | float) -> int:
    """Keep risk score between 0 and 100."""
    return max(0, min(100, int(round(score))))


def _severity_from_score(score: int) -> str:
    """Convert numerical score into a severity level."""
    if score >= 90:
        return "RED"

    if score >= 70:
        return "ORANGE"

    if score >= 40:
        return "AMBER"

    return "GREEN"


# ============================================================
# MAIN RISK CALCULATION
# ============================================================

def calculate_risk_score(
    temperature: float,
    humidity: float,
    door_open: bool,
    door_open_seconds: int | float | None = None,
) -> dict[str, Any]:
    """
    Calculate environmental food-safety risk.

    Parameters
    ----------
    temperature:
        Refrigerator/cold-storage temperature in Celsius.

    humidity:
        Relative humidity percentage.

    door_open:
        True when the refrigerator/storage door is open.

    door_open_seconds:
        Optional duration for which the door has been open.

    Returns
    -------
    dict
        {
            "risk_score": int,
            "severity": str,
            "reasons": list[str]
        }
    """

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if temperature is None:
        raise ValueError("temperature is required")

    if humidity is None:
        raise ValueError("humidity is required")

    temperature = float(temperature)
    humidity = float(humidity)

    if humidity < 0 or humidity > 100:
        raise ValueError(
            "humidity must be between 0 and 100"
        )

    if door_open_seconds is not None:
        door_open_seconds = max(
            0,
            float(door_open_seconds)
        )

    score = 0
    reasons: list[str] = []

    # ========================================================
    # TEMPERATURE
    # ========================================================

    if temperature <= IDEAL_TEMP_MAX:
        # Normal refrigeration range.
        score += 0

    elif temperature <= ELEVATED_TEMP_MAX:
        score += 25
        reasons.append(
            "Elevated refrigerator temperature detected"
        )

    elif temperature <= HIGH_TEMP_MAX:
        score += 50
        reasons.append(
            "High refrigerator temperature detected"
        )

    else:
        score += 70
        reasons.append(
            "Critical refrigerator temperature detected"
        )

    # ========================================================
    # HUMIDITY
    # ========================================================

    if humidity <= IDEAL_HUMIDITY_MAX:
        score += 0

    elif humidity <= HIGH_HUMIDITY_MAX:
        score += 10
        reasons.append(
            "Elevated humidity detected"
        )

    else:
        score += 20
        reasons.append(
            "High humidity detected"
        )

    # ========================================================
    # DOOR
    # ========================================================

    if door_open:

        if (
            door_open_seconds is not None
            and door_open_seconds >= DOOR_OPEN_LIMIT_SECONDS
        ):
            score += 25
            reasons.append(
                "Refrigerator door has remained open "
                "for an extended period"
            )

        else:
            score += 10
            reasons.append(
                "Refrigerator door is open"
            )

    # ========================================================
    # COMBINATION RISK
    # ========================================================

    # Open door + elevated temperature is more significant
    # than either signal alone.
    if door_open and temperature > ELEVATED_TEMP_MAX:
        score += 15
        reasons.append(
            "Open door combined with elevated temperature"
        )

    # Very high temperature + high humidity is another
    # combined environmental risk.
    if (
        temperature > HIGH_TEMP_MAX
        and humidity > HIGH_HUMIDITY_MAX
    ):
        score += 10
        reasons.append(
            "High temperature and high humidity "
            "detected together"
        )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    score = _clamp_score(score)
    severity = _severity_from_score(score)

    # A genuinely normal reading should explicitly return
    # an empty reason list and a low score.
    return {
        "risk_score": score,
        "severity": severity,
        "reasons": reasons,
    }


# ============================================================
# SIMPLE COMPATIBILITY ALIAS
# ============================================================

def calculate_risk(
    temperature: float,
    humidity: float,
    door_open: bool,
    door_open_seconds: int | float | None = None,
) -> dict[str, Any]:
    """
    Backward-compatible alias.

    Allows other SafeBite modules to call calculate_risk()
    without maintaining two implementations.
    """

    return calculate_risk_score(
        temperature=temperature,
        humidity=humidity,
        door_open=door_open,
        door_open_seconds=door_open_seconds,
    )