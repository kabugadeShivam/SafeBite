# SafeBite Physical Prototype Hardware

This hardware plan is aligned with the current SafeBite IoT API and database model.

## Minimum required kit

| Component | Qty | Purpose | SafeBite field / function |
|---|---:|---|---|
| ESP32 DevKit (Wi-Fi) | 1 | IoT controller and network gateway | `device_id` |
| DHT22 / AM2302 temperature-humidity sensor | 1 | Measure storage temperature and relative humidity | `temperature`, `humidity` |
| Magnetic reed switch + magnet | 1 | Detect refrigerator/cold-storage door state | `door_open` |
| 5V USB power supply | 1 | Power the ESP32 continuously | Power |
| Breadboard or screw-terminal/prototype board | 1 | Mount/connect components during MVP | Wiring |
| Dupont jumper wires | 1 set | ESP32-to-sensor connections | Wiring |

## Recommended physical layout

- Place the ESP32 outside the refrigerator/cold-storage enclosure where Wi-Fi is reliable.
- Place the DHT22 sensor inside the monitored storage area, away from the heater/compressor outlet and direct water droplets.
- Mount the reed switch and magnet on the refrigerator/cold-storage door so the digital input changes when the door opens.
- Keep the ESP32 powered continuously from a stable 5V USB supply.

## Suggested ESP32 pins

- DHT22 data: GPIO 4
- Reed switch: GPIO 27
- DHT22 VCC: 3.3V
- DHT22 GND: GND
- Reed switch one side: GPIO 27
- Reed switch other side: GND
- Use `INPUT_PULLUP` for the reed-switch input.

## Data flow

```text
DHT22 + Reed Switch
        |
        v
      ESP32
        |
        | Wi-Fi / HTTP JSON
        v
POST /sensors/readings
        |
        v
SafeBite Risk Engine
        |
        +--> Sensor Reading
        +--> Environmental Alert
        +--> Officer Action Queue
```

## Device identity

The current demo already defines this device:

```text
Device ID:   SB-MGM-ESP32-001
Outlet:      SB-MGM-001 — MGM College Canteen
Device type: ESP32
```

The simulator uses this exact device ID, so the first physical board can replace the simulator without changing the backend contract.

## Payload sent by the real ESP32

```json
{
  "device_id": "SB-MGM-ESP32-001",
  "temperature": 5.2,
  "humidity": 64.5,
  "door_open": false
}
```

## Important local-network detail

The laptop's `127.0.0.1` address works for the Python simulator because the simulator runs on the same computer as FastAPI. A physical ESP32 cannot use `127.0.0.1` to reach the laptop. Set the firmware's server URL to the laptop's LAN IP, for example:

```text
http://192.168.1.20:8000/sensors/readings
```

The laptop and ESP32 must be on the same reachable network, and Windows Firewall must allow inbound TCP traffic to port 8000 when testing over LAN.

## MVP scope

Do not add gas, flame, camera, load-cell, GPS, or other sensors yet. The current SafeBite risk engine is explicitly based on temperature, humidity, and door state. Additional sensors should be introduced only when the backend risk model is extended to use their data.
