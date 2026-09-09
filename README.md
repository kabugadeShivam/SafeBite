# SafeBite v2 — Government Food Safety Monitoring Platform

This version freezes the architecture around the complete government workflow:

**Authenticated Regional Officer → Live/Simulated IoT → Risk Engine → Alert → Evidence → Investigation → Corrective Action → Supervisor Verification → Auditable Record**

## Backend

```powershell
cd C:\SafeBite
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Because the database schema changed, for this prototype delete the old database once:

```powershell
Remove-Item backend\safebite.db -ErrorAction SilentlyContinue
```

Seed demo data:

```powershell
python -m backend.seed_demo
```

Start API:

```powershell
uvicorn backend.main:app --reload
```

Open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

## Demo credentials

- Central Admin: `admin` / `Admin@12345`
- Regional Officer: `officer_nm` / `SafeBite@123`
- Supervisor: `supervisor_nm` / `SafeBite@123`

These are local prototype credentials; change them before any real deployment.

## Simulator

In a second terminal:

```powershell
cd C:\SafeBite
iot_simulator\simulator.py
```

or:

```powershell
python iot_simulator\simulator.py
```

The simulator now sends JSON to the same endpoint that the future ESP32 will use.

## Frontend

Create the React app using Vite, then replace its `src` files with the files in this repository's `frontend/src` directory. Install `react-router-dom`, then run `npm run dev`.

## Blockchain

`blockchain/SafeBiteAudit.sol` is the on-chain audit contract. The backend currently creates a tamper-evident hash chain locally first; the contract is the next integration target for recording the resulting hashes on Hardhat/Ganache. This separation keeps the government workflow testable before wallet/RPC configuration is introduced.
