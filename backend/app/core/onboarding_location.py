"""Strict LGD adapter. Never treats legacy synthetic fallback rows or postcodes as villages."""
from __future__ import annotations

import httpx
import re
import json
import sqlite3
import math
import asyncio
from pathlib import Path
from app.core.area_classification import classify_area, official_area_flag, fetch_area_amenities

LOCALITY_DB = Path(__file__).resolve().parent / 'data' / 'locality_master.sqlite3'


def place_name(value):
    return re.sub(r'[^\w]', '', re.sub(r'\s+(?:district|division)$', '', value or '', flags=re.I).casefold())


def postal_location_hint(latitude, longitude):
    """Reference-branch postal fallback: approximate hints, never invented LGD codes."""
    if not LOCALITY_DB.exists():
        return None
    try:
        with sqlite3.connect(f'file:{LOCALITY_DB.as_posix()}?mode=ro', uri=True) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute('''SELECT state,district,taluk,office_name,latitude,longitude
                FROM pincode_localities WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
                ORDER BY ((latitude-?)*(latitude-?)*1.5+(longitude-?)*(longitude-?)) LIMIT 1''',
                (latitude-.1,latitude+.1,longitude-.1,longitude+.1,latitude,latitude,longitude,longitude)).fetchone()
        if row:
            distance = math.hypot((row['latitude']-latitude)*111, (row['longitude']-longitude)*111*math.cos(math.radians(latitude)))
            if distance <= 10:
                return {'state':row['state'],'district':row['district'],'county':row['taluk'],
                    'village':re.sub(r'\s+(?:B\.?O\.?|S\.?O\.?|H\.?O\.?)$', '', row['office_name'], flags=re.I)}
    except (sqlite3.Error, OSError):
        pass
    return None


class LocationUnavailable(ValueError):
    pass


