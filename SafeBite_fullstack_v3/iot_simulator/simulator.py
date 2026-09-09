import random
import time
import requests

API_URL = "http://127.0.0.1:8000/sensors/readings"
DEVICE_ID = "SB-MGM-ESP32-001"


def generate_sensor_data():
    mode = random.choices(["NORMAL", "WARNING", "CRITICAL"], weights=[70, 20, 10], k=1)[0]

    if mode == "CRITICAL":
        return {
            "device_id": DEVICE_ID,
            "temperature": round(random.uniform(9, 12), 2),
            "humidity": round(random.uniform(81, 92), 2),
            "door_open": True,
        }

    if mode == "WARNING":
        return {
            "device_id": DEVICE_ID,
            "temperature": round(random.uniform(6.1, 8), 2),
            "humidity": round(random.uniform(70, 80), 2),
            "door_open": random.choice([True, False]),
        }

    return {
        "device_id": DEVICE_ID,
        "temperature": round(random.uniform(3, 6), 2),
        "humidity": round(random.uniform(55, 70), 2),
        "door_open": random.choice([False, False, False, True]),
    }


while True:
    data = generate_sensor_data()
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        print("Sensor Data Sent:")
        print(data)
        print("Server Response:")
        print(response.json())
    except requests.RequestException as exc:
        print("Connection error:", exc)
    except ValueError:
        print("Server returned non-JSON response:", response.text)

    print("-" * 60)
    time.sleep(5)
