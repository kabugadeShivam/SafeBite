"""
SafeBite Risk Engine

Calculates an environmental food-safety risk score from:
- Refrigerator/cold-storage temperature
- Optional humidity
- Door-open state

Humidity is optional so a temperature-only DS18B20 prototype does not
invent a humidity measurement.

Score:
    0  - 39   GREEN
    40 - 69   AMBER
    70 - 89   ORANGE
    90 - 100  RED
"""

from __future__ import annotations

from typing import Any


IDEAL_TEMP_MAX = 5.0
ELEVATED_TEMP_MAX = 8.0
HIGH_TEMP_MAX = 12.0
IDEAL_HUMIDITY_MAX = 70.0
HIGH_HUMIDITY_MAX = 85.0
DOOR_OPEN_LIMIT_SECONDS = 120


def _clamp_score(score: int | float) -> int:
    return max(0, min(100, int(round(score))))


def _severity_from_score(score: int) -> str:
    if score >= 90:
        return "RED"
    if score >= 70:
        return "ORANGE"
    if score >= 40:
        return "AMBER"
    return "GREEN"


def calculate_risk_score(
    temperature: float,
    humidity: float | None,
    door_open: bool,
    door_open_seconds: int | float | None = None,
) -> dict[str, Any]:
    if temperature is None:
        raise ValueError("temperature is required")

    temperature = float(temperature)

    if humidity is not None:
        humidity = float(humidity)
        if humidity < 0 or humidity > 100:
            raise ValueError("humidity must be between 0 and 100")

    if door_open_seconds is not None:
        door_open_seconds = max(0, float(door_open_seconds))

    score = 0
    reasons: list[str] = []

    if temperature <= IDEAL_TEMP_MAX:
        pass
    elif temperature <= ELEVATED_TEMP_MAX:
        score += 25
        reasons.append("Elevated refrigerator temperature detected")
    elif temperature <= HIGH_TEMP_MAX:
        score += 50
        reasons.append("High refrigerator temperature detected")
    else:
        score += 70
        reasons.append("Critical refrigerator temperature detected")

    # Humidity is optional for the DS18B20-only prototype.
    if humidity is not None:
        if humidity <= IDEAL_HUMIDITY_MAX:
            pass
        elif humidity <= HIGH_HUMIDITY_MAX:
            score += 10
            reasons.append("Elevated humidity detected")
        else:
            score += 20
            reasons.append("High humidity detected")

    if door_open:
        if (
            door_open_seconds is not None
            and door_open_seconds >= DOOR_OPEN_LIMIT_SECONDS
        ):
            score += 25
            reasons.append("Refrigerator door has remained open for an extended period")
        else:
            score += 10
            reasons.append("Refrigerator door is open")

    if door_open and temperature > ELEVATED_TEMP_MAX:
        score += 15
        reasons.append("Open door combined with elevated temperature")

    if (
        humidity is not None
        and temperature > HIGH_TEMP_MAX
        and humidity > HIGH_HUMIDITY_MAX
    ):
        score += 10
        reasons.append("High temperature and high humidity detected together")

    score = _clamp_score(score)

    return {
        "risk_score": score,
        "severity": _severity_from_score(score),
        "reasons": reasons,
    }


def calculate_risk(
    temperature: float,
    humidity: float | None,
    door_open: bool,
    door_open_seconds: int | float | None = None,
) -> dict[str, Any]:
    return calculate_risk_score(
        temperature=temperature,
        humidity=humidity,
        door_open=door_open,
        door_open_seconds=door_open_seconds,
    )
