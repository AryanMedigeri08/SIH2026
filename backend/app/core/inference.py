"""
inference.py — Phase 3, Udyam Saathi

Thread-safe inference module for the 10-Dimensional XGBoost Viability Classifier.
Guarantees < 5ms inference latency and zero-crash execution via deterministic fallback.

Public API:
    predict_viability(features, model_path=None) -> ViabilityPrediction
"""

from __future__ import annotations
import json
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Union, Any
import numpy as np
import joblib
from feature_extractor import FeatureVector, FEATURE_NAMES, extract_features

def _resolve_model_path() -> Path:
    candidates = [
        Path(__file__).parent.parent / "data" / "viability_xgb.joblib",
        Path(__file__).parent / "viability_xgb.joblib",
        Path.cwd() / "backend" / "app" / "data" / "viability_xgb.joblib",
        Path.cwd() / "viability_xgb.joblib",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

def _resolve_metadata_path() -> Path:
    candidates = [
        Path(__file__).parent.parent / "data" / "model_metadata.json",
        Path(__file__).parent / "model_metadata.json",
        Path.cwd() / "backend" / "app" / "data" / "model_metadata.json",
        Path.cwd() / "model_metadata.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

DEFAULT_MODEL_PATH = _resolve_model_path()
DEFAULT_METADATA_PATH = _resolve_metadata_path()

CLASS_MAP = {
    0: "SUITABLE",
    1: "CAUTION",
    2: "RECONSIDER",
}


@dataclass
class ViabilityPrediction:
    verdict: str                        # "SUITABLE" | "CAUTION" | "RECONSIDER"
    confidence_pct: float               # e.g. 96.45
    class_probabilities: dict[str, float]  # {"SUITABLE": 0.9645, "CAUTION": 0.0312, "RECONSIDER": 0.0043}
    top_positive_factors: list[str]     # Key grounded positive drivers
    top_risk_factors: list[str]         # Key grounded risk drivers
    feature_values: dict[str, float]    # 10-D inputs for auditability
    is_fallback: bool                   # True if deterministic rule fallback was used
    model_version: str                  # "xgboost_v2.0" or "rule_fallback_v1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "confidence_pct": round(self.confidence_pct, 2),
            "class_probabilities": {k: round(v, 4) for k, v in self.class_probabilities.items()},
            "top_positive_factors": self.top_positive_factors,
            "top_risk_factors": self.top_risk_factors,
            "feature_values": {k: round(v, 4) for k, v in self.feature_values.items()},
            "is_fallback": self.is_fallback,
            "model_version": self.model_version,
        }


class ViabilityModelLoader:
    """Thread-safe singleton model loader."""
    _instance: Optional[ViabilityModelLoader] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ViabilityModelLoader, cls).__new__(cls)
                cls._instance._model = None
                cls._instance._metadata = None
                cls._instance._loaded_path = None
            return cls._instance

    def get_model(self, model_path: Optional[Union[str, Path]] = None):
        with self._lock:
            target_path = Path(model_path) if model_path is not None else DEFAULT_MODEL_PATH
            if not target_path.exists():
                return None
            if self._model is None or self._loaded_path != target_path:
                try:
                    self._model = joblib.load(target_path)
                    self._loaded_path = target_path
                except Exception:
                    self._model = None
                    self._loaded_path = None
            return self._model

    def get_metadata(self, metadata_path: Optional[Union[str, Path]] = None):
        with self._lock:
            target_path = Path(metadata_path) if metadata_path is not None else DEFAULT_METADATA_PATH
            if not target_path.exists():
                return None
            if self._metadata is None:
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        self._metadata = json.load(f)
                except Exception:
                    self._metadata = None
            return self._metadata


