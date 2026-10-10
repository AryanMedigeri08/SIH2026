"""Small relational store for role assignments, DPR handoff, and conversations.

Only IDs and messages are stored here. DPR bodies remain in the existing
projects/feasibility tables, avoiding duplicate large JSON payloads.
"""

from __future__ import annotations

import re
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from app.database import db_manager


def location_key(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def _postgres_sql(sql: str) -> str:
    index = 0

    def replace(_: re.Match[str]) -> str:
        nonlocal index
        index += 1
        return f"${index}"

    return re.sub(r"\?", replace, sql)


def _ready() -> None:
    if not db_manager.pool and not db_manager.sqlite:
        raise HTTPException(503, "Persistent database is unavailable.")


async def fetch_all(sql: str, *args: Any) -> list[dict[str, Any]]:
    _ready()
    if db_manager.pool:
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch(_postgres_sql(sql), *args)
            return [dict(row) for row in rows]
    rows = db_manager.sqlite.execute(sql, args).fetchall()
    return [dict(row) for row in rows]


async def fetch_one(sql: str, *args: Any) -> dict[str, Any] | None:
    rows = await fetch_all(sql, *args)
    return rows[0] if rows else None


async def execute(sql: str, *args: Any) -> None:
    _ready()
    if db_manager.pool:
        async with db_manager.pool.acquire() as conn:
            # asyncpg expects native timestamp/numeric values, not SQLite-style
            # ISO strings and Python floats for TIMESTAMPTZ/NUMERIC columns.
            native_args = tuple(
                datetime.fromisoformat(arg) if isinstance(arg, str) and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?\+\d\d:\d\d", arg)
                else Decimal(str(arg)) if isinstance(arg, float)
                else arg for arg in args
            )
            await conn.execute(_postgres_sql(sql), *native_args)
    else:
        db_manager.sqlite.execute(sql, args)
        db_manager.sqlite.commit()


async def get_role(uid: str) -> dict[str, Any]:
    row = await fetch_one("SELECT role,state_key,district_key,village_key FROM user_roles WHERE user_id=?", uid)
    return row or {"role": "entrepreneur", "state_key": None, "district_key": None, "village_key": None}


async def assign_role(uid: str, role: str, state: str | None = None, district: str | None = None, village: str | None = None) -> None:
    if role not in {"entrepreneur", "banker", "government", "superadmin"}:
        raise ValueError("Invalid role")
    await execute(
        "INSERT INTO user_roles(user_id,role,state_key,district_key,village_key,created_at) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET role=excluded.role,state_key=excluded.state_key,district_key=excluded.district_key,village_key=excluded.village_key",
        uid, role, location_key(state) if state else None,
        location_key(district) if district else None,
        location_key(village) if village else None,
        datetime.now(timezone.utc).isoformat(),
    )


async def find_banker(state: str, district: str, village: str) -> dict[str, Any] | None:
    return await fetch_one(
        "SELECT user_id FROM user_roles WHERE role='banker' AND state_key=? AND district_key=? AND village_key=?",
        location_key(state), location_key(district), location_key(village),
    )


async def bank_verification(state: str, district: str, village: str) -> dict[str, Any] | None:
    return await fetch_one(
        "SELECT available,evidence,verified_by,verified_at FROM bank_branch_verifications "
        "WHERE state_key=? AND district_key=? AND village_key=?",
        location_key(state), location_key(district), location_key(village),
    )


async def save_bank_verification(state: str, district: str, village: str,
                                 available: bool, evidence: str, verified_by: str) -> None:
    await execute(
        "INSERT INTO bank_branch_verifications(state_key,district_key,village_key,available,evidence,verified_by,verified_at) "
        "VALUES(?,?,?,?,?,?,?) ON CONFLICT(state_key,district_key,village_key) DO UPDATE SET "
        "available=excluded.available,evidence=excluded.evidence,verified_by=excluded.verified_by,verified_at=excluded.verified_at",
        location_key(state), location_key(district), location_key(village),
        available, evidence.strip(), verified_by, datetime.now(timezone.utc).isoformat(),
    )


async def submit_application(project_id: str, entrepreneur_uid: str, banker_uid: str) -> dict[str, Any]:
    application_id = f"APP-{uuid.uuid4().hex[:12].upper()}"
    await execute(
        "INSERT INTO bank_applications(application_id,project_id,entrepreneur_uid,banker_uid,status,submitted_at) "
        "VALUES(?,?,?,?,'submitted',?) ON CONFLICT(project_id,banker_uid) DO NOTHING",
        application_id, project_id, entrepreneur_uid, banker_uid, datetime.now(timezone.utc).isoformat(),
    )
    return await fetch_one("SELECT * FROM bank_applications WHERE project_id=? AND banker_uid=?", project_id, banker_uid)


async def get_application(application_id: str) -> dict[str, Any] | None:
    return await fetch_one("SELECT * FROM bank_applications WHERE application_id=?", application_id)


async def list_applications(uid: str, role: str) -> list[dict[str, Any]]:
    column = "banker_uid" if role == "banker" else "entrepreneur_uid"
    applications = await fetch_all(
        f"SELECT * FROM bank_applications WHERE {column}=? ORDER BY submitted_at DESC", uid,
    )
    for application in applications:
        project = await db_manager.get_project(application["project_id"])
        if project:
            application.update({key: project.get(key) for key in
                                ("business_name", "village_name", "district_name", "state_name")})
    return applications


async def list_messages(application_id: str) -> list[dict[str, Any]]:
    return await fetch_all(
        "SELECT message_id,application_id,sender_uid,recipient_uid,body,created_at "
        "FROM application_messages WHERE application_id=? ORDER BY created_at,message_id", application_id,
    )


async def add_message(application_id: str, sender_uid: str, recipient_uid: str, body: str) -> dict[str, Any]:
    message_id = f"MSG-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    await execute(
        "INSERT INTO application_messages(message_id,application_id,sender_uid,recipient_uid,body,created_at) VALUES(?,?,?,?,?,?)",
        message_id, application_id, sender_uid, recipient_uid, body, timestamp,
    )
    return {"message_id": message_id, "application_id": application_id, "sender_uid": sender_uid,
            "recipient_uid": recipient_uid, "body": body, "created_at": timestamp}


