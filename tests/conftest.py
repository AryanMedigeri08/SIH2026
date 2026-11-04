import sys
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR), str(BACKEND_DIR / 'app' / 'core')]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(autouse=True)
def local_test_auth(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "ALLOW_TEST_AUTH", True)


@pytest.fixture(autouse=True)
def offline_classification_amenities(monkeypatch):
    from app.core import onboarding_location
    async def unavailable(_):
        return {'available':False,'source':'unavailable','indicators':{}}
    monkeypatch.setattr(onboarding_location,'fetch_area_amenities',unavailable)
