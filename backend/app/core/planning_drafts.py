"""Owner-scoped TTL drafts shared by the existing PostgreSQL/SQLite workers.

Preview rows are separate from projects and feasibility reports. Table creation
is additive and uses the same database permissions as existing startup tables.
"""
import copy
import json
import time
import uuid

from fastapi import HTTPException

from app.core.enterprise_planning import Draft, sessions
from app.models.planning import PlanningRequest
from app.database import db_manager

TABLE_SQL = """CREATE TABLE IF NOT EXISTS planning_drafts (
    owner TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    payload TEXT NOT NULL
)"""


class PlanningDraftStore:
    def __init__(self, database, memory=sessions):
        self.database = database
        self.memory = memory

    async def save(self, owner, request, result):
        database = self.database
        if not database.pool and database.sqlite is None:
            # Isolated tests/preview fixtures do not start the application DB.
            return self.memory.save(owner, request, result)
        draft_id = uuid.uuid4().hex
        now = time.time()
        expires = now + 1800
        payload = json.dumps({"request": request.model_dump(mode="json"), "result": result}, allow_nan=False)
        if database.pool:
            async with database.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(TABLE_SQL)
                    await conn.execute("DELETE FROM planning_drafts WHERE expires_at < $1", now)
                    await conn.execute("""INSERT INTO planning_drafts (owner, draft_id, expires_at, payload)
                        VALUES ($1, $2, $3, $4) ON CONFLICT (owner) DO UPDATE SET
                        draft_id=EXCLUDED.draft_id, expires_at=EXCLUDED.expires_at, payload=EXCLUDED.payload""",
                        owner, draft_id, expires, payload)
        else:
            with database.sqlite as conn:
                conn.execute(TABLE_SQL)
                conn.execute("DELETE FROM planning_drafts WHERE expires_at < ?", (now,))
                conn.execute("""INSERT INTO planning_drafts (owner, draft_id, expires_at, payload)
                    VALUES (?, ?, ?, ?) ON CONFLICT (owner) DO UPDATE SET
                    draft_id=excluded.draft_id, expires_at=excluded.expires_at, payload=excluded.payload""",
                    (owner, draft_id, expires, payload))
        return draft_id

    async def get(self, owner, draft_id):
        database = self.database
        if not database.pool and database.sqlite is None:
            draft = self.memory.drafts.get(draft_id)
            if not draft or draft.owner != owner:
                raise HTTPException(404, "Planning preview not found. Evaluate again.")
            return copy.deepcopy(draft)
        if database.pool:
            async with database.pool.acquire() as conn:
                await conn.execute(TABLE_SQL)
                row = await conn.fetchrow("SELECT payload, expires_at FROM planning_drafts WHERE owner=$1 AND draft_id=$2", owner, draft_id)
        else:
            database.sqlite.execute(TABLE_SQL)
            row = database.sqlite.execute("SELECT payload, expires_at FROM planning_drafts WHERE owner=? AND draft_id=?", (owner, draft_id)).fetchone()
        if not row:
            raise HTTPException(404, "Planning preview not found or replaced. Evaluate again.")
        # Both asyncpg.Record and SQLite rows support positional access.
        payload = json.loads(row[0])
        return Draft(owner, row[1], PlanningRequest.model_validate(payload["request"]), payload["result"])


draft_store = PlanningDraftStore(db_manager)
