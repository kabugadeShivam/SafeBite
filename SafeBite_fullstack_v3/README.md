# SafeBite v3 — Integrated Government Food Safety Platform

## Core workflow
Restaurant/IoT → FastAPI → risk engine → alert → regional government portal → investigation → evidence → corrective action → supervisor verification → tamper-evident audit chain → blockchain-ready smart contract.

## Demo accounts
- Central Admin: `admin` / `Admin@12345`
- Regional Officer: `officer_nm` / `SafeBite@123`
- Supervisor: `supervisor_nm` / `SafeBite@123`

## Backend
```powershell
cd C:\SafeBite
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m backend.seed_demo
uvicorn backend.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## Frontend
```powershell
cd C:\SafeBite\frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

## IoT simulator
```powershell
cd C:\SafeBite
.venv\Scripts\Activate.ps1
python iot_simulator\simulator.py
```

The simulator uses the same JSON contract that the eventual ESP32 can use. Replace the simulator with the physical device later without changing the government portal workflow.

## Production notes
- Set `SAFEBITE_JWT_SECRET` to a strong secret.
- Use HTTPS, secure secrets, proper identity infrastructure and a production database.
- The current audit layer is a tamper-evident local hash chain. Deploy `blockchain/SafeBiteAudit.sol` to Hardhat/Ganache or another authorized EVM network before describing external blockchain storage as live.
