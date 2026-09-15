# SafeBite Physical Prototype Hardware

This hardware plan is aligned with the current SafeBite software workflow.

## Current one-outlet prototype

| Component | Qty | Purpose |
|---|---:|---|
| ESP32 DevKit | 1 | Main IoT controller and Wi-Fi gateway |
| Waterproof DS18B20 probe | 1 | Cold-storage temperature monitoring |
| 4.7k resistor | 1 | DS18B20 data-line pull-up |
| Magnetic reed switch + magnet | 1 | Future refrigerator/cold-storage door state |
| LED + resistor | 1+ | Local prototype status indication |
| ESP32-CAM + OV2640 | 1 | Future visual inspection and image capture |
| 2.4-inch ILI9341 TFT | 1 | Future local item/outlet status display |
| Active buzzer | 1 | Future local warning |
| Breadboard / prototype PCB | 1 | MVP wiring |
| Dupont jumper wire set | 1 | Connections |
| USB cable | 1+ | ESP32 programming/power |

## Current temperature path

```text
Waterproof DS18B20
    ↓
ESP32 GPIO 4
    ↓ Wi-Fi / HTTPS
POST /sensors/readings
    ↓
SafeBite FastAPI
    ↓
PostgreSQL
    ↓
Risk Engine
    ↓
Government Dashboard / Alert
```

## DS18B20 wiring

For the common 3-wire waterproof DS18B20 probe:

- Red: VCC → ESP32 3.3V
- Black: GND → ESP32 GND
- Yellow/White: DATA → ESP32 GPIO 4
- 4.7k resistor: between DATA and 3.3V

Because probe wire colors can vary by manufacturer, verify the connector/wire labels before powering the circuit.

## Current sensor software contract

The temperature-only prototype sends:

```json
{
  "device_id": "SB-MGM-ESP32-001",
  "temperature": 5.2,
  "humidity": null,
  "door_open": false
}
```

to:

```text
POST /sensors/readings
```

The backend stores the temperature and does not invent a humidity reading. Humidity can be added later when a humidity-capable sensor is installed.

## LED prototype

Use an LED only after the temperature reading is confirmed. Suggested mapping:

```text
GREEN  → normal temperature
AMBER  → elevated temperature
RED    → high/critical temperature
```

Each LED should have its own series resistor, typically 220-330 ohms for a standard indicator LED.

## Current firmware

`hardware/esp32_safebite/esp32_safebite.ino` uses:

- DS18B20 data: GPIO 4
- production endpoint: SafeBite Render HTTPS API
- device ID: `SB-MGM-ESP32-001`
- reporting interval: 10 seconds

The firmware uses `OneWire` and `DallasTemperature` libraries.

## Door, camera and additional hardware

The reed switch, ESP32-CAM, TFT and buzzer remain planned extensions. Integrate them one at a time after the DS18B20 path is stable.

## Safety note

This is a prototype monitoring system, not a calibrated food-safety instrument. Sensor readings should be validated against an appropriate reference thermometer before making operational decisions.
