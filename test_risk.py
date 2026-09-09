from backend.services.risk_service import calculate_risk_score


result = calculate_risk_score(
    temperature=5.94,
    humidity=61.79,
    door_open=True
)

print(result)