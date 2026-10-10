"""Role-gated bank handoff, staff administration, and government oversight."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
import uuid
import asyncio
import shutil
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.core.amenities_client import lookup_village_bank_branch
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.firebase_admin_client import firebase_auth
from app.core import role_store
from app.core.staff_identity import firebase_staff_email
from app.database import db_manager

logger = logging.getLogger("udyam_saathi.roles")
router = APIRouter(prefix="/roles", tags=["Role-based workflows"])
_process_started = time.monotonic()


def require_roles(*roles: str):
    async def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in roles:
            raise HTTPException(403, "Your account does not have access to this resource.")
        return user
    return dependency


def _slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:38]
    return slug or "village-" + hashlib.sha256(value.encode()).hexdigest()[:8]


def _staff_password() -> str:
    password = settings.STAFF_INITIAL_PASSWORD
    if len(password) < 6:
        raise HTTPException(503, "Staff credential provisioning is not configured.")
    return password


async def _create_staff_account(email: str, role: str, name: str,
                                state: str | None = None, district: str | None = None,
                                village: str | None = None) -> dict:
    """Never promote an existing Firebase identity just because an email matches."""
    password = _staff_password()
    auth_email = firebase_staff_email(email)
    try:
        existing = await run_in_threadpool(firebase_auth.get_user_by_email, auth_email)
    except firebase_auth.UserNotFoundError:
        existing = None
    if existing:
        assigned = await role_store.get_role(existing.uid)
        if assigned["role"] != role:
            raise HTTPException(409, "Email belongs to another account; no role was changed.")
        if role == "banker" and (assigned.get("state_key"), assigned.get("district_key"), assigned.get("village_key")) != (
            role_store.location_key(state), role_store.location_key(district), role_store.location_key(village)
        ):
            raise HTTPException(409, "Village credential alias already belongs to another location.")
        return {"uid": existing.uid, "email": email, "created": False}
    try:
        record = await run_in_threadpool(firebase_auth.create_user, email=auth_email, password=password,
                                         display_name=name, email_verified=True)
    except firebase_auth.EmailAlreadyExistsError:
        # A concurrent request may have created this village identity after
        # our first lookup. Wait briefly for its relational role row.
        for _ in range(5):
            existing = await run_in_threadpool(firebase_auth.get_user_by_email, auth_email)
            assigned = await role_store.get_role(existing.uid)
            if assigned["role"] == role and (role != "banker" or (
                assigned.get("state_key"), assigned.get("district_key"), assigned.get("village_key")
            ) == (role_store.location_key(state), role_store.location_key(district), role_store.location_key(village))):
                return {"uid": existing.uid, "email": email, "created": False}
            await asyncio.sleep(0.1)
        raise HTTPException(409, "Staff identity was created concurrently but its role could not be verified.")
    try:
        await db_manager.upsert_user(record.uid, auth_email, name, auth_provider="password")
        await role_store.assign_role(record.uid, role, state, district, village)
        await role_store.record_activity(record.uid, "staff_account_created", role)
    except Exception:
        # A Firebase-only staff identity must not be left usable after DB failure.
        try:
            await run_in_threadpool(firebase_auth.delete_user, record.uid)
        except Exception:
            logger.exception("Could not roll back Firebase staff account %s", record.uid)
        try:
            await db_manager.delete_user(record.uid)
        except Exception:
            logger.exception("Could not roll back staff profile row %s", record.uid)
        raise
    return {"uid": record.uid, "email": email, "created": True}


async def _banker_for_project(project: dict) -> dict:
    state, district, village = (project.get(key) or "" for key in ("state_name", "district_name", "village_name"))
    if not all((state, district, village)):
        raise HTTPException(400, "Project has no complete village location.")
    bank = await _bank_availability(state, district, village)
    if not bank["verified"]:
        raise HTTPException(503, "Village bank availability has not been verified. Request administrator verification before sending.")
    if not bank["available"]:
        raise HTTPException(409, "No village bank branch is verified for this location.")
    existing = await role_store.find_banker(state, district, village)
    if existing:
        return {"uid": existing["user_id"], "created": False}
    alias = f"{_slug(village)}@udyam"
    try:
        return await _create_staff_account(alias, "banker", f"{village} Banker", state, district, village)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        # Same village name in another district must not share an identity.
        existing = await role_store.find_banker(state, district, village)
        if existing:
            return {"uid": existing["user_id"], "created": False}
        alias = f"{_slug(village)}-{_slug(district)}@udyam"
        return await _create_staff_account(alias, "banker", f"{village} Banker", state, district, village)


async def _bank_availability(state: str, district: str, village: str) -> dict:
    """Use durable admin evidence or an existing village banker before the external feed."""
    if not all((state, district, village)):
        return {"available": False, "verified": False, "source": "missing_location", "village": village}
    manual = await role_store.bank_verification(state, district, village)
    if manual:
        return {"available": bool(manual["available"]), "verified": True,
                "source": "admin_verified", "village": village}
    if await role_store.find_banker(state, district, village):
        return {"available": True, "verified": True,
                "source": "provisioned_village_banker", "village": village}
    return await run_in_threadpool(lookup_village_bank_branch, state, district, village)


async def _owned_project(project_id: str, uid: str) -> dict:
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(404, "Enterprise not found.")
    if project.get("user_id") != uid:
        raise HTTPException(403, "Enterprise does not belong to this account.")
    return project


async def _member_application(application_id: str, user: AuthenticatedUser) -> dict:
    application = await role_store.get_application(application_id)
    if not application:
        raise HTTPException(404, "Bank application not found.")
    if user.uid not in (application["entrepreneur_uid"], application["banker_uid"]):
        raise HTTPException(403, "This bank application belongs to another account.")
    expected_role = "banker" if user.uid == application["banker_uid"] else "entrepreneur"
    if user.role != expected_role:
        raise HTTPException(403, "Role does not match this application.")
    return application


class SubmitApplication(BaseModel):
    project_id: str


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class StatusIn(BaseModel):
    status: Literal["under_review", "needs_information", "approved", "declined"]


class StaffIn(BaseModel):
    email: str
    name: str = Field(min_length=2, max_length=120)
    role: Literal["banker", "government"]
    state_name: str | None = None
    district_name: str | None = None
    village_name: str | None = None


class SchemeIn(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=2000)
    administering_body: str | None = Field(default=None, max_length=150)
    benefit_amount: float | None = Field(default=None, ge=0)


class DisbursementIn(BaseModel):
    scheme_name: str = Field(min_length=3, max_length=150)
    beneficiary_uid: str
    amount: float = Field(gt=0)


class BankVerificationIn(BaseModel):
    state_name: str = Field(min_length=2, max_length=120)
    district_name: str = Field(min_length=2, max_length=120)
    village_name: str = Field(min_length=2, max_length=120)
    available: bool
    evidence: str = Field(min_length=8, max_length=500)


@router.get("/me")
async def my_role(user: AuthenticatedUser = Depends(get_current_user)):
    return {"role": user.role, "state_key": user.state_key,
            "district_key": user.district_key, "village_key": user.village_key}


@router.get("/bank-availability/{project_id}")
async def bank_availability(project_id: str, user: AuthenticatedUser = Depends(require_roles("entrepreneur"))):
    project = await _owned_project(project_id, user.uid)
    state, district, village = (project.get(key) or "" for key in ("state_name", "district_name", "village_name"))
    return await _bank_availability(state, district, village)


@router.post("/bank-verification-requests/{project_id}")
async def request_bank_verification(project_id: str, user: AuthenticatedUser = Depends(require_roles("entrepreneur"))):
    project = await _owned_project(project_id, user.uid)
    state, district, village = (project.get(key) or "" for key in ("state_name", "district_name", "village_name"))
    if not all((state, district, village)):
        raise HTTPException(400, "Complete your enterprise location first.")
    latest = await role_store.fetch_one(
        "SELECT created_at FROM activity_events WHERE actor_uid=? AND action='bank_verification_requested' "
        "AND subject_id=? ORDER BY created_at DESC LIMIT 1", user.uid, project_id,
    )
    if latest:
        previous = latest["created_at"]
        if isinstance(previous, str):
            previous = datetime.fromisoformat(previous)
        if (datetime.now(timezone.utc) - previous).total_seconds() < 86400:
            return {"requested": True, "already_requested": True}
    await role_store.record_activity(user.uid, "bank_verification_requested", project_id)
    return {"requested": True, "already_requested": False}


@router.get("/admin/bank-verification-requests")
async def admin_bank_verification_requests(user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    events = await role_store.fetch_all(
        "SELECT subject_id,MAX(created_at) AS requested_at FROM activity_events "
        "WHERE action='bank_verification_requested' GROUP BY subject_id ORDER BY requested_at DESC LIMIT 100"
    )
    result = []
    for event in events:
        project = await db_manager.get_project(event["subject_id"])
        if project:
            state, district, village = (project.get(key) or "" for key in ("state_name", "district_name", "village_name"))
            manual = await role_store.bank_verification(state, district, village)
            banker = await role_store.find_banker(state, district, village) if not manual else None
            result.append({"project_id": event["subject_id"], "business_name": project.get("business_name"),
                           "state_name": state, "district_name": district, "village_name": village,
                           "requested_at": event["requested_at"],
                           "verification": {"available": bool(manual["available"]) if manual else bool(banker),
                                            "verified": bool(manual or banker),
                                            "source": "admin_verified" if manual else "provisioned_village_banker" if banker else "pending"}})
    return result


@router.post("/admin/bank-verifications")
async def admin_save_bank_verification(payload: BankVerificationIn,
                                       user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    await role_store.save_bank_verification(payload.state_name, payload.district_name, payload.village_name,
                                            payload.available, payload.evidence, user.uid)
    await role_store.record_activity(user.uid, "bank_branch_verified", payload.village_name)
    return await _bank_availability(payload.state_name, payload.district_name, payload.village_name)


@router.post("/applications")
async def send_to_banker(payload: SubmitApplication, user: AuthenticatedUser = Depends(require_roles("entrepreneur"))):
    project = await _owned_project(payload.project_id, user.uid)
    if not (project.get("analysis_result") or {}).get("dpr"):
        raise HTTPException(409, "Generate the project's DPR before sending it to a banker.")
    banker = await _banker_for_project(project)
    application = await role_store.submit_application(payload.project_id, user.uid, banker["uid"])
    await role_store.record_activity(user.uid, "dpr_submitted", application["application_id"])
    return application


@router.get("/applications")
async def my_applications(user: AuthenticatedUser = Depends(require_roles("entrepreneur", "banker"))):
    return await role_store.list_applications(user.uid, user.role)


@router.get("/applications/{application_id}")
async def application_detail(application_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    application = await _member_application(application_id, user)
    project = await db_manager.get_project(application["project_id"])
    if not project:
        raise HTTPException(404, "Submitted enterprise is unavailable.")
    return {"application": application, "project": project}


@router.patch("/applications/{application_id}/status")
async def set_application_status(application_id: str, payload: StatusIn,
                                 user: AuthenticatedUser = Depends(require_roles("banker"))):
    application = await _member_application(application_id, user)
    await role_store.execute("UPDATE bank_applications SET status=? WHERE application_id=?", payload.status, application_id)
    await role_store.record_activity(user.uid, "application_" + payload.status, application_id)
    return {"application_id": application_id, "status": payload.status}


@router.get("/applications/{application_id}/messages")
async def get_messages(application_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    await _member_application(application_id, user)
    return await role_store.list_messages(application_id)


@router.post("/applications/{application_id}/messages")
async def post_message(application_id: str, payload: MessageIn,
                       user: AuthenticatedUser = Depends(get_current_user)):
    application = await _member_application(application_id, user)
    if not payload.body.strip():
        raise HTTPException(400, "Message cannot be blank.")
    recipient = application["banker_uid"] if user.role == "entrepreneur" else application["entrepreneur_uid"]
    message = await role_store.add_message(application_id, user.uid, recipient, payload.body.strip())
    await role_store.record_activity(user.uid, "message_sent", application_id)
    return message


@router.post("/staff")
async def create_staff(payload: StaffIn, user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    if payload.role == "banker" and not all((payload.state_name, payload.district_name, payload.village_name)):
        raise HTTPException(400, "Banker location requires state, district, and village.")
    result = await _create_staff_account(payload.email.strip().lower(), payload.role, payload.name.strip(),
                                         payload.state_name, payload.district_name, payload.village_name)
    await role_store.record_activity(user.uid, "staff_provisioned", result["uid"])
    return result


@router.get("/admin/users")
async def admin_users(user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    return await role_store.fetch_all(
        "SELECT u.firebase_uid,u.email,u.name,u.phone,r.role,r.state_key,r.district_key,r.village_key "
        "FROM users u LEFT JOIN user_roles r ON r.user_id=u.firebase_uid ORDER BY u.created_at DESC LIMIT 200"
    )


@router.get("/admin/system-status")
async def admin_system_status(user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    """A read-only operational snapshot; never return connection strings or secrets."""
    engine = "postgresql" if db_manager.pool else "sqlite" if db_manager.sqlite else "unavailable"
    started = time.monotonic()
    try:
        await asyncio.wait_for(role_store.fetch_one("SELECT 1 AS ok"), timeout=3.0)
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    try:
        disk_free_mb = round(shutil.disk_usage(settings.DATA_DIR).free / (1024 * 1024))
    except OSError:
        disk_free_mb = None
    return {
        "api": "operational",
        "uptime_seconds": round(time.monotonic() - _process_started),
        "database": {"engine": engine, "status": db_status,
                     "latency_ms": round((time.monotonic() - started) * 1000),
                     "fallback_active": bool(settings.DATABASE_URL and engine == "sqlite")},
        "authentication": {"provider": "firebase", "configured": bool(
            settings.FIREBASE_SERVICE_ACCOUNT_JSON or settings.FIREBASE_SERVICE_ACCOUNT_PATH),
            "connectivity": "not_tested"},
        "bank_data": {"external_lookup": "best_effort", "admin_verification": "enabled"},
        "services": {
            "ml_model_file_present": settings.MODEL_FILE.is_file(),
            "llm_configured": bool(settings.GROQ_API_KEY or settings.GROQ_CHAT_KEY or settings.GROQ_API_KEY_LLM or settings.SARVAM_API_KEY),
            "speech_configured": bool(settings.BHASHINI_API_KEY and settings.BHASHINI_USER_ID),
            "remote_connectivity": "not_tested",
        },
        "disk_free_mb": disk_free_mb,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/admin/activity")
async def admin_activity(user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    return await role_store.fetch_all(
        "SELECT event_id,actor_uid,action,subject_id,created_at FROM activity_events ORDER BY created_at DESC LIMIT 200"
    )


@router.get("/admin/applications")
async def admin_applications(user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    return await role_store.fetch_all(
        "SELECT application_id,project_id,entrepreneur_uid,banker_uid,status,submitted_at "
        "FROM bank_applications ORDER BY submitted_at DESC LIMIT 200"
    )


@router.get("/admin/users/{uid}/projects")
async def admin_user_projects(uid: str, user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    if not await db_manager.get_user(uid):
        raise HTTPException(404, "User not found.")
    return await db_manager.list_projects(uid)


@router.get("/admin/applications/{application_id}")
async def admin_application_detail(application_id: str,
                                   user: AuthenticatedUser = Depends(require_roles("superadmin"))):
    application = await role_store.get_application(application_id)
    if not application:
        raise HTTPException(404, "Bank application not found.")
    project = await db_manager.get_project(application["project_id"])
    return {"application": application, "project": project,
            "messages": await role_store.list_messages(application_id)}


@router.get("/government/summary")
async def government_summary(user: AuthenticatedUser = Depends(require_roles("government", "superadmin"))):
    # Reimbursements are recorded facts; modeled subsidy amounts are not paid funds.
    payments = await role_store.fetch_all(
        "SELECT scheme_name,COUNT(*) AS beneficiaries,SUM(amount) AS reimbursed "
        "FROM scheme_disbursements GROUP BY scheme_name ORDER BY reimbursed DESC"
    )
    applications = await role_store.fetch_one("SELECT COUNT(*) AS total FROM bank_applications")
    users = await role_store.fetch_one("SELECT COUNT(*) AS total FROM users")
    scheme_interest = await role_store.scheme_interest_summary()
    return {"registered_users": users["total"], "bank_applications": applications["total"],
            "total_reimbursed": sum(float(row["reimbursed"]) for row in payments),
            "schemes": [{**row, "reimbursed": float(row["reimbursed"])} for row in payments],
            "scheme_interest": scheme_interest}


@router.get("/government/schemes")
async def government_schemes(user: AuthenticatedUser = Depends(require_roles("government", "superadmin"))):
    return await role_store.fetch_all("SELECT * FROM custom_schemes ORDER BY created_at DESC")


@router.post("/government/schemes")
async def add_scheme(payload: SchemeIn, user: AuthenticatedUser = Depends(require_roles("government", "superadmin"))):
    scheme_id = f"SCH-{uuid.uuid4().hex[:12].upper()}"
    await role_store.execute(
        "INSERT INTO custom_schemes(scheme_id,name,description,administering_body,benefit_amount,created_by,created_at) "
        "VALUES(?,?,?,?,?,?,?)", scheme_id, payload.name.strip(), payload.description.strip(),
        payload.administering_body, payload.benefit_amount, user.uid,
        datetime.now(timezone.utc).isoformat(),
    )
    await role_store.record_activity(user.uid, "scheme_added", scheme_id)
    return {"scheme_id": scheme_id, **payload.model_dump()}


@router.post("/government/disbursements")
async def record_disbursement(payload: DisbursementIn,
                              user: AuthenticatedUser = Depends(require_roles("government", "superadmin"))):
    if not await db_manager.get_user(payload.beneficiary_uid):
        raise HTTPException(404, "Beneficiary not found.")
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    await role_store.execute(
        "INSERT INTO scheme_disbursements(disbursement_id,scheme_name,beneficiary_uid,amount,recorded_by,created_at) "
        "VALUES(?,?,?,?,?,?)", payment_id, payload.scheme_name.strip(), payload.beneficiary_uid,
        payload.amount, user.uid, datetime.now(timezone.utc).isoformat(),
    )
    await role_store.record_activity(user.uid, "reimbursement_recorded", payment_id)
    return {"disbursement_id": payment_id, **payload.model_dump()}
