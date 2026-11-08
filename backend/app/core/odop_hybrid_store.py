"""Shared ODOP advice cache and owner request leases for both backend workers."""
import copy
import json
import math
import uuid
from collections import OrderedDict

from fastapi import HTTPException
from app.database import db_manager

TABLE = """CREATE TABLE IF NOT EXISTS odop_hybrid_reviews (
    owner TEXT PRIMARY KEY, input_hash TEXT NOT NULL DEFAULT '',
    attempt_id TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'idle',
    payload TEXT, expires_at DOUBLE PRECISION NOT NULL DEFAULT 0,
    lease_until DOUBLE PRECISION NOT NULL DEFAULT 0,
    next_allowed_at DOUBLE PRECISION NOT NULL DEFAULT 0
)"""
COLUMNS = "input_hash, attempt_id, status, payload, expires_at, lease_until, next_allowed_at"


def reserve_decision(row, input_hash, now):
    if row and row["input_hash"] == input_hash and row["status"] == "ready" and row["expires_at"] > now:
        return {"cached": json.loads(row["payload"])}
    wait = max(row["lease_until"], row["next_allowed_at"]) - now if row else 0
    if wait > 0:
        seconds = max(1, math.ceil(wait))
        raise HTTPException(429, f"Please wait {seconds} seconds before another ODOP evaluation.", headers={"Retry-After": str(seconds)})
    return {"attempt_id": uuid.uuid4().hex}


class HybridStore:
    def __init__(self, database):
        self.database = database
        self.memory = OrderedDict()

    async def reserve(self, owner, input_hash, now):
        db = self.database
        if db.pool:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Serialize first-use DDL across the deployed workers.
                    await conn.execute("SELECT pg_advisory_xact_lock(679024173)")
                    await conn.execute(TABLE)
                    await conn.execute("INSERT INTO odop_hybrid_reviews (owner) VALUES ($1) ON CONFLICT (owner) DO NOTHING", owner)
                    row = await conn.fetchrow(f"SELECT {COLUMNS} FROM odop_hybrid_reviews WHERE owner=$1 FOR UPDATE", owner)
                    decision = reserve_decision(dict(row), input_hash, now)
                    if "cached" not in decision:
                        await conn.execute("""UPDATE odop_hybrid_reviews SET input_hash=$2, attempt_id=$3,
                            status='pending', payload=NULL, expires_at=$4, lease_until=$5, next_allowed_at=$6 WHERE owner=$1""",
                            owner, input_hash, decision["attempt_id"], now + 86400, now + 20, now + 30)
                    return decision
        if db.sqlite is not None:
            with db.sqlite as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(TABLE)
                row = conn.execute(f"SELECT {COLUMNS} FROM odop_hybrid_reviews WHERE owner=?", (owner,)).fetchone()
                data = dict(zip(COLUMNS.split(", "), row)) if row else None
                decision = reserve_decision(data, input_hash, now)
                if "cached" not in decision:
                    conn.execute("""INSERT INTO odop_hybrid_reviews
                        (owner,input_hash,attempt_id,status,payload,expires_at,lease_until,next_allowed_at)
                        VALUES (?,?,?,'pending',NULL,?,?,?) ON CONFLICT(owner) DO UPDATE SET
                        input_hash=excluded.input_hash,attempt_id=excluded.attempt_id,status='pending',payload=NULL,
                        expires_at=excluded.expires_at,lease_until=excluded.lease_until,next_allowed_at=excluded.next_allowed_at""",
                        (owner, input_hash, decision["attempt_id"], now + 86400, now + 20, now + 30))
                return decision
        decision = reserve_decision(self.memory.get(owner), input_hash, now)
        if "cached" not in decision:
            self.memory[owner] = dict(input_hash=input_hash, attempt_id=decision["attempt_id"], status="pending",
                payload=None, expires_at=now + 86400, lease_until=now + 20, next_allowed_at=now + 30)
            while len(self.memory) > 500:
                self.memory.popitem(last=False)
        return copy.deepcopy(decision)

    async def complete(self, owner, attempt_id, result, now):
        db = self.database
        status = "ready" if result is not None else "error"
        payload = json.dumps(result, allow_nan=False) if result is not None else None
        expires = now + (86400 if result is not None else 30)
        if db.pool:
            async with db.pool.acquire() as conn:
                await conn.execute("""UPDATE odop_hybrid_reviews SET status=$3,payload=$4,expires_at=$5,lease_until=0
                    WHERE owner=$1 AND attempt_id=$2""", owner, attempt_id, status, payload, expires)
        elif db.sqlite is not None:
            with db.sqlite as conn:
                conn.execute("""UPDATE odop_hybrid_reviews SET status=?,payload=?,expires_at=?,lease_until=0
                    WHERE owner=? AND attempt_id=?""", (status, payload, expires, owner, attempt_id))
        else:
            row = self.memory.get(owner)
            if row and row["attempt_id"] == attempt_id:
                row.update(status=status, payload=payload, expires_at=expires, lease_until=0)


hybrid_store = HybridStore(db_manager)
