"""Regression tests for liquidity that remains after the project is funded."""

from pathlib import Path
from types import SimpleNamespace
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.feature_extractor import extract_features_from_pipeline_objects
from app.core.financial_calculator import scheme_promoter_contribution_rate


def _features(available_cash: float):
    return extract_features_from_pipeline_objects(
        pop_proj=SimpleNamespace(projected_population=20000),
        tam_est=SimpleNamespace(),
        msme_dens=SimpleNamespace(data_available=True, msme_density_per_10k=8.0),
        comp_int=SimpleNamespace(competition_intensity_normalized=0.3),
        top_scheme=SimpleNamespace(subsidy_grant_amount=100000),
        amort_res=SimpleNamespace(principal=500000),
        dscr_res=SimpleNamespace(dscr=1.5),
        wc_res=SimpleNamespace(monthly_working_capital_outlay=50000),
        project_cost=800000,
        annual_turnover=1000000,
        infrastructure_score=7,
        cpi_inflation_pct=5,
        weather_risk_score=0.2,
        available_cash_reserve=available_cash,
    )


def test_committed_project_cash_is_not_counted_as_liquidity():
    assert _features(0).working_capital_months_buffer == 0
    assert _features(100000).working_capital_months_buffer == 2
    assert _features(-50000).working_capital_months_buffer == 0


def test_minimum_contribution_comes_from_selected_scheme():
    assert scheme_promoter_contribution_rate("PMEGP", "general") == 0.10
    assert scheme_promoter_contribution_rate("PMEGP", "women") == 0.05
    assert scheme_promoter_contribution_rate("PMFME", "women") == 0.10
    assert scheme_promoter_contribution_rate("MUDRA_KISHORE", "general") == 0
    assert scheme_promoter_contribution_rate("UNKNOWN", "general") == 0
