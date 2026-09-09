import random
import time

import requests

API_URL = "http://127.0.0.1:8000/sensors/readings"
DEVICE_ID = "SB-MGM-ESP32-001"


def generate_sensor_data():
    dangerous = random.random() < 0.30

    if dangerous:
        return {
            "device_id": DEVICE_ID,
            "temperature": round(random.uniform(9.0, 12.0), 2),
            "humidity": round(random.uniform(80.0, 90.0), 2),
            "door_open": True,
        }

    return {
        "device_id": DEVICE_ID,
        "temperature": round(random.uniform(3.0, 6.0), 2),
        "humidity": round(random.uniform(55.0, 70.0), 2),
        "door_open": random.choice([False, False, False, True]),
    }


while True:
    payload = generate_sensor_data()

    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        print("Sensor Data Sent:")
        print(payload)
        print("Server Response:")
        print(response.json())
    except requests.RequestException as exc:
        print("Request error:", exc)

    print("-" * 60)
    time.sleep(5)
