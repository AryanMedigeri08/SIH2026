"""Strict LGD adapter. Never treats legacy synthetic fallback rows or postcodes as villages."""
from __future__ import annotations

import httpx


class LocationUnavailable(ValueError):
    pass


class OnboardingLocation:
    def __init__(self, db):
        self.db = db

    async def options(self, level: str, parent: int | None = None, search: str = ""):
        # Reuse the existing LGD tables and code conventions. Legacy API fallbacks
        # fabricate blocks/villages; these are deliberately excluded from onboarding.
        if not self.db.pool:
            if level == "states":
                return await self.db.get_states()
            raise LocationUnavailable("The official location directory is unavailable. Please retry when connected; your progress is saved.")
        queries = {
            "states": ("SELECT state_code, state_name FROM states ORDER BY state_name", []),
            "districts": ("SELECT district_code, district_name, state_code FROM districts WHERE state_code=$1 ORDER BY district_name", [parent]),
            "blocks": ("SELECT development_block_code, development_block_name, district_code FROM blocks WHERE district_code=$1 ORDER BY development_block_name", [parent]),
            "villages": ("SELECT village_code, village_name, development_block_code, district_code, state_code FROM villages WHERE development_block_code=$1 AND village_name ILIKE $2 ORDER BY village_name LIMIT 500", [parent, f"%{search}%"]),
        }
        if level not in queries or (level != "states" and parent is None):
            raise ValueError("Choose the parent location first.")
        sql, args = queries[level]
        async with self.db.pool.acquire() as conn:
            return [dict(row) for row in await conn.fetch(sql, *args)]

    async def select(self, selection):
        if not self.db.pool:
            raise LocationUnavailable("Connect to the official LGD directory to verify this business location.")
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT v.*, s.state_name, d.district_name, b.development_block_name
                FROM villages v
                JOIN blocks b ON v.development_block_code=b.development_block_code AND v.district_code=b.district_code
                JOIN districts d ON b.district_code=d.district_code AND v.state_code=d.state_code
                JOIN states s ON d.state_code=s.state_code
                WHERE s.state_code=$1 AND d.district_code=$2 AND b.development_block_code=$3 AND v.village_code=$4
            """, selection.state_code, selection.district_code, selection.block_code, selection.village_code)
        if not row:
            raise ValueError("That village does not belong to the selected state, district and development block. Please choose it again.")
        row = dict(row)
        # Use authoritative flags if actually provided by this deployment's LGD schema.
        is_rural = row.get("is_rural")
        if not isinstance(is_rural, bool):
            flag = str(row.get("rural_urban") or row.get("area_classification") or "").strip().lower()
            is_rural = {"rural": True, "urban": False, "r": True, "u": False}.get(flag)
        source = "lgd"
        if is_rural is None:
            is_rural = selection.verified_is_rural
            source = "legacy_user_verification"
        return {"state_code": selection.state_code, "district_code": selection.district_code,
                "block_code": selection.block_code, "village_code": selection.village_code,
                "state_name": row["state_name"], "district_name": row["district_name"],
                "block_name": row["development_block_name"], "village_name": row["village_name"],
                "is_rural": is_rural, "area_source": source if is_rural is not None else "verification_required",
                "latitude": float(row["latitude"]) if row.get("latitude") is not None else None,
                "longitude": float(row["longitude"]) if row.get("longitude") is not None else None,
                "source": "lgd"}

    async def detect(self, gps):
        if gps.accuracy > 1000:
            raise ValueError("This GPS reading covers more than one kilometre. Try again outdoors or choose your business location below.")
        # Reverse geocoding supplies candidates only. Exact LGD joins own the hierarchy.
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://nominatim.openstreetmap.org/reverse", params={
                "lat": gps.latitude, "lon": gps.longitude, "format": "json", "addressdetails": 1},
                headers={"User-Agent": "UdyamSaathi/2.0 location-verification"})
            response.raise_for_status()
            address = response.json().get("address", {})
        # Keep only locality evidence; exact device coordinates and street address
        # are not needed in the saved conversation or in the business report.
        physical = {"accuracy": gps.accuracy, "state_name": address.get("state"),
                    "district_hint": address.get("state_district") or address.get("district"),
                    "locality_hint": address.get("village") or address.get("hamlet") or address.get("town"),
                    "source": "gps_reverse_geocode_candidate"}
        if not self.db.pool:
            return physical, None
        village = address.get("village") or address.get("hamlet") or address.get("town") or ""
        district = address.get("state_district") or address.get("district") or address.get("county") or ""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT v.state_code, v.district_code, v.development_block_code, v.village_code
                FROM villages v JOIN districts d ON v.district_code=d.district_code
                JOIN states s ON d.state_code=s.state_code
                WHERE LOWER(s.state_name)=LOWER($1) AND LOWER(d.district_name)=LOWER($2)
                  AND LOWER(v.village_name)=LOWER($3) LIMIT 2
            """, address.get("state", ""), district, village)
        if len(rows) != 1:
            return physical, None
        from app.models.onboarding import LocationSelection
        row = dict(rows[0])
        selection = LocationSelection(revision=gps.revision, state_code=row["state_code"],
                                      district_code=row["district_code"], block_code=row["development_block_code"],
                                      village_code=row["village_code"])
        return physical, await self.select(selection)
