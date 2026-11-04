"""Reference-branch address hints, real census schema and safe location recovery."""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_mira_onboarding import FakePool, LOC
from app.core import onboarding_location as module
from app.core.onboarding_location import OnboardingLocation
from app.models.onboarding import GPSRequest, LocationSelection


def run(coro): return asyncio.run(coro)


def reverse(monkeypatch,address=None,status=200):
    client=httpx.AsyncClient
    transport=httpx.MockTransport(lambda _:httpx.Response(status,json={'address':address or {}}))
    monkeypatch.setattr(module.httpx,'AsyncClient',lambda **kwargs:client(transport=transport,**kwargs))


def test_area_classifier_uses_actual_census_code_columns():
    class Connection:
        async def fetch(self,sql,*args):
            assert 'c.town_village' in sql and 'v.village_census_2011_code' in sql
            assert 's.census_2011_code' in sql and 'd.census_2011_code' in sql
            assert args==(456,27,490)
            return [{'evidence':{'town_rural_urban':'Urban','administrative_level':'Town'}}]
    service=OnboardingLocation(SimpleNamespace(pool=FakePool(Connection())))
    assert run(service.census_area(LocationSelection(revision=0,state_code=27,district_code=490,block_code=123,village_code=456))) is False


def test_city_suburb_and_county_hints_resolve_without_using_first_dropdown_row(monkeypatch):
    reverse(monkeypatch,{'state':'Maharashtra','state_district':'Pune Division','county':'Pune District','suburb':'Example'})
    class Connection:
        async def fetch(self,sql,*args):
            assert args==('maharashtra',['pune','pune'],['example']) or args==('maharashtra',['pune'],['example'])
            return [{'state_code':27,'district_code':490,'development_block_code':123,'village_code':456}]
        async def fetchrow(self,*_): return {**LOC,'development_block_name':'Haveli'}
    service=OnboardingLocation(SimpleNamespace(pool=FakePool(Connection())))
    physical,selected=run(service.detect(GPSRequest(revision=0,latitude=18.5,longitude=73.9,accuracy=5000)))
    assert selected['village_code']==456 and selected['latitude']==18.5
    assert physical['approximate'] is True and physical['resolved_codes']['block_code']==123
    assert 'latitude' not in physical


def test_postal_fallback_preserves_detected_hints_when_reverse_service_fails(monkeypatch):
    reverse(monkeypatch,status=503)
    monkeypatch.setattr(module,'postal_location_hint',lambda *_:{'state':'Maharashtra','district':'Pune','county':'Haveli','village':'Example'})
    physical,selected=run(OnboardingLocation(SimpleNamespace(pool=None)).detect(GPSRequest(revision=0,latitude=18.5,longitude=73.9,accuracy=50)))
    assert selected is None and physical['source']=='postal_directory_candidate'
    assert physical['district_hint']=='Pune' and physical['block_hint']=='Haveli'
    assert physical['approximate'] is True and 'village_code' not in physical


def test_directory_outage_keeps_address_visible(monkeypatch):
    reverse(monkeypatch,{'state':'Maharashtra','district':'Pune','village':'Example'})
    class Connection:
        async def fetch(self,*_): raise RuntimeError('directory offline')
    physical,selected=run(OnboardingLocation(SimpleNamespace(pool=FakePool(Connection()))).detect(GPSRequest(revision=0,latitude=18.5,longitude=73.9,accuracy=50)))
    assert selected is None and physical['district_hint']=='Pune' and physical['directory_unavailable'] is True


def test_dashboard_lookup_is_authenticated_read_only_and_not_cached(monkeypatch):
    from app.routers import locations
    from app.core.auth_dependency import get_current_user,AuthenticatedUser
    class Service:
        def __init__(self,_): pass
        async def detect(self,_): return {'state_name':'Maharashtra','district_hint':'Pune'},dict(LOC)
    monkeypatch.setattr(module,'OnboardingLocation',Service)
    app=FastAPI();app.include_router(locations.router)
    with TestClient(app) as client:
        payload={'revision':0,'latitude':18.5,'longitude':73.9,'accuracy':50}
        assert client.post('/locations/detect',json=payload).status_code==401
        app.dependency_overrides[get_current_user]=lambda:AuthenticatedUser(uid='location-test')
        result=client.post('/locations/detect',json=payload)
        assert result.status_code==200 and result.headers['cache-control']=='no-store'
        assert result.json()['location']['village_code']==456
