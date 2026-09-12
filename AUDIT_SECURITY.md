# AUDIT_SECURITY.md — Dependency, Secret & Configuration Security Audit

**Audit Date:** 2026-09-11  
**Auditor:** Antigravity AI Engine (Document 3 Audit Subsystem)  
**Standard:** Document 3, Section 5 (Gate 2 — Dependency and Security Audit)  
**Project:** Udyam Saathi — MSME Village Intelligence, Market Analysis & Opportunity Engine  

---

## 1. Executive Security Summary
| Audit Category | Findings | Risk Level | Status |
|---|---|---|---|
| **Hard-Coded Secrets** | Zero API keys or database credentials found in codebase | NONE | PASS |
| **Secret Storage (.env)** | Present in root, strictly excluded via `.gitignore` | LOW | PASS |
| **CORS Policy** | Restricted to explicit origins (`ALLOWED_ORIGINS`); no wildcard `*` allowed with credentials | LOW | PASS |
| **Credential Masking** | API keys (Data.gov.in, Groq, Neon) excluded from logs and API payloads | NONE | PASS |
| **Error Exposure** | Stack traces intercepted by FastAPI exception handlers | LOW | PASS |
| **Debug Mode in Production** | `DEBUG=True` set in `.env` for local development | MEDIUM | NEEDS_ACTION |

---

## 2. Detailed Findings & Evaluation

### 2.1 Hardcoded Credentials Audit (Critical / High)
* **Scan Target:** `backend/`, `frontend/`, `tests/`, `docs/`.
* **Search Patterns:** Regex scans for AWS secrets, Neon DB connection strings, Data.gov.in UUID tokens (`579b464d...`), Groq tokens (`gsk_...`), Google Translate tokens.
* **Finding:** Zero hardcoded credentials detected in the git-tracked source code.
* **Status:** `PASS`

### 2.2 Environment & Secret Isolation (Gate 2 Requirement)
* **Requirement:** Never place the Data.gov.in API key or Firebase credentials in Git.
* **Verification:**
  * `.gitignore` explicitly isolates:
    ```gitignore
    .env
    .env.local
    .env.*.local
    *.env
    *firebase*.json
    serviceAccountKey.json
    firebase-credentials.json
    ```
* **Status:** `PASS`

### 2.3 CORS & Middleware Configuration
* **Configuration:** Defined in `backend/app/main.py:108-115` using `CORSMiddleware`.
* **Origins:** Sourced dynamically from `settings.CORS_ORIGINS` (`http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`).
* **Evaluation:** Disallows arbitrary wildcard `*` origins while allowing required front-end development ports.
* **Status:** `PASS`

### 2.4 Leakage Prevention in Intelligence Deliverables
* **Requirement:** Data.gov.in API key must never appear in generated opportunity reports, evidence objects, logs, or screenshots.
* **Verification:**
  * `MarketOpportunityReport` exposes `data_lineage` referencing public portal URLs and source IDs (`UDYAM_MSME`, `CENSUS_2011_POPULATION`, `MISSION_ANTYODAYA`, `ODOP_REGISTRY`), omitting query parameter tokens or authentication headers.
* **Status:** `PASS`

### 2.5 Operational Action Required Prior to Production Deployment
1. Set `DEBUG=False` in `.env` for staging/production builds to prevent FastAPI interactive OpenAPI swagger from displaying verbose exception tracebacks.
2. Ensure production environment secrets (Neon DB, Groq, Data.gov.in) are injected via container environment variables or cloud secret managers (e.g., AWS Secrets Manager / Doppler / GitHub Secrets).

---

## 3. Audit Conclusion for Gate 2
* No `CRITICAL` or `HIGH` security vulnerabilities exist in the codebase.
* The single `MEDIUM` finding (`DEBUG=True`) is an intentional local development setting to be toggled before production deployment.
* Gate 2 Result: **PASS**
