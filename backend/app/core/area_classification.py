"""Automatic, explainable village classification; development != scheme status."""
from __future__ import annotations

import math
import re
import time
import httpx

POLICY = 'village_development_v1'
_CACHE = {}


def normalized(value):
    return re.sub(r'[^\w]', '', str(value or '').casefold())


def number(value):
    try:
        result = float(str(value).replace(',', ''))
        return result if math.isfinite(result) and result >= 0 else None
    except (ValueError, TypeError):
        return None


def official_area_flag(row):
    flag = row.get('is_rural')
    if isinstance(flag, bool):
        return flag
    if str(flag).lower() in ('true', 'false'):
        return str(flag).lower() == 'true'
    for key in ('town_rural_urban','rural_urban','area_classification','residence','tru','TRU','area_type','administrative_level'):
        value = str(row.get(key) or '').strip().lower()
        if value in ('rural','r','village'):
            return True
        if value in ('urban','u','town','census town','statutory town'):
            return False
    return None


def development_profile(census, amenities):
    """Application planning score, not a declaration of Census/PMEGP status."""
    population = number(census.get('total_population'))
    density = number(census.get('population_density_per_sq_km'))
    area = number(census.get('area_sq_km'))
    if density is None and population is not None and area:
        density = population / area
    workers = number(census.get('main_workers'))
    cultivators = number(census.get('main_cultivators'))
    labourers = number(census.get('main_agri_labourers'))
    non_agri = None
    if workers and cultivators is not None and labourers is not None and cultivators + labourers <= workers:
        non_agri = 100 * (workers-cultivators-labourers) / workers
    observed = amenities.get('indicators', {}) if amenities.get('available') else {}
    services = [value for key,value in observed.items() if key != 'power_hours' and isinstance(value,bool)]
    power = number(observed.get('power_hours'))
    if power is not None:
        services.append(power >= 18)
    service_coverage = len(services)
    present = sum(services)
    groups = {
        'population':None if population is None else 2 if population>=20000 else 1 if population>=5000 else 0,
        'density':None if density is None else 2 if density>=1500 else 1 if density>=400 else 0,
        'non_agricultural_work':None if non_agri is None else 2 if non_agri>=75 else 1 if non_agri>=50 else 0,
        'amenities':None if service_coverage<3 else 2 if present>=4 else 1 if present>=3 else 0,
    }
    sufficient = population is not None and sum(value is not None for value in groups.values()) >= 3
    score = sum(value for value in groups.values() if value is not None)
    label = ('Urban' if score>=6 else 'Semi-urban' if score>=3 else 'Rural') if sufficient else 'Insufficient data'
    return {'label':label,'basis':'estimated_development_profile','policy':POLICY,'score':score if sufficient else None,
        'factor_scores':groups,'population':population,'population_year':2011 if population is not None else None,
        'density_per_sq_km':round(density,2) if density is not None else None,
        'non_agricultural_main_workers_percent':round(non_agri,2) if non_agri is not None else None,
        'workforce_denominator':'all main workers; not the Census male-main-worker criterion',
        'amenities_observed':service_coverage,'amenities_present':present,
        'missing_factors':[key for key,value in groups.items() if value is None]}


def classify_area(locality, records, amenities):
    # A municipal notification / gram panchayat is administrative evidence;
    # a bank, road, high population or broadband connection is not.
    body = normalized(locality.get('local_body_type_name'))
    rural_bodies = {'villagepanchayat','grampanchayat','gramapanchayat'}
    urban_bodies = {'municipality','municipalcouncil','municipalcorporation','nagarpanchayat','cantonmentboard','notifiedtownareacommittee','townpanchayat'}
    flag, source = None, 'classification_unavailable'
    if body in rural_bodies | urban_bodies:
        flag,source = body in rural_bodies,'lgd_local_body'
    elif official_area_flag(locality) is not None:
        flag,source = official_area_flag(locality),'lgd'
    else:
        flags = {official_area_flag(row) for row in records} - {None}
        if len(flags)==1:
            flag,source = flags.pop(),'official_census_code_match'
    # Never add together Total/Rural/Urban rows or use district catchment defaults.
    census = records[0] if len(records)==1 else {}
    if len(records)>1:
        totals = [row for row in records if str(row.get('town_rural_urban','')).casefold()=='total']
        if len(totals)==1:
            census=totals[0]
    profile = development_profile(census,amenities)
    return {'is_rural':flag,'label':('Rural' if flag else 'Urban') if flag is not None else 'Not established',
        'source':source,'automatic':True,'official_status_available':flag is not None,
        'local_body_type':locality.get('local_body_type_name'),
        'development_profile':profile,'amenities':amenities,
        'reason':'Official administrative/census status determines the scheme area category; measured village indicators describe its development profile.'}


