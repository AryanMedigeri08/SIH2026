"""
feature_extractor.py — Phase 3, Udyam Saathi

Extracts and normalizes the 10-Dimensional ML Feature Vector (x0 ... x9)
mandated by udyam_saathi_master_blueprint.md §3 for the XGBoost Viability Classifier.

Feature Vector Specification:
    x0: dscr                           [0.0 - 5.0]   (financial_calculator.py)
    x1: subsidy_coverage_ratio         [0.0 - 1.0]   (subsidy / total_project_cost)
    x2: loan_to_income_ratio           [0.0 - 10.0]  (loan_principal / annual_turnover)
    x3: log_projected_population       [2.0 - 6.0]   (log10(projected_population))
    x4: msme_density_per_10k           [0.0 - 200.0] (registered MSMEs per 10k pop)
    x5: infrastructure_score           [0.0 - 10.0]  (composite: road+haat+power+bank+PDS)
    x6: cpi_inflation_pct              [-2.0 - 20.0] (state rural CPI inflation)
    x7: working_capital_months_buffer  [0.0 - 24.0]  (promoter margin / monthly WC outlay)
    x8: competition_intensity          [0.0 - 1.0]   (estimated competitors per 1k catchment)
    x9: weather_risk_score             [0.0 - 1.0]   (heavy rain days fraction from Open-Meteo)

Safe Defaults for Missing / Unresolved Data (matching Phase 1 & Phase 2 graceful degradation):
    infrastructure_score: 6.0
    cpi_inflation_pct: 5.0
    weather_risk_score: 0.20
    msme_density_per_10k: 8.0
    competition_intensity: 0.30
    working_capital_months_buffer: 3.0
"""

from __future__ import annotations
import math
from dataclasses import dataclass, asdict
from typing import Optional, Union, Any
import numpy as np

FEATURE_NAMES = [
    "dscr",
    "subsidy_coverage_ratio",
    "loan_to_income_ratio",
    "log_projected_population",
    "msme_density_per_10k",
    "infrastructure_score",
    "cpi_inflation_pct",
    "working_capital_months_buffer",
    "competition_intensity",
    "weather_risk_score",
]

# Safe median defaults when external datasets are partially unavailable
DEFAULT_FEATURE_VALUES = {
    "dscr": 1.33,
    "subsidy_coverage_ratio": 0.25,
    "loan_to_income_ratio": 1.20,
    "log_projected_population": 3.60,  # ~4,000 population
    "msme_density_per_10k": 8.0,
    "infrastructure_score": 6.0,
    "cpi_inflation_pct": 5.0,
    "working_capital_months_buffer": 3.0,
    "competition_intensity": 0.30,
    "weather_risk_score": 0.20,
}

# Domain bounds for clamping
FEATURE_BOUNDS = {
    "dscr": (0.0, 5.0),
    "subsidy_coverage_ratio": (0.0, 1.0),
    "loan_to_income_ratio": (0.0, 10.0),
    "log_projected_population": (1.0, 7.0),
    "msme_density_per_10k": (0.0, 200.0),
    "infrastructure_score": (0.0, 10.0),
    "cpi_inflation_pct": (-5.0, 25.0),
    "working_capital_months_buffer": (0.0, 24.0),
    "competition_intensity": (0.0, 1.0),
    "weather_risk_score": (0.0, 1.0),
}


@dataclass
class FeatureVector:
    dscr: float
    subsidy_coverage_ratio: float
    loan_to_income_ratio: float
    log_projected_population: float
    msme_density_per_10k: float
    infrastructure_score: float
    cpi_inflation_pct: float
    working_capital_months_buffer: float
    competition_intensity: float
    weather_risk_score: float

    def to_array(self) -> np.ndarray:
        """Returns 1D numpy array of shape (10,)"""
        return np.array([
            self.dscr,
            self.subsidy_coverage_ratio,
            self.loan_to_income_ratio,
            self.log_projected_population,
            self.msme_density_per_10k,
            self.infrastructure_score,
            self.cpi_inflation_pct,
            self.working_capital_months_buffer,
            self.competition_intensity,
            self.weather_risk_score,
        ], dtype=np.float64)

    def to_dict(self) -> dict[str, float]:
        return {k: round(float(v), 4) for k, v in asdict(self).items()}

    def to_clamped_array(self) -> np.ndarray:
        """Returns clamped array matching feature bounds"""
        raw = self.to_array()
        clamped = []
        for i, name in enumerate(FEATURE_NAMES):
            low, high = FEATURE_BOUNDS[name]
            clamped.append(float(np.clip(raw[i], low, high)))
        return np.array(clamped, dtype=np.float64)


