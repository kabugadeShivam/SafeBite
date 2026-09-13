# SafeBite Physical Prototype Hardware

This hardware plan is aligned with the current SafeBite software workflow.

## Complete one-outlet prototype kit

| Component | Qty | Purpose |
|---|---:|---|
| ESP32 DevKit | 1 | Main IoT controller and Wi-Fi gateway |
| DHT22 / AM2302 | 1 | Temperature + humidity monitoring |
| Magnetic reed switch + magnet | 1 | Cold-storage door state |
| ESP32-CAM + OV2640 | 1 | Visual inspection and image capture |
| ESP32-CAM-MB programmer | 1 | Program ESP32-CAM |
| 2.4-inch ILI9341 TFT | 1 | Local item/outlet status display |
| Active buzzer | 1 | Local warning for high-risk conditions |
| 5V 2A USB power supply | 1 | Continuous power |
| Breadboard / prototype PCB | 1 | MVP wiring |
| Dupont jumper wire set | 1 | Connections |
| 4.7k-10k resistors | 1 pack | Sensor pull-up / prototyping |
| USB cables | 2 | ESP32 / ESP32-CAM programming |
| Enclosure | 1 | Protect electronics |
| Mounting hardware | 1 set | Sensor/camera installation |

## Functional blocks

```text
ESP32
  ├── DHT22 → temperature + humidity
  ├── Reed switch → door state
  ├── TFT → local status
  └── Buzzer → local warning

ESP32-CAM
  └── Image → SafeBite visual analysis
```

## Current sensor software contract

The ESP32 sends:

```json
{
  "device_id": "SB-MGM-ESP32-001",
  "temperature": 5.2,
  "humidity": 64.5,
  "door_open": false
}
```

to:

```text
POST /sensors/readings
```

The backend stores the reading and can create an environmental alert. The same contract is used by the simulator, so the real ESP32 replaces the simulator without changing the backend API.

## Suggested ESP32 pins

The current starter firmware uses:

- DHT22 data: GPIO 4
- Reed switch: GPIO 27
- DHT22 VCC: 3.3V
- DHT22 GND: GND
- Reed switch one side: GPIO 27
- Reed switch other side: GND
- Reed input: `INPUT_PULLUP`

The TFT display and buzzer are intentionally kept in the prototype wiring plan so their final pins can be assigned after the exact display board is received.

## Camera role

The camera is used for two software paths:

```text
Product image
    ├── Expiry OCR
    └── Visual/hygiene analysis
```

The government Item Scanner combines these results with the latest outlet storage reading and returns `SAFE`, `CHECK`, or `UNSAFE`.

## SafeBite item check

```text
Food item
   ↓
Camera image
   ↓
Expiry OCR + visual analysis
   ↓
Latest storage evidence
   ↓
Item safety assessment
   ↓
SAFE / CHECK / UNSAFE
```

This is an evidence-based risk assessment, not a laboratory food-safety test. Government officers remain the final authority.

## Important local-network detail

The laptop's `127.0.0.1` address works for the Python simulator because the simulator runs on the same computer as FastAPI. A physical ESP32 cannot use `127.0.0.1` to reach the laptop. Set the firmware server URL to the laptop's LAN IP, for example:

```text
http://192.168.1.20:8000/sensors/readings
```

The laptop and ESP32 must be on the same reachable network, and Windows Firewall must allow inbound TCP traffic to port 8000 when testing over LAN.

## MVP scope

Do not add extra environmental sensors unless the SafeBite risk engine is extended to use their readings. The current risk engine is based on temperature, humidity and door state, while the camera is the visual input for expiry and hygiene analysis.