class OnboardingLocation:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def area_flag(row):
        return official_area_flag(row)

    async def census_evidence(self, selection):
        try:
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT to_jsonb(c) AS evidence FROM census_raw c
                    JOIN villages v ON v.village_code=$1
                    JOIN states s ON s.state_code=v.state_code
                    JOIN districts d ON d.district_code=v.district_code AND d.state_code=s.state_code
                    WHERE s.state_code=$2 AND d.district_code=$3 AND (
                        c.matched_village_code=v.village_code OR (
                            c.town_village=LPAD(v.village_census_2011_code::text,6,'0')
                            AND c.state=LPAD(s.census_2011_code::text,2,'0')
                            AND c.district=LPAD(d.census_2011_code::text,3,'0')
                        )) AND LOWER(c.administrative_level) IN ('village','town') LIMIT 3
                """, selection.village_code, selection.state_code, selection.district_code)
            evidence_rows = []
            for row in rows:
                evidence = row['evidence']
                if isinstance(evidence, str):
                    evidence = json.loads(evidence)
                extra = evidence.get('extra_fields') or {}
                if isinstance(extra,str):
                    try:
                        extra=json.loads(extra)
                    except ValueError:
                        extra={}
                if not isinstance(extra,dict):
                    extra={}
                evidence_rows.append({**{key:extra[key] for key in ('area_sq_km','population_density_per_sq_km') if key in extra},**evidence})
            return evidence_rows
        except Exception:
            return []

    async def census_area(self, selection):
        flags={self.area_flag(row) for row in await self.census_evidence(selection)}-{None}
        return flags.pop() if len(flags)==1 else None

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
        if row.get('local_body_code') is not None:
            try:
                async with self.db.pool.acquire() as conn:
                    body=await conn.fetchrow('SELECT local_body_type_name FROM pri_local_bodies WHERE local_body_code=$1 AND state_code=$2',row['local_body_code'],selection.state_code)
                if body:
                    row['local_body_type_name']=body['local_body_type_name']
            except Exception:
                pass  # Some deployments have LGD village data without local-body data.
        locality={**row,'village_code':selection.village_code,'state_code':selection.state_code,'district_code':selection.district_code}
        records,amenities=await asyncio.gather(self.census_evidence(selection),fetch_area_amenities(locality))
        classification=classify_area(locality,records,amenities)
        is_rural=classification['is_rural']
        return {"state_code": selection.state_code, "district_code": selection.district_code,
                "block_code": selection.block_code, "village_code": selection.village_code,
                "state_name": row["state_name"], "district_name": row["district_name"],
                "block_name": row["development_block_name"], "village_name": row["village_name"],
                "is_rural": is_rural, "area_source": classification['source'], "area_classification":classification,
                "latitude": float(row["latitude"]) if row.get("latitude") is not None else None,
                "longitude": float(row["longitude"]) if row.get("longitude") is not None else None,
                "source": "lgd"}

    async def detect(self, gps):
        if gps.accuracy > 100000:
            raise ValueError("The device location is too imprecise. Try again outdoors or choose your business location below.")
        # Reverse geocoding supplies candidates only. Exact LGD joins own the hierarchy.
        source = 'gps_reverse_geocode_candidate'
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("https://nominatim.openstreetmap.org/reverse", params={
                    "lat": gps.latitude, "lon": gps.longitude, "format": "json", "addressdetails": 1, "accept-language":"en"},
                    headers={"User-Agent": "UdyamSaathi/2.0 location-verification"})
                response.raise_for_status()
                address = response.json().get("address", {})
        except (httpx.HTTPError, ValueError):
            address = {}
        postal = None
        if not address.get('state') or not any(address.get(key) for key in ('village','hamlet','town','suburb','city')):
            postal = postal_location_hint(gps.latitude,gps.longitude)
            if postal:
                address = {**postal,**{key:value for key,value in address.items() if value}}
                source = 'postal_directory_candidate'
        if not address:
            raise LocationUnavailable('The device position was received, but address lookup is unavailable. Retry or choose the business location.')
        # Display locality hints without a street address or raw device coordinates.
        # A uniquely resolved business candidate carries its GPS anchor separately.
        physical = {"accuracy": gps.accuracy, "state_name": address.get("state"),
                    "district_hint": address.get("district") or address.get("county") or address.get("state_district"),
                    "block_hint": address.get('county') or address.get('city_district') or address.get('municipality'),
                    "locality_hint": next((address[key] for key in ('village','hamlet','suburb','town','city','neighbourhood') if address.get(key)), None),
                    "approximate": gps.accuracy>1000 or source=='postal_directory_candidate', "source":source}
        if not self.db.pool:
            return physical, None
        locality_hints = list(dict.fromkeys(address[key] for key in ('village','hamlet','suburb','town','city','neighbourhood') if address.get(key)))
        district_hints = list(dict.fromkeys(re.sub(r'\s+(?:district|division)$','',address[key],flags=re.I).strip() for key in ('district','county','state_district') if address.get(key)))
        if not locality_hints or not district_hints:
            return physical, None
        try:
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch("""
                SELECT v.state_code, v.district_code, v.development_block_code, v.village_code, b.development_block_name
                FROM villages v JOIN districts d ON v.district_code=d.district_code
                JOIN states s ON d.state_code=s.state_code
                JOIN blocks b ON b.development_block_code=v.development_block_code AND b.district_code=d.district_code
                WHERE REGEXP_REPLACE(LOWER(s.state_name),'[^a-z0-9]','','g')=$1
                  AND REGEXP_REPLACE(LOWER(d.district_name),'[^a-z0-9]','','g')=ANY($2::text[])
                  AND REGEXP_REPLACE(LOWER(v.village_name),'[^a-z0-9]','','g')=ANY($3::text[]) LIMIT 50
                """, place_name(address.get("state", "")), [place_name(name) for name in district_hints], [place_name(name) for name in locality_hints])
        except Exception:
            physical['directory_unavailable'] = True
            return physical, None
        if len(rows)>=50:
            return physical,None
        # Multiple identical join rows are not independent locality matches.
        rows = list({(row['state_code'],row['district_code'],row['development_block_code'],row['village_code']):row for row in rows}.values())
        if len(rows)>1:
            block_hints={place_name(address[key]) for key in ('county','city_district','municipality','suburb') if address.get(key)}
            narrowed=[row for row in rows if place_name(row.get('development_block_name')) in block_hints]
            if len(narrowed)==1:
                rows=narrowed
        if len(rows) != 1:
            return physical, None
        from app.models.onboarding import LocationSelection
        row = dict(rows[0])
        selection = LocationSelection(revision=gps.revision, state_code=row["state_code"],
                                      district_code=row["district_code"], block_code=row["development_block_code"],
                                      village_code=row["village_code"])
        selected = await self.select(selection)
        physical.update(state_name=selected['state_name'],district_hint=selected['district_name'],locality_hint=selected['village_name'])
        physical['resolved_codes'] = {key:selected[key] for key in ('state_code','district_code','block_code','village_code')}
        selected['detection_source'] = source
        selected['approximate'] = physical['approximate']
        selected.update(latitude=gps.latitude,longitude=gps.longitude,coordinate_source='device_gps')
        return physical, selected
