from __future__ import annotations

from typing import Any


def assess_item(
    expiry: dict[str, Any],
    vision: dict[str, Any] | None = None,
    temperature: float | None = None,
    humidity: float | None = None,
    door_open: bool | None = None,
) -> dict[str, Any]:
    status = "SAFE"
    reasons: list[str] = []

    expiry_status = str(expiry.get("status") or "NOT_FOUND").upper()

    if expiry_status == "EXPIRED":
        status = "UNSAFE"
        reasons.append("Expiry date has passed")
    elif expiry_status == "EXPIRES_TODAY":
        status = "CHECK"
        reasons.append("Expiry date is today")
    elif expiry_status != "VALID":
        status = "CHECK"
        reasons.append("Expiry date could not be verified")

    if vision and vision.get("success") is True:
        vision_score = float(vision.get("risk_score") or 0)
        if vision_score >= 70:
            status = "UNSAFE"
            reasons.append("High visual risk detected")
        elif vision_score >= 40 and status == "SAFE":
            status = "CHECK"
            reasons.append("Moderate visual risk detected")

    if temperature is not None:
        temp = float(temperature)
        if temp > 12:
            status = "UNSAFE"
            reasons.append("Storage temperature is critically high")
        elif temp > 8 and status == "SAFE":
            status = "CHECK"
            reasons.append("Storage temperature is elevated")

    if humidity is not None and float(humidity) > 85:
        if status == "SAFE":
            status = "CHECK"
        reasons.append("Storage humidity is high")

    if door_open is True:
        if status == "SAFE":
            status = "CHECK"
        reasons.append("Cold-storage door is open")

    return {
        "status": status,
        "safe": status == "SAFE",
        "reasons": reasons,
    }