async def record_activity(uid: str, action: str, subject_id: str | None = None) -> None:
    await execute(
        "INSERT INTO activity_events(event_id,actor_uid,action,subject_id,created_at) VALUES(?,?,?,?,?)",
        f"EVT-{uuid.uuid4().hex[:12].upper()}", uid, action, subject_id, datetime.now(timezone.utc).isoformat(),
    )


async def scheme_interest_summary() -> list[dict[str, Any]]:
    """Aggregate eligible DPR recommendations, never confuse them with payments."""
    if db_manager.pool:
        rows = await fetch_all(
            "SELECT user_id, analysis_result #> '{report,scheme_optimization}' AS schemes "
            "FROM projects WHERE analysis_result IS NOT NULL"
        )
    else:
        rows = await fetch_all("SELECT user_id,payload FROM projects")
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        if "payload" in row:
            payload = json.loads(row["payload"])
            schemes = (payload.get("analysis_result") or {}).get("report", {}).get("scheme_optimization", [])
        else:
            schemes = row.get("schemes")
            if isinstance(schemes, str):
                schemes = json.loads(schemes)
        for scheme in schemes or []:
            if not isinstance(scheme, dict) or scheme.get("eligible") is not True:
                continue
            name = str(scheme.get("scheme_id") or scheme.get("full_name") or "").strip()
            if not name:
                continue
            entry = grouped.setdefault(name, {"scheme_name": name, "eligible_projects": 0, "entrepreneurs": set()})
            entry["eligible_projects"] += 1
            entry["entrepreneurs"].add(row["user_id"])
    return sorted(
        ({"scheme_name": entry["scheme_name"], "eligible_projects": entry["eligible_projects"],
          "entrepreneurs": len(entry["entrepreneurs"])} for entry in grouped.values()),
        key=lambda item: (-item["eligible_projects"], item["scheme_name"]),
    )
