"""
database.py — Async Database Pool Manager with Neon PostgreSQL & In-Memory Fallback Store.
"""

from __future__ import annotations
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Union, Any
from pathlib import Path

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory LGD dataset for offline operation
FALLBACK_STATES = [
    {"state_code": 1, "state_name": "Jammu and Kashmir", "state_or_ut": "U"},
    {"state_code": 2, "state_name": "Himachal Pradesh", "state_or_ut": "S"},
    {"state_code": 3, "state_name": "Punjab", "state_or_ut": "S"},
    {"state_code": 4, "state_name": "Chandigarh", "state_or_ut": "U"},
    {"state_code": 5, "state_name": "Uttarakhand", "state_or_ut": "S"},
    {"state_code": 6, "state_name": "Haryana", "state_or_ut": "S"},
    {"state_code": 7, "state_name": "Delhi", "state_or_ut": "U"},
    {"state_code": 8, "state_name": "Rajasthan", "state_or_ut": "S"},
    {"state_code": 9, "state_name": "Uttar Pradesh", "state_or_ut": "S"},
    {"state_code": 10, "state_name": "Bihar", "state_or_ut": "S"},
    {"state_code": 11, "state_name": "Sikkim", "state_or_ut": "S"},
    {"state_code": 12, "state_name": "Arunachal Pradesh", "state_or_ut": "S"},
    {"state_code": 13, "state_name": "Nagaland", "state_or_ut": "S"},
    {"state_code": 14, "state_name": "Manipur", "state_or_ut": "S"},
    {"state_code": 15, "state_name": "Mizoram", "state_or_ut": "S"},
    {"state_code": 16, "state_name": "Tripura", "state_or_ut": "S"},
    {"state_code": 17, "state_name": "Meghalaya", "state_or_ut": "S"},
    {"state_code": 18, "state_name": "Assam", "state_or_ut": "S"},
    {"state_code": 19, "state_name": "West Bengal", "state_or_ut": "S"},
    {"state_code": 20, "state_name": "Jharkhand", "state_or_ut": "S"},
    {"state_code": 21, "state_name": "Odisha", "state_or_ut": "S"},
    {"state_code": 22, "state_name": "Chhattisgarh", "state_or_ut": "S"},
    {"state_code": 23, "state_name": "Madhya Pradesh", "state_or_ut": "S"},
    {"state_code": 24, "state_name": "Gujarat", "state_or_ut": "S"},
    {"state_code": 27, "state_name": "Maharashtra", "state_or_ut": "S"},
    {"state_code": 28, "state_name": "Andhra Pradesh", "state_or_ut": "S"},
    {"state_code": 29, "state_name": "Karnataka", "state_or_ut": "S"},
    {"state_code": 30, "state_name": "Goa", "state_or_ut": "S"},
    {"state_code": 31, "state_name": "Lakshadweep", "state_or_ut": "U"},
    {"state_code": 32, "state_name": "Kerala", "state_or_ut": "S"},
    {"state_code": 33, "state_name": "Tamil Nadu", "state_or_ut": "S"},
    {"state_code": 34, "state_name": "Puducherry", "state_or_ut": "U"},
    {"state_code": 35, "state_name": "Andaman and Nicobar Islands", "state_or_ut": "U"},
    {"state_code": 36, "state_name": "Telangana", "state_or_ut": "S"},
    {"state_code": 37, "state_name": "Ladakh", "state_or_ut": "U"},
]

