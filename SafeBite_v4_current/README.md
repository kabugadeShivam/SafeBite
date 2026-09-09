# SafeBite v4

Smart IoT-Based Food Safety and Hygiene Monitoring System with a regional government monitoring portal, AI event interfaces, investigation workflow, evidence hashing and blockchain-ready auditing.

## Core flow

Restaurant / IoT device -> sensor/AI event -> risk engine -> alert -> regional government officer -> investigation -> findings/action -> supervisor verification -> audit chain -> optional EVM blockchain anchor.

## Backend

```powershell
cd C:\SafeBite
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m backend.seed_demo
uvicorn backend.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Frontend

```powershell
cd C:\SafeBite\frontend_app
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo users

- Central Admin: `admin / Admin@12345`
- Regional Officer: `officer_nm / SafeBite@123`
- Supervisor: `supervisor_nm / SafeBite@123`

## Development order

1. Government portal and investigations
2. AI event APIs (OCR + hygiene)
3. Local audit chain
4. Hardhat/Ganache anchoring
5. Real ESP32 + sensors
6. Final integration and testing

Do not treat the project-defined risk score as an official food-safety certification or legal classification.
