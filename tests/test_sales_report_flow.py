import asyncio
import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/app/core"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.models.schemas import UserInput, ProjectCreate, ProjectModel
from app.core.sales_forecast_report import forecast_html, forecast_markdown
from app.core.sales_forecast import ForecastPlan, calculate_forecast
from test_sales_forecast import plan_dict, payload


def input_data(mode="estimate"):
    return UserInput(state_name="Karnataka", district_name="Test", village_name="Test",
                     project_cost=2_000_000, annual_turnover_estimate=900_000, sales_forecast_mode=mode)


@pytest.fixture
def pipeline(monkeypatch):
    from app.routers import feasibility as f
    from app.core.udyam.geography.gazetteer import Gazetteer
    monkeypatch.setattr(Gazetteer, "__init__", lambda self: None)
    monkeypatch.setattr(Gazetteer, "resolve_locality_coords", lambda *a, **k: None)
    monkeypatch.setattr(Gazetteer, "get_district_centroid", lambda *a, **k: None)
    async def census(**_): return dict(base_population_2011=5000, district_population_2011=1_000_000, provenance="regional_baseline")
    async def msme(**_): return dict(total_msme=1000, provenance="state_baseline")
    async def cpi(*_): return 4.85
    async def cpi_evidence(*_): return dict(value=4.85, status="fallback")
    async def weather(*_): return .2
    async def registered(*_): return dict(status="unavailable")
    monkeypatch.setattr(f.db_manager, "get_census_demographics", census)
    monkeypatch.setattr(f.db_manager, "get_district_msme_stats", msme)
    monkeypatch.setattr(f.db_manager, "get_state_cpi_inflation", cpi)
    monkeypatch.setattr(f.db_manager, "get_state_cpi_evidence", cpi_evidence)
    monkeypatch.setattr(f.db_manager, "get_weather_risk_score", weather)
    monkeypatch.setattr(f, "registered_market_context", registered)
    amenities = SimpleNamespace(infrastructure_score=7, to_dict=lambda: {"provenance": "regional_baseline"})
    monkeypatch.setattr(f, "fetch_village_amenities", lambda **_: amenities)
    ml = dict(verdict="SUITABLE", confidence_pct=75, is_fallback=True, top_positive_factors=[], top_risk_factors=[])
    monkeypatch.setattr(f, "predict_viability", lambda _: SimpleNamespace(**ml, to_dict=lambda: ml))
    synth = dict(model_name="test", is_fallback=True, swot_matrix=None)
    monkeypatch.setattr(f, "generate_executive_synthesis", lambda *a, **k: SimpleNamespace(**synth, to_dict=lambda: synth))
    monkeypatch.setattr(f, "build_bank_dpr", lambda **_: SimpleNamespace())
    return f


def test_validated_sales_feed_report_without_changing_budget_or_dscr_formula(pipeline, monkeypatch):
    forecast = calculate_forecast(ForecastPlan(**plan_dict()), payload())
    async def estimate(*_): return copy.deepcopy(forecast)
    monkeypatch.setattr(pipeline, "generate_sales_forecast", estimate)
    original = input_data()
    report, dpr = asyncio.run(pipeline._run_pipeline(original))
    assert original.annual_turnover_estimate == 900000  # no mutation of caller input
    assert report.input_parameters.annual_turnover_estimate == 720000
    assert report.input_parameters.project_cost == 2_000_000
    assert dpr.sales_forecast["annual_sales"]["base"] == 720000
    assert report.sales_forecast["entered_annual_sales_estimate"] == 900000
    dscr = report.financial_analysis["dscr"]
    assert dscr["dscr"] == pytest.approx((720000 * .30 / 12) / report.financial_analysis["amortization"]["monthly_emi"], abs=.0002)
    assert report.model_dump(mode="json")["sales_forecast"]["evidence_snapshot"]


def test_manual_reports_do_not_call_forecast(pipeline, monkeypatch):
    async def forbidden(*_): raise AssertionError("manual mode must not forecast")
    monkeypatch.setattr(pipeline, "generate_sales_forecast", forbidden)
    report, dpr = asyncio.run(pipeline._run_pipeline(input_data("manual")))
    assert report.sales_forecast is None and dpr.sales_forecast is None
    assert report.input_parameters.annual_turnover_estimate == 900000


def test_zero_sales_and_provider_failure_do_not_block_report(pipeline, monkeypatch):
    async def zero(*_):
        result = calculate_forecast(ForecastPlan(**plan_dict()), payload())
        result["annual_sales"]["base"] = 0
        return result
    monkeypatch.setattr(pipeline, "generate_sales_forecast", zero)
    report, _ = asyncio.run(pipeline._run_pipeline(input_data()))
    assert report.input_parameters.annual_turnover_estimate == 0
    async def broken(*_): raise ValueError("bad response")
    monkeypatch.setattr(pipeline, "generate_sales_forecast", broken)
    report, _ = asyncio.run(pipeline._run_pipeline(input_data()))
    assert report.sales_forecast["status"] == "manual_fallback"
    assert report.input_parameters.annual_turnover_estimate == 900000


def test_saved_settings_round_trip_and_historical_default():
    from app.routers.projects import _project_dict_to_user_input
    project = ProjectCreate(business_name="Milk delivery", business_category="manufacturing", sector="dairy",
        investment_amount=1000000, annual_turnover_estimate=0, state_name="Karnataka", district_name="Test",
        sales_forecast_mode="estimate", sales_context={"target_customers": "local households", "sales_channels": "delivery"},
        forecast_start_month="2027-01-01")
    restored = _project_dict_to_user_input(project.model_dump(mode="json"))
    assert restored.sales_forecast_mode == "estimate"
    assert restored.sales_context.sales_channels == "delivery"
    assert restored.forecast_start_month.isoformat() == "2027-01-01"
    assert input_data("manual").sales_forecast_mode == "manual"


def test_exports_escape_untrusted_model_text_and_include_audit():
    result = calculate_forecast(ForecastPlan(**plan_dict()), payload())
    result["warnings"].append('<script>alert("bad")</script>')
    html = forecast_html(result)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "720,000.00" in html and "scenario_assumption" in html
    assert "evidence_snapshot" in forecast_markdown(result)
    assert forecast_html(None) == ""


def test_accepted_sales_sync_to_project_record_without_writing_real_database(tmp_path):
    import sqlite3, json
    from app.database import DatabaseManager
    db = DatabaseManager()
    db.sqlite = sqlite3.connect(":memory:")
    db.sqlite.row_factory = sqlite3.Row
    db.sqlite.execute("CREATE TABLE projects (project_id TEXT, payload TEXT, updated_at TEXT)")
    record = {"project_id": "test", "user_id": "test", "annual_turnover_estimate": 900000}
    db.sqlite.execute("INSERT INTO projects VALUES (?, ?, ?)", ("test", json.dumps(record), "now"))
    analysis = {"report": {"sales_forecast": {"status": "provisional"},
                           "input_parameters": {"annual_turnover_estimate": 0}}}
    updated = asyncio.run(db.update_project_analysis("test", analysis))
    assert updated["annual_turnover_estimate"] == 0
    assert json.loads(db.sqlite.execute("SELECT payload FROM projects").fetchone()[0])["annual_turnover_estimate"] == 0
    db.sqlite.close()