FALLBACK_DISTRICTS = {
    19: [  # West Bengal
        {"district_code": 312, "district_name": "Bankura", "state_code": 19},
        {"district_code": 313, "district_name": "Purulia", "state_code": 19},
        {"district_code": 314, "district_name": "Birbhum", "state_code": 19},
        {"district_code": 315, "district_name": "Purba Bardhaman", "state_code": 19},
        {"district_code": 318, "district_name": "Kolkata", "state_code": 19},
    ],
    29: [  # Karnataka
        {"district_code": 541, "district_name": "Ramanagara", "state_code": 29},
        {"district_code": 542, "district_name": "Bengaluru Urban", "state_code": 29},
        {"district_code": 543, "district_name": "Bengaluru Rural", "state_code": 29},
        {"district_code": 544, "district_name": "Mysuru", "state_code": 29},
    ],
    9: [  # Uttar Pradesh
        {"district_code": 178, "district_name": "Varanasi", "state_code": 9},
        {"district_code": 179, "district_name": "Bulandshahr", "state_code": 9},
        {"district_code": 180, "district_name": "Lucknow", "state_code": 9},
        {"district_code": 181, "district_name": "Prayagraj", "state_code": 9},
    ],
    23: [  # Madhya Pradesh
        {"district_code": 401, "district_name": "Ujjain", "state_code": 23},
        {"district_code": 402, "district_name": "Indore", "state_code": 23},
        {"district_code": 403, "district_name": "Bhopal", "state_code": 23},
    ],
    33: [  # Tamil Nadu
        {"district_code": 580, "district_name": "Chennai", "state_code": 33},
        {"district_code": 581, "district_name": "Coimbatore", "state_code": 33},
        {"district_code": 582, "district_name": "Madurai", "state_code": 33},
    ],
    27: [  # Maharashtra
        {"district_code": 480, "district_name": "Pune", "state_code": 27},
        {"district_code": 481, "district_name": "Mumbai", "state_code": 27},
        {"district_code": 482, "district_name": "Nagpur", "state_code": 27},
    ],
}


