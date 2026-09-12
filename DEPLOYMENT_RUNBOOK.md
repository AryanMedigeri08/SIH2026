# Udyam Saathi — Production Deployment & Operational Runbook

**Document Standard:** Document 4, Phase 17 (Deployment Rehearsal & Runbook)  
**System Version:** 2.0.0-production  
**Date:** September 2026  
**Auditor:** Antigravity Autonomous Engineering Subsystem  

---

## 1. System Topology & Prerequisites

### Topology
```text
[ Browser / Mobile Client ]
            │ (HTTP / WebSocket)
            ▼
   [ Reverse Proxy / NGINX ] (Port 80 / 443)
            │
            ├─► /api/v2/* ────► [ FastAPI ASGI (Uvicorn) ] (Port 8000)
            │                          │
            │                          ├─► [ PostgreSQL / Neon Pool ]
            │                          │      (Fallback: Durable SQLite3)
            │                          │
            │                          ├─► [ Immutable DataSnapshots (Disk) ]
            │                          │
            │                          └─► [ Upstream Gov APIs (UDYAM/Antyodaya) ]
            │
            └─► /* ───────────► [ Vite Static SPA Bundle / NGINX ]
```

### Runtime Prerequisites
* **Operating System:** Ubuntu 22.04 LTS, Debian 12, or Windows Server 2022
* **Python Runtime:** Python 3.10.x or 3.11.x
* **Node.js Runtime:** Node.js 18.x or 20.x LTS + npm 9+
* **Database (Primary):** Neon Serverless PostgreSQL or local PostgreSQL 15+
* **Database (Fallback):** SQLite 3.35+ (automatically initialized if `DATABASE_URL` is omitted)
* **Memory / Compute:** Minimum 2 vCPU, 4GB RAM (8GB recommended for production)

---

## 2. Environment Variables & Secret Management

Create a secure `.env` file in the project root based on [`.env.example`](file:///c:/SIH2026/.env.example).

> [!CAUTION]
> **Strict Secret Safeguard:** Secrets must **never** be committed to version control, printed to standard out, returned in API payloads, or exposed in frontend client bundles.

| Environment Variable | Description | Default / Example | Classification |
|---|---|---|---|
| `PORT` | FastAPI backend port | `8000` | Public Config |
| `HOST` | FastAPI bind host | `0.0.0.0` | Public Config |
| `DEBUG` | Debug mode (must be `False` in prod) | `False` | Public Config |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require` | **SECRET** |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase Admin SDK JSON string | Single-line JSON credentials | **SECRET** |
| `GROQ_API_KEY` | Groq AI Cloud synthesis API key | `gsk_...` | **SECRET** |
| `DATA_GOV_IN_API_KEY` | OGD / Mission Antyodaya API key | `579b...` | **SECRET** |
| `ALLOWED_ORIGINS` | CORS explicit allow-list | `http://localhost:5173,https://udyam-saathi.gov.in` | Public Config |

---

## 3. Clean Environment Deployment Steps

### Step 1: Clone & Configure
```bash
git clone https://github.com/AryanMedigeri08/SIH2026.git
cd SIH2026
cp .env.example .env
# Edit .env with production credentials
```

### Step 2: Backend Virtual Environment & Dependencies
```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Database Initialization
The application automatically runs safe, non-destructive schema migrations upon startup.
* If `DATABASE_URL` is provided: Connects via `asyncpg` connection pool (min=1, max=10) and creates tables `users`, `projects`, `feasibility_reports`, and `revoked_sessions`.
* If `DATABASE_URL` is not set: Automatically establishes durable SQLite storage at `backend/app/data/udyam_saathi.sqlite3` with foreign key enforcement (`PRAGMA foreign_keys = ON;`).

### Step 4: Frontend Build
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Start the Backend Server
```bash
# Production mode with multiple workers:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 4. Health Check & Smoke Verification

### Automated Health Endpoint
```bash
curl -i http://localhost:8000/api/v2/health
```
Expected HTTP 200 Response:
```json
{
  "status": "healthy",
  "app_name": "Udyam Saathi REST API",
  "version": "2.0.0",
  "timestamp_utc": "2026-09-12T04:30:00.000Z",
  "database_connected": true,
  "ai_synthesizer_active": true,
  "ml_classifier_loaded": true
}
```

### Smoke Test: Opportunity Intelligence Replay
```bash
curl -X POST http://localhost:8000/api/v2/market-analysis/opportunity \
  -H "Content-Type: application/json" \
  -d '{
    "state": "TELANGANA",
    "district": "MEDAK",
    "village": "Balanagar",
    "business_intent": "dairy",
    "snapshot_id": "SNAP-09D8E7D1C0B3"
  }'
```
Expected verification checks:
* Response HTTP 200 OK
* Response header `X-Correlation-ID` present (e.g., `CID-...`)
* Response header `X-Response-Time-ms` present (< 500ms)
* `composite_score`: `46.0`
* `recommendation`: `"SATURATED_MARKET"`
* `confidence`: `"HIGH"`

---

## 5. Failure Recovery & Degraded Modes

| Failure Scenario | Automatic System Behavior | Operator Action |
|---|---|---|
| **Neon Database Outage** | Switches automatically to durable local SQLite store without crashing active requests | Check Neon console or network connection; restart pool once restored |
| **Data.gov.in / UDYAM 429 / 500** | Retries with exponential backoff (1s, 2s); falls back cleanly to regional baseline amenities and cached snapshots | Ensure API key quota is refreshed; system remains functional in degraded mode |
| **Groq LLM Quota Exhausted** | Drops back cleanly to deterministic rule-based executive synthesis | Synthesizer reports `source: DETERMINISTIC_FALLBACK`; user experiences zero downtime |
| **Invalid Client Coordinates** | Pipeline marks record `UNMAPPED` and bounds within uncertainty stress tiers | No action needed; coordinates are never fabricated |

---

## 6. Rollback Procedures

If an unrecoverable defect is observed following deployment:

1. **Stop Application:**
   ```bash
   kill -9 $(pgrep -f "uvicorn app.main:app")
   ```
2. **Revert Git Release Tag:**
   ```bash
   git checkout tags/v1.9.0-stable
   ```
3. **Rollback Database (if required):**
   Database migrations in `DatabaseManager._init_tables()` are non-destructive (only adding `CREATE TABLE IF NOT EXISTS` or new columns via `ALTER TABLE`). Reversion does not cause data loss.
4. **Restart Previous Stable Version:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
5. **Verify Health:**
   ```bash
   curl http://localhost:8000/api/v2/health
   ```
