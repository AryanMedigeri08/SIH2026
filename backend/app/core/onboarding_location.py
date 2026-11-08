"""Resolve actual location records. Never choose a first-result substitute."""
import sqlite3
from pathlib import Path
import httpx
from fastapi import HTTPException
from app.database import db_manager


async def location_options(level, state='', district='', block=''):
    if db_manager.pool:
        async with db_manager.pool.acquire() as conn:
            if level == 'states':
                rows = await conn.fetch('SELECT state_name FROM states ORDER BY state_name')
            elif level == 'districts':
                rows = await conn.fetch('SELECT d.district_name FROM districts d JOIN states s ON s.state_code=d.state_code WHERE LOWER(s.state_name)=LOWER($1) ORDER BY d.district_name', state)
            elif level == 'blocks':
                rows = await conn.fetch('SELECT b.development_block_name AS block_name FROM blocks b JOIN districts d ON d.district_code=b.district_code JOIN states s ON s.state_code=d.state_code WHERE LOWER(s.state_name)=LOWER($1) AND LOWER(d.district_name)=LOWER($2) ORDER BY b.development_block_name', state, district)
            else:
                rows = await conn.fetch('SELECT v.village_name FROM villages v JOIN blocks b ON b.development_block_code=v.development_block_code JOIN districts d ON d.district_code=v.district_code JOIN states s ON s.state_code=d.state_code WHERE LOWER(s.state_name)=LOWER($1) AND LOWER(d.district_name)=LOWER($2) AND LOWER(b.development_block_name)=LOWER($3) ORDER BY v.village_name', state, district, block)
            key = {'states': 'state_name', 'districts': 'district_name', 'blocks': 'block_name', 'villages': 'village_name'}[level]
            return sorted({r[key] for r in rows if r[key]})
    # Real postal locality fallback: taluk is labelled as such in provenance.
    path = Path(__file__).parent / 'data/locality_master.sqlite3'
    if not path.exists():
        return []
    column = {'states': 'state', 'districts': 'district', 'blocks': 'taluk', 'villages': 'office_name'}[level]
    where, params = [], []
    for col, value in [('state', state), ('district', district), ('taluk', block)]:
        if value:
            where.append(f'LOWER({col})=LOWER(?)'); params.append(value)
    with sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True) as conn:
        rows = conn.execute(f"SELECT DISTINCT {column} FROM pincode_localities WHERE {column} IS NOT NULL AND {column}<>''" + (' AND ' + ' AND '.join(where) if where else '') + f' ORDER BY {column}', params).fetchall()
    return [r[0] for r in rows]


async def validate_location(location):
    parents = {}
    for level, field in [('states', 'state_name'), ('districts', 'district_name'), ('blocks', 'block_name'), ('villages', 'village_name')]:
        choices = await location_options(level, **parents)
        if getattr(location, field) not in choices:
            raise HTTPException(422, f'Choose a valid {field.replace("_name", "")} from the location list.')
        if field != 'village_name':
            parents[field.replace('_name', '')] = getattr(location, field)
    return {**location.model_dump(), 'is_rural': True,
            'classification_source': 'LGD village record' if db_manager.pool else 'Postal locality; existing rural planning default, unverified',
            'hierarchy_source': 'LGD' if db_manager.pool else 'Postal locality (block field is taluk)'}


async def resolve_gps(latitude, longitude):
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get('https://nominatim.openstreetmap.org/reverse',
            params={'lat': latitude, 'lon': longitude, 'format': 'json', 'addressdetails': 1, 'accept-language': 'en'},
            headers={'User-Agent': 'UdyamSaathi/2.0 onboarding location confirmation'})
        response.raise_for_status()
    address = response.json().get('address', {})
    hints = {
        'state_name': [address.get('state')],
        'district_name': [address.get('state_district'), address.get('district'), address.get('county')],
        'block_name': [address.get('county'), address.get('subdistrict'), address.get('municipality')],
        'village_name': [address.get('village'), address.get('hamlet'), address.get('town'), address.get('suburb')],
    }
    result = dict(latitude=latitude, longitude=longitude, source='gps', confirmed=False)
    parents = {}
    for level, field in [('states', 'state_name'), ('districts', 'district_name'), ('blocks', 'block_name'), ('villages', 'village_name')]:
        choices = await location_options(level, **parents)
        matches = [c for c in choices if c.casefold() in {str(v).casefold() for v in hints[field] if v}]
        if len(matches) != 1:
            break
        result[field] = matches[0]
        if field != 'village_name':
            parents[field.replace('_name', '')] = matches[0]
    return result