def extract_features(
    dscr: Optional[float] = None,
    subsidy_grant_amount: Optional[float] = None,
    total_project_cost: Optional[float] = None,
    loan_principal: Optional[float] = None,
    annual_turnover: Optional[float] = None,
    projected_population: Optional[Union[int, float]] = None,
    msme_density_per_10k: Optional[float] = None,
    infrastructure_score: Optional[float] = None,
    cpi_inflation_pct: Optional[float] = None,
    working_capital_months_buffer: Optional[float] = None,
    competition_intensity: Optional[float] = None,
    weather_risk_score: Optional[float] = None,
    # Direct ratios if already computed upstream:
    subsidy_coverage_ratio: Optional[float] = None,
    loan_to_income_ratio: Optional[float] = None,
    log_projected_population: Optional[float] = None,
) -> FeatureVector:
    """
    Extracts and validates the 10-D feature vector from raw business data or computed metrics.
    Gracefully applies domain-grounded median fallbacks for any missing optional parameter.
    """
    # x0: DSCR
    val_dscr = dscr if dscr is not None else DEFAULT_FEATURE_VALUES["dscr"]

    # x1: Subsidy Coverage Ratio
    if subsidy_coverage_ratio is not None:
        val_sub = subsidy_coverage_ratio
    elif subsidy_grant_amount is not None and total_project_cost is not None and total_project_cost > 0:
        val_sub = subsidy_grant_amount / total_project_cost
    else:
        val_sub = DEFAULT_FEATURE_VALUES["subsidy_coverage_ratio"]

    # x2: Loan to Income Ratio
    if loan_to_income_ratio is not None:
        val_lti = loan_to_income_ratio
    elif loan_principal is not None and annual_turnover is not None and annual_turnover > 0:
        val_lti = loan_principal / annual_turnover
    else:
        val_lti = DEFAULT_FEATURE_VALUES["loan_to_income_ratio"]

    # x3: Log Projected Population
    if log_projected_population is not None:
        val_log_pop = log_projected_population
    elif projected_population is not None and projected_population > 0:
        val_log_pop = math.log10(max(float(projected_population), 1.0))
    else:
        val_log_pop = DEFAULT_FEATURE_VALUES["log_projected_population"]

    # x4: MSME Density per 10k
    val_msme = msme_density_per_10k if msme_density_per_10k is not None else DEFAULT_FEATURE_VALUES["msme_density_per_10k"]

    # x5: Infrastructure Score (0-10)
    val_infra = infrastructure_score if infrastructure_score is not None else DEFAULT_FEATURE_VALUES["infrastructure_score"]

    # x6: CPI Inflation %
    val_cpi = cpi_inflation_pct if cpi_inflation_pct is not None else DEFAULT_FEATURE_VALUES["cpi_inflation_pct"]

    # x7: Working Capital Months Buffer
    val_wc_buf = working_capital_months_buffer if working_capital_months_buffer is not None else DEFAULT_FEATURE_VALUES["working_capital_months_buffer"]

    # x8: Competition Intensity (0-1)
    val_comp = competition_intensity if competition_intensity is not None else DEFAULT_FEATURE_VALUES["competition_intensity"]

    # x9: Weather Risk Score (0-1)
    val_weather = weather_risk_score if weather_risk_score is not None else DEFAULT_FEATURE_VALUES["weather_risk_score"]

    # Construct and clamp within domain ranges
    raw_vector = FeatureVector(
        dscr=float(val_dscr),
        subsidy_coverage_ratio=float(val_sub),
        loan_to_income_ratio=float(val_lti),
        log_projected_population=float(val_log_pop),
        msme_density_per_10k=float(val_msme),
        infrastructure_score=float(val_infra),
        cpi_inflation_pct=float(val_cpi),
        working_capital_months_buffer=float(val_wc_buf),
        competition_intensity=float(val_comp),
        weather_risk_score=float(val_weather),
    )

    # Return clamped vector for numerical safety
    clamped_arr = raw_vector.to_clamped_array()
    return FeatureVector(
        dscr=float(clamped_arr[0]),
        subsidy_coverage_ratio=float(clamped_arr[1]),
        loan_to_income_ratio=float(clamped_arr[2]),
        log_projected_population=float(clamped_arr[3]),
        msme_density_per_10k=float(clamped_arr[4]),
        infrastructure_score=float(clamped_arr[5]),
        cpi_inflation_pct=float(clamped_arr[6]),
        working_capital_months_buffer=float(clamped_arr[7]),
        competition_intensity=float(clamped_arr[8]),
        weather_risk_score=float(clamped_arr[9]),
    )


def extract_features_from_pipeline_objects(
    pop_proj: Any,
    tam_est: Any,
    msme_dens: Any,
    comp_int: Any,
    top_scheme: Any,
    amort_res: Any,
    dscr_res: Any,
    wc_res: Any,
    project_cost: float,
    annual_turnover: float,
    infrastructure_score: float,
    cpi_inflation_pct: float,
    weather_risk_score: float,
    promoter_margin_amount: float,
) -> FeatureVector:
    """
    Direct helper to extract features when chaining Phase 2 module outputs.
    """
    subsidy_ratio = top_scheme.subsidy_grant_amount / project_cost if project_cost > 0 else 0.0
    loan_to_inc = amort_res.principal / annual_turnover if annual_turnover > 0 else 1.0
    wc_buf = promoter_margin_amount / wc_res.monthly_working_capital_outlay if wc_res.monthly_working_capital_outlay > 0 else 0.0

    return extract_features(
        dscr=dscr_res.dscr,
        subsidy_coverage_ratio=subsidy_ratio,
        loan_to_income_ratio=loan_to_inc,
        projected_population=pop_proj.projected_population,
        msme_density_per_10k=msme_dens.msme_density_per_10k if msme_dens.data_available else None,
        infrastructure_score=infrastructure_score,
        cpi_inflation_pct=cpi_inflation_pct,
        working_capital_months_buffer=wc_buf,
        competition_intensity=comp_int.competition_intensity_normalized,
        weather_risk_score=weather_risk_score,
    )