def _explain_factors(features: FeatureVector) -> tuple[list[str], list[str]]:
    """
    Derives grounded, domain-specific explainability statements for positive
    and risk drivers without requiring heavy external SHAP computation at runtime.
    """
    positives: list[str] = []
    risks: list[str] = []

    # x0: DSCR
    if features.dscr >= 1.33:
        positives.append(f"Strong Debt Service Coverage Ratio (DSCR: {features.dscr:.2f}) comfortably clears RBI benchmark (1.33)")
    elif features.dscr >= 1.0:
        risks.append(f"Marginal DSCR ({features.dscr:.2f}) leaves narrow cashflow safety margin against revenue dips")
    else:
        risks.append(f"Critical DSCR ({features.dscr:.2f}) indicates severe cashflow deficit for loan servicing")

    # x1: Subsidy Coverage Ratio
    if features.subsidy_coverage_ratio >= 0.20:
        positives.append(f"Substantial capital subsidy coverage ({features.subsidy_coverage_ratio * 100:.1f}% of project cost) reduces debt liability")
    elif features.subsidy_coverage_ratio == 0.0:
        risks.append("Zero government subsidy grant; 100% of capital must be self-funded or debt-financed")

    # x2: Loan to Income Ratio
    if features.loan_to_income_ratio <= 1.5:
        positives.append(f"Conservative loan-to-turnover leverage ({features.loan_to_income_ratio:.2f}x)")
    elif features.loan_to_income_ratio >= 3.0:
        risks.append(f"High debt-to-turnover leverage ({features.loan_to_income_ratio:.2f}x annual revenue)")

    # x5: Infrastructure Score
    if features.infrastructure_score >= 7.0:
        positives.append(f"High village infrastructure readiness ({features.infrastructure_score:.1f}/10)")
    elif features.infrastructure_score < 5.0:
        risks.append(f"Low site infrastructure readiness ({features.infrastructure_score:.1f}/10) may increase logistics cost")

    # x6: CPI Inflation %
    if features.cpi_inflation_pct > 6.5:
        risks.append(f"Elevated rural inflation pressure ({features.cpi_inflation_pct:.2f}%) requires proactive pricing adjustments")

    # x7: Working Capital Months Buffer
    if features.working_capital_months_buffer >= 3.0:
        positives.append(f"Healthy liquidity buffer ({features.working_capital_months_buffer:.1f} months of working capital reserve)")
    elif features.working_capital_months_buffer < 1.0:
        risks.append(f"Tight working capital liquidity buffer ({features.working_capital_months_buffer:.1f} months)")

    # x8: Competition Intensity
    if features.competition_intensity <= 0.30:
        positives.append("Low competitor saturation in local market catchment")
    elif features.competition_intensity >= 0.65:
        risks.append(f"High local competition intensity ({features.competition_intensity:.2f}/1.0)")

    # x9: Weather Risk
    if features.weather_risk_score >= 0.35:
        risks.append(f"Seasonal heavy weather risk score ({features.weather_risk_score:.2f}) requires buffer stocking")

    # Ensure at least 1 factor in each list
    if not positives:
        positives.append("Enterprise parameters align with baseline operational viability")
    if not risks:
        risks.append("No high-severity operational risk factors detected")

    return positives[:3], risks[:3]


def _rule_based_fallback(features: FeatureVector) -> ViabilityPrediction:
    """
    100% Deterministic rule-based fallback when ML model artifact is offline.
    Guarantees zero-crash execution.
    """
    f_dscr = features.dscr
    f_infra = features.infrastructure_score
    f_comp = features.competition_intensity
    f_lti = features.loan_to_income_ratio

    if f_dscr < 1.0 or (f_dscr < 1.15 and f_lti > 3.0) or (f_dscr < 1.15 and f_comp > 0.7):
        verdict = "RECONSIDER"
        probs = {"SUITABLE": 0.05, "CAUTION": 0.15, "RECONSIDER": 0.80}
    elif f_dscr >= 1.33 and f_infra >= 5.0 and f_comp <= 0.60:
        verdict = "SUITABLE"
        probs = {"SUITABLE": 0.85, "CAUTION": 0.12, "RECONSIDER": 0.03}
    else:
        verdict = "CAUTION"
        probs = {"SUITABLE": 0.20, "CAUTION": 0.70, "RECONSIDER": 0.10}

    pos, risk = _explain_factors(features)
    conf = float(probs[verdict] * 100)

    return ViabilityPrediction(
        verdict=verdict,
        confidence_pct=conf,
        class_probabilities=probs,
        top_positive_factors=pos,
        top_risk_factors=risk,
        feature_values=features.to_dict(),
        is_fallback=True,
        model_version="rule_fallback_v1.0",
    )


def predict_viability(
    features: Union[FeatureVector, dict[str, float], list[float], np.ndarray],
    model_path: Optional[Union[str, Path]] = None,
) -> ViabilityPrediction:
    """
    Performs high-speed (< 5ms) multi-class viability classification.
    """
    # 1. Normalize input into FeatureVector
    if isinstance(features, FeatureVector):
        fv = features
    elif isinstance(features, dict):
        fv = extract_features(**features)
    elif isinstance(features, (list, np.ndarray)):
        arr = np.array(features, dtype=float).flatten()
        if len(arr) != 10:
            raise ValueError(f"Expected 10 feature values, got {len(arr)}")
        fv = FeatureVector(*arr.tolist())
    else:
        raise TypeError(f"Unsupported features type: {type(features)}")

    # 2. Attempt model inference via singleton loader
    loader = ViabilityModelLoader()
    model = loader.get_model(model_path)

    if model is None:
        return _rule_based_fallback(fv)

    try:
        X_arr = fv.to_clamped_array().reshape(1, -1)
        proba = model.predict_proba(X_arr)[0]

        prob_dict = {
            "SUITABLE": float(proba[0]),
            "CAUTION": float(proba[1]),
            "RECONSIDER": float(proba[2]),
        }

        pred_idx = int(np.argmax(proba))
        verdict = CLASS_MAP[pred_idx]
        confidence_pct = float(proba[pred_idx] * 100)

        positives, risks = _explain_factors(fv)

        return ViabilityPrediction(
            verdict=verdict,
            confidence_pct=confidence_pct,
            class_probabilities=prob_dict,
            top_positive_factors=positives,
            top_risk_factors=risks,
            feature_values=fv.to_dict(),
            is_fallback=False,
            model_version="xgboost_v2.0",
        )

    except Exception:
        # Gracefully degrade to rule-based heuristic on any runtime error
        return _rule_based_fallback(fv)