def parse_amenity_record(record):
    """Unknown indicators stay unknown; absence never becomes a default True."""
    indicators = {}
    keys = {
        'road':['all_weather_road__status_a_1__na_2__','black_topped__pucca__road__status_a_1__na_2__'],
        'banking':['atm__status_a_1__na_2__','commercial_bank__status_a_1__na_2__','cooperative_bank__status_a_1__na_2__'],
        'internet':['internet_cafes___common_service_centre__csc___status_a_1__na_2__'],
        'market_or_storage':['mandis_regular_market__status_a_1__na_2__','weekly_haat__status_a_1__na_2__','agricultural_marketing_society__status_a_1__na_2__'],
    }
    for name,aliases in keys.items():
        values=[str(record[key]).strip() for key in aliases if record.get(key) is not None]
        indicators[name]=True if '1' in values else False if values and all(value=='2' for value in values) else None
    power = record.get('power_supply_for_commercial_use_summer__april_sept___per_day__in_hours_')
    power = number(power)
    indicators['power_hours']=power if power is not None and power<=24 else None
    return indicators


def matches_village(record, locality):
    if not isinstance(record,dict):
        return False
    code=record.get('lgd_village_code') or record.get('village_code')
    state=record.get('state_name');district=record.get('district_name')
    if state and normalized(state)!=normalized(locality['state_name']):
        return False
    if district and normalized(district)!=normalized(locality['district_name']):
        return False
    if code is not None:
        return str(code)==str(locality['village_code'])
    block=record.get('development_block_name') or record.get('block_name')
    expected_block=locality.get('development_block_name') or locality.get('block_name')
    return bool(state and district and block and expected_block and normalized(block)==normalized(expected_block)
        and normalized(record.get('village_name'))==normalized(locality['village_name']))


async def fetch_area_amenities(locality):
    from app.config import settings
    from app.core.amenities_client import _get_district_resource_map
    unavailable={'available':False,'source':'unavailable','indicators':{}}
    if not settings.DATA_GOV_IN_API_KEY:
        return unavailable
    resources=_get_district_resource_map()
    resource=next((value for name,value in resources.items() if normalized(name)==normalized(locality['district_name'])),None)
    if not resource:
        return unavailable
    key=(locality['state_code'],locality['district_code'],locality['village_code'],resource)
    cached=_CACHE.get(key)
    if cached and time.monotonic()-cached[0]<86400:
        return cached[1]
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response=await client.get(f'https://api.data.gov.in/resource/{resource}',params={
                'api-key':settings.DATA_GOV_IN_API_KEY,'format':'json','limit':2,'filters[village_name]':locality['village_name']})
            response.raise_for_status()
            payload=response.json()
            if not isinstance(payload,dict) or not isinstance(payload.get('records'),list):
                return unavailable
            records=payload['records']
        matches=[record for record in records if matches_village(record,locality)]
        # Ambiguous rows and unfiltered district fallbacks are never village evidence.
        if len(matches)!=1:
            return unavailable
        indicators=parse_amenity_record(matches[0])
        result={'available':any(value is not None for value in indicators.values()),'source':'data_gov_in_exact_village',
            'village_code':locality['village_code'],'indicators':indicators}
        if result['available']:
            if len(_CACHE)>=512:
                _CACHE.pop(next(iter(_CACHE)))
            _CACHE[key]=(time.monotonic(),result)
        return result
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return unavailable
