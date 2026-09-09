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

    score = max(0, score)

    if score < 40:
        severity = "RED"
    elif score < 60:
        severity = "ORANGE"
    elif score < 80:
        severity = "AMBER"
    else:
        severity = "GREEN"

    return {
        "risk_score": score,
        "severity": severity,
        "reasons": reasons,
    }
