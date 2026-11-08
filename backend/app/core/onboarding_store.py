"""Owner-scoped resumable onboarding; no phone codes or audio are persisted."""
import copy
import json
from collections import OrderedDict
from fastapi import HTTPException
from app.database import db_manager

TABLE = 'CREATE TABLE IF NOT EXISTS mira_onboarding (owner TEXT PRIMARY KEY, payload TEXT NOT NULL)'


class OnboardingStore:
    def __init__(self, database):
        self.db = database
        self.memory = OrderedDict()

    async def get(self, owner):
        if self.db.pool:
            async with self.db.pool.acquire() as conn:
                await conn.execute(TABLE)
                raw = await conn.fetchval('SELECT payload FROM mira_onboarding WHERE owner=$1', owner)
        elif self.db.sqlite is not None:
            self.db.sqlite.execute(TABLE)
            row = self.db.sqlite.execute('SELECT payload FROM mira_onboarding WHERE owner=?', (owner,)).fetchone()
            raw = row[0] if row else None
        else:
            return copy.deepcopy(self.memory.get(owner))
        return json.loads(raw) if raw else None

    async def save(self, owner, data):
        raw = json.dumps(data, ensure_ascii=False, allow_nan=False)
        if len(raw.encode()) > 16000:
            raise HTTPException(422, 'Onboarding answers are too long. Please shorten the description.')
        if self.db.pool:
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute('SELECT pg_advisory_xact_lock(679024175)')
                    await conn.execute(TABLE)
                    await conn.execute('INSERT INTO mira_onboarding(owner,payload) VALUES($1,$2) ON CONFLICT(owner) DO UPDATE SET payload=excluded.payload', owner, raw)
        elif self.db.sqlite is not None:
            with self.db.sqlite as conn:
                conn.execute(TABLE)
                conn.execute('INSERT INTO mira_onboarding(owner,payload) VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET payload=excluded.payload', (owner, raw))
        else:
            self.memory[owner] = copy.deepcopy(data)
            while len(self.memory) > 500:
                self.memory.popitem(last=False)
        return data


onboarding_store = OnboardingStore(db_manager)
