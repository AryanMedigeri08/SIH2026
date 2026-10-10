# Role-based workflow handoff (2026-10-10)

Branch: `Refactor-wizard-aryan`. Implementation commit: `595ae82` (pushed).

## Implemented

- Firebase-authenticated, Neon-backed roles: entrepreneur, banker, government, superadmin. Public registration remains entrepreneur-only; the login role defaults to entrepreneur.
- User-facing staff IDs `Gov@udyam`, `SuperAdmin@udyam`, and `<village>@udyam` map internally to Firebase-valid `@udyam.example.com` identities. The user-requested temporary password is read from ignored `STAFF_INITIAL_PASSWORD`, never committed.
- Live government and SuperAdmin accounts provisioned and verified against Firebase and Neon. Their role-gated API access and logout token rejection passed.
- Village DPR submission, once a *live exact-village bank branch* is confirmed by the amenities API, creates/reuses one banker per village. Banker Overview, scrutiny, application status, and entrepreneur/banker messages are persisted in Neon; DPR content remains in the existing project row to avoid duplication.
- Government dashboard separates potential scheme eligibility from actual recorded reimbursements and has an administrative scheme catalog. SuperAdmin can provision staff and inspect users, enterprises, applications, messages, and activity.
- Staff routes have client role guards; backend ownership/role checks are authoritative. Previously unauthenticated report-DPR access is now denied.

## Verification performed

- `python -m pytest -q tests/test_roles.py tests/test_business_management.py tests/test_passkeys.py`: **23 passed**.
- `node --test tests/roles.test.mjs`: **2 passed**.
- `npm run build`: **passed**. Both backend and frontend development servers started. Direct public/staff URLs responded, unauthenticated staff/DPR APIs returned 401, and browser smoke checks confirmed the role selector and `/banker` redirect to `/login`.
- `python -m scripts.check_live_roles` from `backend/`: **passed** for government and SuperAdmin Firebase sign-in, Neon role, API access denial, and post-logout rejection.
- `python -m pytest -q tests --ignore=tests/test_phase6.py --tb=short`: **268 passed, 26 failed**. Failures are in voice/opportunity/audit tests and API-dependent mocks, while the new role/persistence suites pass. These modules were not changed by the role implementation; a clean-baseline run was not performed, so their prior status is unconfirmed. A raw `python -m pytest -q` additionally fails collection in `misc/scratch/test_opportunity_engine_medak.py` and `tests/test_phase6.py` (unsigned test-token assumption). Do not report the full suite as green.

## Remaining / needs a decision

1. **Live village-bank verification:** The configured Data.gov.in amenities request for Alandi/Pune refused the connection in this environment. No bank was provisioned or DPR transmitted for an unverified village. End-to-end live banker creation and handoff needs a working village-amenities source, or an explicitly approved, auditable administrator verification path. The SQLite/API tests cover the successful path with a mocked verified response.
2. **Shared credential risk:** The user explicitly selected `081020` for temporary staff passwords. It is weak and shared. Replace with unique credentials, forced rotation, and MFA before any real customer DPR data is used.
3. **Scheme catalog:** New government schemes are recorded but intentionally do not change the existing eligibility or financial engines without a validated ruleset. Adding a scheme to DPR calculations is a separate rules-integration task.
4. **Localization and admin operations:** New staff pages expose the language selector, but their dashboard copy is still largely English. SuperAdmin has oversight and staff provisioning, not disable/delete/role-reassignment controls. Clarify desired scope before extending these privileged operations.

Do not change the shared password in Git. Secrets reside only in ignored local environment files.
