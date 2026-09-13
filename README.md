# SafeBite — AI-Assisted Food Safety Governance Platform

SafeBite combines **IoT monitoring, computer vision/OCR, citizen reporting, monthly AI assessment, government investigation, and tamper-evident audit records**.

The design principle is simple:

> **AI detects and prioritizes. Officers physically verify and decide. Blockchain preserves the audit trail.**

## Core workflow

```text
IoT sensors / AI vision / Citizen reports
                ↓
             Evidence
                ↓
          Risk / Alerting
                ↓
       Government Action Queue
                ↓
        Physical Investigation
                ↓
       Corrective Action
                ↓
      Supervisor Verification
                ↓
       Tamper-evident Audit
```

### Monthly automated workflow

```text
Official audit data
+ verified citizen evidence
+ IoT/AI findings
+ investigation outcomes
+ previous monthly scores
                ↓
        Monthly AI analysis
                ↓
       Score + public status
         + short comment
                ↓
      Appreciation / Warning
                ↓
          Email / SMS
```

Persistent low monthly scores trigger **LICENCE_REVIEW_RECOMMENDED** for government review. SafeBite does not automatically cancel a licence.

## Backend setup

```powershell
cd C:\SafeBite

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1

pip install -r backend\requirements.txt
```

The backend dependencies include FastAPI, SQLAlchemy, requests, NumPy, OpenCV, Pillow and pytesseract.

### OCR requirement on Windows

Install the **Tesseract OCR executable** separately. SafeBite looks for `tesseract.exe` on PATH or at common Windows installation paths. You can also set:

```text
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Environment variables

Copy `.env.example` to `.env` and fill only the services you use.

```powershell
Copy-Item .env.example .env
```

Important variables include:

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
TESSERACT_CMD=

SAFE_BITE_MONTHLY_AUTO_RUN=true
SAFE_BITE_MONTHLY_RUN_DAY=1
SAFE_BITE_MONTHLY_RUN_HOUR_UTC=2
SAFE_BITE_MONTHLY_CATCH_UP_DAYS=7

SAFEBITE_PERSISTENT_MONTHS=3
SAFEBITE_PERSISTENT_SCORE_THRESHOLD=60
```

Email and SMS settings are optional. Leave them blank during local development; the notification service will report `NOT_CONFIGURED` rather than crashing the monthly run.

## Demo database

For a fresh prototype database:

```powershell
Remove-Item backend\safebite.db -ErrorAction SilentlyContinue
python -m backend.seed_demo
```

Demo accounts:

```text
Central Admin: admin / Admin@12345
Regional Officer: officer_nm / SafeBite@123
Supervisor: supervisor_nm / SafeBite@123
```

These are prototype credentials and must be changed for any real deployment.

## Start the API

```powershell
uvicorn backend.main:app --reload
```

Useful pages:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

## Main API capabilities

```text
POST /sensors/readings
POST /ai/expiry
POST /ai/hygiene
POST /ai/item-safety
GET  /government/auditor/regional
GET  /government/action-queue
GET  /government/command-center
GET  /government/monthly-notices
POST /government/monthly-notices/generate
GET  /public/outlets/{registration_id}
POST /public/reports
POST /government/citizen-reports/{report_id}/review
```

### Item safety scanner

`POST /ai/item-safety` combines:

- expiry OCR
- available hygiene-vision findings
- the latest outlet storage reading

and returns:

```text
SAFE
CHECK
UNSAFE
```

This is an evidence-based risk assessment, not a laboratory test. Government officers remain the final authority.

## Simulator

The repository contains an IoT simulator that sends the same JSON contract the future ESP32 will use:

```powershell
cd C:\SafeBite
python iot_simulator\simulator.py
```

The demo device is:

```text
SB-MGM-ESP32-001
```

The current payload is:

```json
{
  "device_id": "SB-MGM-ESP32-001",
  "temperature": 4.5,
  "humidity": 65,
  "door_open": false
}
```

## Frontend

```powershell
cd C:\SafeBite\frontend
npm install
npm run dev
```

Government views include:

```text
Overview
Command Center
Action Queue
Item Scanner
Monthly Notices
Alerts
Investigations
Establishments
Reports
Audit History
```

Public views include an outlet status page, citizen reporting, and report tracking.

## Monthly AI behaviour

The monthly AI analyst uses the deterministic regional audit score as the baseline and keeps the AI score within a configured guardrail. When the external AI service is unavailable, SafeBite falls back to the official audit score and a deterministic explanation.

Persistent failure is evaluated deterministically from the current assessment plus previous monthly assessments, avoiding an LLM-made legal decision.

## Hardware handoff

The prototype hardware is documented under `hardware/`.

Core kit:

```text
ESP32 DevKit
DHT22 / AM2302
Magnetic reed switch
ESP32-CAM + OV2640
2.4" TFT display
Buzzer
5V power supply
Breadboard / wiring / enclosure
```

The ESP32 sends temperature, humidity and door state to `/sensors/readings`. The camera provides visual input for expiry and hygiene analysis.

## Regression tests

Run the software-only checks from the repository root:

```powershell
python backend\test_core.py
python backend\test_monthly_ai.py
```

These cover route registration, item-safety rules, monthly AI fallback, and persistent-failure detection.

## Blockchain

SafeBite maintains a tamper-evident local audit chain first. Blockchain transaction recording is layered on top of that audit record so the government workflow remains testable even when the local blockchain/RPC service is not running.

## Security notes

- `.env`, databases, uploads and Node build artifacts are excluded by `.gitignore`.
- Never commit real API keys or private keys.
- Replace demo passwords before deployment.
- AI recommendations are advisory; official decisions remain with authorised government officers.