class DatabaseManager:
    """
    Manages async connection pool and provides CRUD operations for LGD hierarchy and projects.
    """
    _instance: Optional[DatabaseManager] = None

    def __init__(self):
        self.pool = None
        self.in_memory_projects: dict[str, dict[str, Any]] = {}
        self.in_memory_reports: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self):
        if settings.DATABASE_URL and settings.DATABASE_URL.strip():
            try:
                import asyncpg
                self.pool = await asyncpg.create_pool(
                    settings.DATABASE_URL.strip(),
                    min_size=1,
                    max_size=10,
                    timeout=10.0,
                )
                logger.info("Connected to Neon PostgreSQL pool successfully.")
                await self._init_tables()
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed ({e}); operating in in-memory mode.")
                self.pool = None
        else:
            logger.info("DATABASE_URL not set; running with fast in-memory store.")
            self.pool = None

    async def _init_tables(self):
        if not self.pool:
            return
        try:
            async with self.pool.acquire() as conn:
                # Ensure default demo user exists for foreign key constraint
                try:
                    await conn.execute("""
                        INSERT INTO users (firebase_uid, name, email, language)
                        VALUES ('guest_user', 'Guest Entrepreneur', 'guest@udyam.gov.in', 'en')
                        ON CONFLICT (firebase_uid) DO NOTHING;
                    """)
                except Exception:
                    pass

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS feasibility_reports (
                        report_id VARCHAR(64) PRIMARY KEY,
                        report_payload JSONB NOT NULL,
                        dpr_payload JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                logger.info("PostgreSQL schema & tables initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not auto-create tables: {e}")

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    # --- LGD Location Resolvers ---
    async def get_states(self) -> list[dict[str, Any]]:
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch("SELECT state_code, state_name, state_or_ut, census_2011_code FROM states ORDER BY state_name")
                    if rows:
                        return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"Error querying states from DB: {e}")
        return FALLBACK_STATES

    async def get_districts(self, state_code: Optional[int] = None, state_name: Optional[str] = None, search: Optional[str] = None) -> list[dict[str, Any]]:
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    resolved_code = state_code
                    if resolved_code is None and state_name:
                        resolved_code = await conn.fetchval(
                            "SELECT state_code FROM states WHERE LOWER(state_name) = LOWER($1) OR state_name ILIKE $1 LIMIT 1",
                            state_name.strip()
                        )
                    
                    if resolved_code is not None:
                        rows = await conn.fetch(
                            "SELECT district_code, district_name, state_code, census_2011_code FROM districts WHERE state_code = $1 ORDER BY district_name",
                            resolved_code
                        )
                        if rows:
                            return [dict(r) for r in rows]
                    elif search:
                        rows = await conn.fetch(
                            "SELECT district_code, district_name, state_code, census_2011_code FROM districts WHERE district_name ILIKE $1 ORDER BY district_name LIMIT 100",
                            f"%{search.strip()}%"
                        )
                        if rows:
                            return [dict(r) for r in rows]
                    else:
                        rows = await conn.fetch(
                            "SELECT district_code, district_name, state_code, census_2011_code FROM districts ORDER BY district_name LIMIT 100"
                        )
                        if rows:
                            return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"Error querying districts from DB: {e}")

        # Fallback resolution
        resolved_code = state_code
        if resolved_code is None and state_name:
            for s in FALLBACK_STATES:
                if s["state_name"].lower() == state_name.lower():
                    resolved_code = s["state_code"]
                    break

        if resolved_code in FALLBACK_DISTRICTS:
            return FALLBACK_DISTRICTS[resolved_code]
        all_dists = []
        for d_list in FALLBACK_DISTRICTS.values():
            all_dists.extend(d_list)
        return all_dists[:20]

    async def get_blocks(
        self,
        district_code: Optional[int] = None,
        district_name: Optional[str] = None,
        state_name: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    resolved_dist = district_code
                    if resolved_dist is None and district_name:
                        resolved_dist = await conn.fetchval(
                            "SELECT district_code FROM districts WHERE LOWER(district_name) = LOWER($1) OR district_name ILIKE $1 LIMIT 1",
                            district_name.strip()
                        )
                    
                    if resolved_dist is not None:
                        rows = await conn.fetch(
                            "SELECT development_block_code, development_block_name, district_code FROM blocks WHERE district_code = $1 ORDER BY development_block_name",
                            resolved_dist
                        )
                        if rows:
                            return [dict(r) for r in rows]
                    elif search:
                        rows = await conn.fetch(
                            "SELECT development_block_code, development_block_name, district_code FROM blocks WHERE development_block_name ILIKE $1 ORDER BY development_block_name LIMIT 100",
                            f"%{search.strip()}%"
                        )
                        if rows:
                            return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"Error querying blocks from DB: {e}")

        dist_id = district_code or 312
        return [
            {"development_block_code": dist_id * 10 + 1, "development_block_name": f"{district_name or 'Central'} Block", "district_code": dist_id},
            {"development_block_code": dist_id * 10 + 2, "development_block_name": f"{district_name or 'Rural'} Block North", "district_code": dist_id},
            {"development_block_code": dist_id * 10 + 3, "development_block_name": f"{district_name or 'Rural'} Block South", "district_code": dist_id},
        ]

    async def get_villages(
        self,
        district_code: Optional[int] = None,
        block_code: Optional[int] = None,
        district_name: Optional[str] = None,
        block_name: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    resolved_dist = district_code
                    if resolved_dist is None and district_name:
                        resolved_dist = await conn.fetchval(
                            "SELECT district_code FROM districts WHERE LOWER(district_name) = LOWER($1) OR district_name ILIKE $1 LIMIT 1",
                            district_name.strip()
                        )

                    resolved_block = block_code
                    if resolved_block is None and block_name:
                        resolved_block = await conn.fetchval(
                            "SELECT development_block_code FROM blocks WHERE LOWER(development_block_name) = LOWER($1) OR development_block_name ILIKE $1 LIMIT 1",
                            block_name.strip()
                        )

                    if resolved_block is not None:
                        rows = await conn.fetch(
                            "SELECT id, village_code, village_name, subdistrict_code, district_code, state_code, development_block_code, pincode FROM villages WHERE development_block_code = $1 ORDER BY village_name LIMIT 100",
                            resolved_block
                        )
                        if rows:
                            return [dict(r) for r in rows]

                    if resolved_dist is not None:
                        rows = await conn.fetch(
                            "SELECT id, village_code, village_name, subdistrict_code, district_code, state_code, development_block_code, pincode FROM villages WHERE district_code = $1 ORDER BY village_name LIMIT 100",
                            resolved_dist
                        )
                        if rows:
                            return [dict(r) for r in rows]

                    if search:
                        rows = await conn.fetch(
                            "SELECT id, village_code, village_name, subdistrict_code, district_code, state_code, development_block_code, pincode FROM villages WHERE village_name ILIKE $1 ORDER BY village_name LIMIT 100",
                            f"%{search.strip()}%"
                        )
                        if rows:
                            return [dict(r) for r in rows]
            except Exception as e:
                logger.warning(f"Error querying villages from DB: {e}")

        dist_id = district_code or 312
        return [
            {"id": 1, "village_code": dist_id * 100 + 1, "village_name": f"Gram {district_name or 'Joypur'}", "district_code": dist_id, "pincode": "722138"},
            {"id": 2, "village_code": dist_id * 100 + 2, "village_name": f"Gram {district_name or 'Kalyanpur'}", "district_code": dist_id, "pincode": "722139"},
            {"id": 3, "village_code": dist_id * 100 + 3, "village_name": f"Gram {district_name or 'Shivpur'}", "district_code": dist_id, "pincode": "722140"},
        ]

    # --- Live Census, MSME, CPI & Weather Query Resolvers ---
    async def get_census_demographics(
        self,
        state_name: str,
        district_name: str,
        village_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Queries census_raw table (660k+ records) for ground-truth village/district population.
        Falls back to district or state average if village is not individually enumerated.
        """
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    # 1. Direct village lookup in census_raw
                    if village_name and village_name.strip() and village_name.strip() != "N/A":
                        v_clean = village_name.strip()
                        row = await conn.fetchrow("""
                            SELECT total_population, total_households, sc_population, st_population, literate_population, area_name, administrative_level
                            FROM census_raw
                            WHERE area_name ILIKE $1
                            ORDER BY total_population DESC
                            LIMIT 1
                        """, f"%{v_clean}%")
                        if row and row["total_population"] and row["total_population"] > 0:
                            return {
                                "base_population_2011": int(row["total_population"]),
                                "base_households_2011": int(row["total_households"] or max(int(row["total_population"] / 4.8), 1)),
                                "sc_population": int(row["sc_population"] or 0),
                                "st_population": int(row["st_population"] or 0),
                                "literate_population": int(row["literate_population"] or 0),
                                "area_name": row["area_name"],
                                "provenance": "census_exact_village",
                            }

                    # 2. Subdistrict / Block / District level lookup in census_raw
                    d_clean = district_name.strip()
                    row_dist = await conn.fetchrow("""
                        SELECT total_population, total_households, sc_population, st_population, literate_population, area_name
                        FROM census_raw
                        WHERE area_name ILIKE $1 AND administrative_level IN ('DISTRICT', 'SUB-DISTRICT')
                        LIMIT 1
                    """, f"%{d_clean}%")
                    if row_dist and row_dist["total_population"] and row_dist["total_population"] > 0:
                        # Derive village catchment estimate from district average
                        tot_pop = int(row_dist["total_population"])
                        derived_village_pop = min(max(int(tot_pop / 350), 1200), 15000)
                        return {
                            "base_population_2011": derived_village_pop,
                            "base_households_2011": max(int(derived_village_pop / 4.8), 1),
                            "sc_population": int(row_dist["sc_population"] or 0),
                            "st_population": int(row_dist["st_population"] or 0),
                            "literate_population": int(row_dist["literate_population"] or 0),
                            "area_name": f"Catchment in {row_dist['area_name']}",
                            "provenance": "census_district_catchment",
                        }
            except Exception as e:
                logger.warning(f"Census query error: {e}")

        # Baseline fallback
        return {
            "base_population_2011": 3850,
            "base_households_2011": 802,
            "sc_population": 540,
            "st_population": 120,
            "literate_population": 2680,
            "area_name": f"Catchment {village_name or district_name}",
            "provenance": "regional_baseline",
        }

    async def get_district_msme_stats(
        self,
        state_name: str,
        district_name: str,
    ) -> dict[str, Any]:
        """
        Queries msme_district table for registered MSMEs count in the target district.
        """
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    d_clean = district_name.strip()
                    row = await conn.fetchrow("""
                        SELECT total, micro, small, medium, state_name, district_name
                        FROM msme_district
                        WHERE district_name ILIKE $1 OR district_name ILIKE $2
                        LIMIT 1
                    """, d_clean, f"%{d_clean}%")
                    if row and row["total"] is not None:
                        return {
                            "total_msme": int(row["total"]),
                            "micro": int(row["micro"] or 0),
                            "small": int(row["small"] or 0),
                            "medium": int(row["medium"] or 0),
                            "state_name": row["state_name"],
                            "district_name": row["district_name"],
                            "provenance": "msme_district_live",
                        }
            except Exception as e:
                logger.warning(f"MSME district query error: {e}")

        return {
            "total_msme": 1250,
            "micro": 1200,
            "small": 45,
            "medium": 5,
            "state_name": state_name,
            "district_name": district_name,
            "provenance": "state_baseline",
        }

    async def get_state_cpi_inflation(self, state_name: str) -> float:
        """
        Queries cpi_data table for the latest state rural CPI inflation rate.
        """
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    s_clean = state_name.strip()
                    row = await conn.fetchrow("""
                        SELECT inflation
                        FROM cpi_data
                        WHERE (state ILIKE $1 OR state = 'All India') AND sector = 'Rural' AND division = 'CPI (General)'
                        ORDER BY year DESC, month DESC
                        LIMIT 1
                    """, f"%{s_clean}%")
                    if row and row["inflation"] is not None:
                        return float(row["inflation"])
            except Exception as e:
                logger.warning(f"CPI query error: {e}")

        return 4.85

    async def get_weather_risk_score(self, state_name: str, district_name: str) -> float:
        """
        Computes geographic weather & monsoon climate disruption risk index (0.0 to 1.0).
        """
        coastal_riverine = ["West Bengal", "Kerala", "Assam", "Odisha", "Bihar", "Tamil Nadu", "Andhra Pradesh", "Goa"]
        arid_drought = ["Rajasthan", "Gujarat", "Haryana", "Punjab"]
        hilly_landslide = ["Himachal Pradesh", "Uttarakhand", "Jammu and Kashmir", "Sikkim", "Meghalaya"]

        s_clean = state_name.strip()
        if any(c.lower() in s_clean.lower() for c in coastal_riverine):
            return 0.28  # Moderate seasonal monsoon / flood factor
        elif any(a.lower() in s_clean.lower() for a in arid_drought):
            return 0.15  # Low rain, higher summer heat factor
        elif any(h.lower() in s_clean.lower() for h in hilly_landslide):
            return 0.32  # Mountain terrain / monsoon transport disruption factor
        return 0.20

    # --- Project Persistence CRUD ---
    async def create_project(self, project_dict: dict[str, Any]) -> dict[str, Any]:
        project_id = project_dict.get("project_id") or f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        business_name = project_dict.get("enterprise_name") or project_dict.get("business_name", "Enterprise Unit")
        business_category = project_dict.get("business_category", "manufacturing")
        investment_amount = float(project_dict.get("project_cost") or project_dict.get("investment_amount", 500000.0))
        state_name = project_dict.get("state_name", "West Bengal")
        district_name = project_dict.get("district_name", "Bankura")
        block_name = project_dict.get("block_name", "Joypur")
        village_name = project_dict.get("village_name", "Joypur")
        user_id = project_dict.get("user_id", "guest_user")
        analysis_result = project_dict.get("analysis_result", {})

        record = {
            **project_dict,
            "project_id": project_id,
            "enterprise_name": business_name,
            "business_name": business_name,
            "project_cost": investment_amount,
            "investment_amount": investment_amount,
            "created_at": now,
            "updated_at": now,
        }
        self.in_memory_projects[project_id] = record

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO projects (
                            project_id, user_id, business_name, business_category, investment_amount,
                            state_name, district_name, block_name, village_name, analysis_result, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                        ON CONFLICT (project_id) DO UPDATE SET
                            business_name = EXCLUDED.business_name,
                            business_category = EXCLUDED.business_category,
                            investment_amount = EXCLUDED.investment_amount,
                            state_name = EXCLUDED.state_name,
                            district_name = EXCLUDED.district_name,
                            block_name = EXCLUDED.block_name,
                            village_name = EXCLUDED.village_name,
                            analysis_result = EXCLUDED.analysis_result
                    """,
                    project_id,
                    user_id,
                    business_name,
                    business_category,
                    investment_amount,
                    state_name,
                    district_name,
                    block_name,
                    village_name,
                    json.dumps(analysis_result),
                    )
            except Exception as e:
                logger.warning(f"Could not persist project to PostgreSQL: {e}")

        return record

    async def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        if project_id in self.in_memory_projects:
            return self.in_memory_projects[project_id]

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM projects WHERE project_id = $1", project_id)
                    if row:
                        rec = dict(row)
                        if isinstance(rec.get("analysis_result"), str):
                            rec["analysis_result"] = json.loads(rec["analysis_result"])
                        rec["enterprise_name"] = rec.get("business_name")
                        rec["project_cost"] = float(rec.get("investment_amount") or 0.0)
                        self.in_memory_projects[project_id] = rec
                        return rec
            except Exception as e:
                logger.warning(f"Could not fetch project from PostgreSQL: {e}")

        return None

    async def list_projects(self, user_id: str = "guest_user") -> list[dict[str, Any]]:
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    if user_id == "all":
                        rows = await conn.fetch("SELECT * FROM projects ORDER BY created_at DESC LIMIT 50")
                    else:
                        rows = await conn.fetch("SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC LIMIT 50", user_id)
                    results = []
                    for r in rows:
                        rec = dict(r)
                        if isinstance(rec.get("analysis_result"), str):
                            rec["analysis_result"] = json.loads(rec["analysis_result"])
                        rec["enterprise_name"] = rec.get("business_name")
                        rec["project_cost"] = float(rec.get("investment_amount") or 0.0)
                        self.in_memory_projects[rec["project_id"]] = rec
                        results.append(rec)
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"Could not list projects from PostgreSQL: {e}")

        return [p for p in self.in_memory_projects.values() if p.get("user_id") == user_id or user_id == "all"]

    async def update_project_analysis(self, project_id: str, analysis_result: dict[str, Any]) -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        if project_id in self.in_memory_projects:
            self.in_memory_projects[project_id]["analysis_result"] = analysis_result
            self.in_memory_projects[project_id]["status"] = "analyzed"
            self.in_memory_projects[project_id]["updated_at"] = now

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE projects
                        SET analysis_result = $1
                        WHERE project_id = $2
                    """, json.dumps(analysis_result), project_id)
            except Exception as e:
                logger.warning(f"Could not update project analysis in PostgreSQL: {e}")

        return self.in_memory_projects.get(project_id)

    # --- Feasibility Report Cache Store ---
    async def save_feasibility_report(self, report_id: str, report_data: dict[str, Any]) -> None:
        self.in_memory_reports[report_id] = report_data

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO feasibility_reports (report_id, report_payload, dpr_payload)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (report_id) DO UPDATE SET
                            report_payload = EXCLUDED.report_payload,
                            dpr_payload = EXCLUDED.dpr_payload
                    """,
                    report_id,
                    json.dumps(report_data.get("report", {})),
                    json.dumps(report_data.get("dpr", {})),
                    )
            except Exception as e:
                logger.warning(f"Could not save feasibility report to PostgreSQL: {e}")

    async def get_feasibility_report(self, report_id: str) -> Optional[dict[str, Any]]:
        if report_id in self.in_memory_reports:
            return self.in_memory_reports[report_id]

        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT report_payload, dpr_payload FROM feasibility_reports WHERE report_id = $1", report_id)
                    if row:
                        rep = json.loads(row["report_payload"]) if isinstance(row["report_payload"], str) else row["report_payload"]
                        dpr = json.loads(row["dpr_payload"]) if isinstance(row["dpr_payload"], str) else row["dpr_payload"]
                        payload = {"report": rep, "dpr": dpr}
                        self.in_memory_reports[report_id] = payload
                        return payload
            except Exception as e:
                logger.warning(f"Could not fetch feasibility report from PostgreSQL: {e}")

        return None


db_manager = DatabaseManager.get_instance()
