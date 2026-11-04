"""Automatic village classification with honest data provenance and scheme status."""
import asyncio
from copy import deepcopy

import httpx
import pytest

from app.core import area_classification as area

LOCALITY={'state_name':'Maharashtra','district_name':'Pune','state_code':27,'district_code':490,
    'village_code':456,'village_name':'Example','development_block_name':'Haveli'}
AMENITIES={'available':True,'source':'data_gov_in_exact_village','indicators':{
    'road':True,'banking':True,'internet':True,'market_or_storage':True,'power_hours':22}}
CENSUS={'town_rural_urban':'Rural','total_population':25000,'main_workers':10000,
    'main_cultivators':500,'main_agri_labourers':500,'population_density_per_sq_km':1600}


def test_large_well_connected_village_gets_urban_profile_without_changing_official_rural_status():
    result=area.classify_area(LOCALITY,[CENSUS],AMENITIES)
    assert result['is_rural'] is True and result['automatic'] is True
    assert result['development_profile']['label']=='Urban'
    assert result['development_profile']['population']==25000
    assert result['development_profile']['non_agricultural_main_workers_percent']==90
    assert result['source']=='official_census_code_match'


def test_local_government_status_wins_over_old_census_and_high_or_low_population():
    result=area.classify_area({**LOCALITY,'local_body_type_name':'Municipal Council'},[CENSUS],AMENITIES)
    assert result['is_rural'] is False and result['source']=='lgd_local_body'
    result=area.classify_area({**LOCALITY,'local_body_type_name':'Gram Panchayat'},[{**CENSUS,'town_rural_urban':'Urban'}],AMENITIES)
    assert result['is_rural'] is True
    assert area.classify_area({**LOCALITY,'local_body_type_name':'Nagar Panchayat'},[],AMENITIES)['is_rural'] is False


@pytest.mark.parametrize('population,density,workers,agri,label',[
    (1200,100,500,450,'Rural'),(7000,500,1000,400,'Semi-urban'),(30000,1800,10000,500,'Urban')])
def test_population_density_workforce_and_observed_services_produce_deterministic_profile(population,density,workers,agri,label):
    census={'total_population':population,'population_density_per_sq_km':density,'main_workers':workers,
        'main_cultivators':agri,'main_agri_labourers':0}
    result=area.development_profile(census,AMENITIES)
    assert result['label']==label and result['policy']==area.POLICY


def test_amenities_change_development_profile_when_demographic_factors_are_unchanged():
    census={'total_population':7000,'main_workers':1000,'main_cultivators':400,'main_agri_labourers':0}
    low={'available':True,'indicators':{'road':False,'banking':False,'internet':False,'market_or_storage':False,'power_hours':8}}
    assert area.development_profile(census,low)['label']=='Rural'
    assert area.development_profile(census,AMENITIES)['label']=='Semi-urban'


def test_incomplete_or_invalid_indicators_never_become_invented_classification():
    unavailable={'available':False,'source':'regional_baseline','indicators':AMENITIES['indicators']}
    result=area.classify_area(LOCALITY,[{'total_population':10000}],unavailable)
    assert result['is_rural'] is None and not result['official_status_available']
    assert result['development_profile']['label']=='Insufficient data'
    assert area.development_profile({'total_population':float('nan')},AMENITIES)['population'] is None
    assert area.development_profile({**CENSUS,'main_cultivators':20000},AMENITIES)['non_agricultural_main_workers_percent'] is None
    assert area.parse_amenity_record({})=={'road':None,'banking':None,'internet':None,'market_or_storage':None,'power_hours':None}


def test_total_rows_are_not_added_together_and_conflicts_do_not_become_official_status():
    result=area.classify_area(LOCALITY,[{**CENSUS,'town_rural_urban':'Total'},CENSUS],AMENITIES)
    assert result['development_profile']['population']==25000
    conflicting=area.classify_area(LOCALITY,[CENSUS,{**CENSUS,'town_rural_urban':'Urban'}],AMENITIES)
    assert conflicting['is_rural'] is None and conflicting['development_profile']['population'] is None


def test_amenity_identity_requires_exact_code_or_full_block_hierarchy():
    assert area.matches_village({'village_code':456},LOCALITY)
    assert not area.matches_village({'village_code':999,'village_name':'Example'},LOCALITY)
    assert not area.matches_village({'village_code':456,'state_name':'Karnataka'},LOCALITY)
    named={'state_name':'Maharashtra','district_name':'Pune','village_name':'Example'}
    assert not area.matches_village(named,LOCALITY)
    assert area.matches_village({**named,'block_name':'Haveli'},LOCALITY)


def test_live_amenity_reader_rejects_district_fallback_and_caches_only_observed_village_data(monkeypatch):
    from app.config import settings
    from app.core import amenities_client
    monkeypatch.setattr(settings,'DATA_GOV_IN_API_KEY','test-key')
    monkeypatch.setattr(amenities_client,'_get_district_resource_map',lambda:{'Pune':'test-resource'})
    area._CACHE.clear()
    calls=[]
    records=[{'village_code':999,'all_weather_road__status_a_1__na_2__':'1'}]
    def reply(request):
        calls.append(request.url.path)
        return httpx.Response(200,json={'records':records})
    client=httpx.AsyncClient
    monkeypatch.setattr(area.httpx,'AsyncClient',lambda **kwargs:client(transport=httpx.MockTransport(reply),**kwargs))
    assert not asyncio.run(area.fetch_area_amenities(LOCALITY))['available']
    records[:]=[{'village_code':456,'all_weather_road__status_a_1__na_2__':'1'}]
    result=asyncio.run(area.fetch_area_amenities(LOCALITY))
    assert result['available'] and result['indicators']['road'] is True
    assert result['indicators']['banking'] is None
    cached=asyncio.run(area.fetch_area_amenities(LOCALITY))
    assert cached==result and len(calls)==2
    area._CACHE.clear()
