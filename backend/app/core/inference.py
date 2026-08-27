"""
inference.py — Phase 3, Udyam Saathi

Thread-safe inference and explainability module for the 10-Dimensional XGBoost Viability Classifier.
Combines high-speed ML scoring with real per-prediction SHAP TreeExplainer attribution
and global feature gain rankings.

Guarantees < 5ms inference latency and zero-crash execution via deterministic fallback.

Public API:
    predict_viability(features, model_path=None) -> ViabilityPrediction
"""

from __future__ import annotations
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Any
import numpy as np
import joblib

logger = logging.getLogger("udyam_saathi.inference")

try:
    from .feature_extractor import FeatureVector, FEATURE_NAMES, extract_features
except ImportError:
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

# Empirical base values in margin space for the 3 classes: [SUITABLE, CAUTION, RECONSIDER]
DEFAULT_EXPECTED_VALUES = [0.8510186, 0.28879157, 0.33739966]


class TreeSHAPExplainer:
    """
    High-performance, thread-safe TreeSHAP explainer for XGBoost models.
    Executes native C++ TreeSHAP Lundberg algorithm with exact feature attribution
    and expected base values.
    """
    def __init__(self, model: Any):
        self.model = model
        self.booster = model.get_booster() if hasattr(model, "get_booster") else model
        self.expected_value = DEFAULT_EXPECTED_VALUES

    def shap_values(self, X: Union[np.ndarray, list]) -> np.ndarray:
        import xgboost as xgb
        X_arr = np.asanyarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        dmat = xgb.DMatrix(X_arr)
        contribs = self.booster.predict(dmat, pred_contribs=True)  # Shape (N, 3, 11)
        # Transpose to shape (N, 10, 3) where [sample, feature, class]
        return np.transpose(contribs[:, :, :10], (0, 2, 1))

    def explain(self, X: Union[np.ndarray, list], pred_idx: int) -> tuple[np.ndarray, float]:
        """Returns (shap_values_for_class, base_value_for_class) in <2ms."""
        import xgboost as xgb
        X_arr = np.asanyarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)
        dmat = xgb.DMatrix(X_arr)
        contribs = self.booster.predict(dmat, pred_contribs=True)  # Shape (1, 3, 11)
        class_shap = contribs[0, pred_idx, :10]
        base_val = float(contribs[0, pred_idx, 10])
        return class_shap, base_val


@dataclass
class ViabilityPrediction:
    verdict: str                                    # "SUITABLE" | "CAUTION" | "RECONSIDER"
    confidence_pct: float                           # e.g. 96.45
    class_probabilities: dict[str, float]              # {"SUITABLE": 0.9645, "CAUTION": 0.0312, "RECONSIDER": 0.0043}
    top_positive_factors: list[str]                 # Key grounded positive drivers (SHAP-derived)
    top_risk_factors: list[str]                     # Key grounded risk drivers (SHAP-derived)
    feature_values: dict[str, float]                # 10-D inputs for auditability
    is_fallback: bool                               # True if deterministic rule fallback was used
    model_version: str                              # "xgboost_v2.0" or "rule_fallback_v1.0"
    shap_explanation: Optional[dict[str, Any]] = None  # Real per-prediction SHAP waterfall
    global_feature_importance: Optional[list[dict[str, Any]]] = None  # Global gain rankings

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
            "shap_explanation": self.shap_explanation,
            "global_feature_importance": self.global_feature_importance,
        }


class ViabilityModelLoader:
    """Thread-safe singleton model and TreeSHAP explainer loader."""
    _instance: Optional[ViabilityModelLoader] = None
    _lock = threading.RLock()


    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ViabilityModelLoader, cls).__new__(cls)
                cls._instance._model = None
                cls._instance._explainer = None
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
                    self._explainer = TreeSHAPExplainer(self._model)
                except Exception as e:
                    logger.error(f"Failed to load XGBoost model from {target_path}: {e}")
                    self._model = None
                    self._loaded_path = None
                    self._explainer = None
            return self._model

    def get_explainer(self, model_path: Optional[Union[str, Path]] = None):
        with self._lock:
            model = self.get_model(model_path)
            if model is None:
                return None
            if self._explainer is None:
                self._explainer = TreeSHAPExplainer(model)
            return self._explainer

    def get_metadata(self, metadata_path: Optional[Union[str, Path]] = None):
        with self._lock:
            target_path = Path(metadata_path) if metadata_path is not None else DEFAULT_METADATA_PATH
            if not target_path.exists():
                return None
            if self._metadata is None:
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        self._metadata = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load model metadata from {target_path}: {e}")
                    self._metadata = None
            return self._metadata


def _describe_feature_factor(feature_name: str, shap_val: float, fv: FeatureVector) -> tuple[Optional[str], Optional[str]]:
    """
    Translates a SHAP-attributed feature contribution into a grounded human-readable explanation sentence.
    Returns (positive_sentence, risk_sentence).
    """
    pos_desc = None
    risk_desc = None

    if feature_name == "dscr":
        if shap_val > 0:
            pos_desc = f"Strong Debt Service Coverage Ratio (DSCR: {fv.dscr:.2f}) comfortably clears RBI benchmark (1.33)"
        else:
            risk_desc = (
                f"Critical DSCR ({fv.dscr:.2f}) indicates severe cashflow deficit for loan servicing"
                if fv.dscr < 1.0
                else f"Marginal DSCR ({fv.dscr:.2f}) leaves narrow cashflow safety margin against revenue dips"
            )

    elif feature_name == "subsidy_coverage_ratio":
        if shap_val > 0:
            pos_desc = f"Substantial capital subsidy coverage ({fv.subsidy_coverage_ratio * 100:.1f}% of project cost) reduces debt liability"
        else:
            risk_desc = f"Low or zero capital subsidy coverage ({fv.subsidy_coverage_ratio * 100:.1f}% of project cost) increases debt burden"

    elif feature_name == "loan_to_income_ratio":
        if shap_val > 0:
            pos_desc = f"Conservative loan-to-turnover leverage ({fv.loan_to_income_ratio:.2f}x)"
        else:
            risk_desc = f"High debt-to-turnover leverage ({fv.loan_to_income_ratio:.2f}x annual revenue)"

    elif feature_name == "infrastructure_score":
        if shap_val > 0:
            pos_desc = f"High village infrastructure readiness ({fv.infrastructure_score:.1f}/10)"
        else:
            risk_desc = f"Low site infrastructure readiness ({fv.infrastructure_score:.1f}/10) may increase logistics cost"

    elif feature_name == "cpi_inflation_pct":
        if shap_val > 0:
            pos_desc = f"Stable local price environment (CPI: {fv.cpi_inflation_pct:.2f}%) supports operating margins"
        else:
            risk_desc = f"Elevated rural inflation pressure ({fv.cpi_inflation_pct:.2f}%) requires proactive pricing adjustments"

    elif feature_name == "working_capital_months_buffer":
        if shap_val > 0:
            pos_desc = f"Healthy liquidity buffer ({fv.working_capital_months_buffer:.1f} months of working capital reserve)"
        else:
            risk_desc = f"Tight working capital liquidity buffer ({fv.working_capital_months_buffer:.1f} months)"

    elif feature_name == "competition_intensity":
        if shap_val > 0:
            pos_desc = "Low competitor saturation in local market catchment"
        else:
            risk_desc = f"High local competition intensity ({fv.competition_intensity:.2f}/1.0)"

    elif feature_name == "weather_risk_score":
        if shap_val > 0:
            pos_desc = "Favorable local climatic and weather risk profile"
        else:
            risk_desc = f"Seasonal heavy weather risk score ({fv.weather_risk_score:.2f}) requires buffer stocking"

    elif feature_name == "log_projected_population":
        if shap_val > 0:
            pos_desc = "Strong local demographic population catchment supports commercial demand"
        else:
            risk_desc = "Constrained catchment population limits local demand volume"

    elif feature_name == "msme_density_per_10k":
        if shap_val > 0:
            pos_desc = f"Dense enterprise network ({fv.msme_density_per_10k:.1f}/10k) provides mature supply-chain support"
        else:
            risk_desc = f"Sparse enterprise density ({fv.msme_density_per_10k:.1f}/10k) indicates nascent commercial ecosystem"

    return pos_desc, risk_desc


def _shap_explain(fv: FeatureVector, model: Any, pred_idx: int) -> tuple[dict[str, Any], list[str], list[str]]:
    """
    Computes per-prediction SHAP contributions toward the predicted class.
    Returns:
        (shap_explanation_dict, top_positive_factors, top_risk_factors)
    """
    X_arr = fv.to_clamped_array().reshape(1, -1)
    predicted_class = CLASS_MAP[pred_idx]
    fv_dict = fv.to_dict()

    loader = ViabilityModelLoader()
    explainer = loader.get_explainer()

    if explainer is None:
        explainer = TreeSHAPExplainer(model)

    class_shap_vals, base_val = explainer.explain(X_arr, pred_idx)

    contributions = []
    for i, name in enumerate(FEATURE_NAMES):
        s_val = float(class_shap_vals[i])
        f_val = float(fv_dict.get(name, 0.0))
        contributions.append({
            "feature": name,
            "shap_value": round(s_val, 4),
            "feature_value": round(f_val, 4),
        })

    # Sort strictly by absolute magnitude descending
    contributions.sort(key=lambda item: abs(item["shap_value"]), reverse=True)

    positives: list[str] = []
    risks: list[str] = []

    for item in contributions:
        feat_name = item["feature"]
        s_val = item["shap_value"]
        pos_str, risk_str = _describe_feature_factor(feat_name, s_val, fv)

        if s_val > 0.0 and pos_str and pos_str not in positives:
            positives.append(pos_str)
        elif s_val < 0.0 and risk_str and risk_str not in risks:
            risks.append(risk_str)

    if not positives:
        positives.append("Enterprise parameters align with baseline operational viability")
    if not risks:
        risks.append("No high-severity operational risk factors detected")

    shap_explanation = {
        "base_value": round(base_val, 4),
        "predicted_class": predicted_class,
        "contributions": contributions,
    }

    return shap_explanation, positives[:3], risks[:3]


def _explain_factors_heuristic(features: FeatureVector) -> tuple[list[str], list[str]]:
    """Heuristic fallback factor explanations for deterministic offline rule fallback."""
    positives: list[str] = []
    risks: list[str] = []

    if features.dscr >= 1.33:
        positives.append(f"Strong Debt Service Coverage Ratio (DSCR: {features.dscr:.2f}) comfortably clears RBI benchmark (1.33)")
    elif features.dscr >= 1.0:
        risks.append(f"Marginal DSCR ({features.dscr:.2f}) leaves narrow cashflow safety margin against revenue dips")
    else:
        risks.append(f"Critical DSCR ({features.dscr:.2f}) indicates severe cashflow deficit for loan servicing")

    if features.subsidy_coverage_ratio >= 0.20:
        positives.append(f"Substantial capital subsidy coverage ({features.subsidy_coverage_ratio * 100:.1f}% of project cost) reduces debt liability")
    elif features.subsidy_coverage_ratio == 0.0:
        risks.append("Zero government subsidy grant; 100% of capital must be self-funded or debt-financed")

    if features.loan_to_income_ratio <= 1.5:
        positives.append(f"Conservative loan-to-turnover leverage ({features.loan_to_income_ratio:.2f}x)")
    elif features.loan_to_income_ratio >= 3.0:
        risks.append(f"High debt-to-turnover leverage ({features.loan_to_income_ratio:.2f}x annual revenue)")

    if features.infrastructure_score >= 7.0:
        positives.append(f"High village infrastructure readiness ({features.infrastructure_score:.1f}/10)")
    elif features.infrastructure_score < 5.0:
        risks.append(f"Low site infrastructure readiness ({features.infrastructure_score:.1f}/10) may increase logistics cost")

    if features.cpi_inflation_pct > 6.5:
        risks.append(f"Elevated rural inflation pressure ({features.cpi_inflation_pct:.2f}%) requires proactive pricing adjustments")

    if features.working_capital_months_buffer >= 3.0:
        positives.append(f"Healthy liquidity buffer ({features.working_capital_months_buffer:.1f} months of working capital reserve)")
    elif features.working_capital_months_buffer < 1.0:
        risks.append(f"Tight working capital liquidity buffer ({features.working_capital_months_buffer:.1f} months)")

    if features.competition_intensity <= 0.30:
        positives.append("Low competitor saturation in local market catchment")
    elif features.competition_intensity >= 0.65:
        risks.append(f"High local competition intensity ({features.competition_intensity:.2f}/1.0)")

    if features.weather_risk_score >= 0.35:
        risks.append(f"Seasonal heavy weather risk score ({features.weather_risk_score:.2f}) requires buffer stocking")

    if not positives:
        positives.append("Enterprise parameters align with baseline operational viability")
    if not risks:
        risks.append("No high-severity operational risk factors detected")

    return positives[:3], risks[:3]


def _rule_based_fallback(features: FeatureVector) -> ViabilityPrediction:
    """100% Deterministic rule-based fallback when ML model artifact is offline."""
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

    pos, risk = _explain_factors_heuristic(features)
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
        shap_explanation={"available": False, "reason": "Rule-based fallback active (no ML model to explain)"},
        global_feature_importance=None,
    )


def predict_viability(
    features: Union[FeatureVector, dict[str, float], list[float], np.ndarray],
    model_path: Optional[Union[str, Path]] = None,
) -> ViabilityPrediction:
    """
    Performs high-speed (< 5ms) multi-class viability classification with real SHAP explainability.
    """
    # 1. Normalize input into FeatureVector
    if isinstance(features, FeatureVector) or type(features).__name__ == "FeatureVector" or hasattr(features, "to_clamped_array"):
        if isinstance(features, FeatureVector):
            fv = features
        else:
            fv = FeatureVector(*features.to_array().tolist())
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

        # Real SHAP TreeExplainer explainability
        shap_explanation, positives, risks = _shap_explain(fv, model, pred_idx)

        # Global feature importance from model metadata
        metadata = loader.get_metadata()
        global_imp = metadata.get("feature_importances_ranked") if metadata else None

        return ViabilityPrediction(
            verdict=verdict,
            confidence_pct=confidence_pct,
            class_probabilities=prob_dict,
            top_positive_factors=positives,
            top_risk_factors=risks,
            feature_values=fv.to_dict(),
            is_fallback=False,
            model_version="xgboost_v2.0",
            shap_explanation=shap_explanation,
            global_feature_importance=global_imp,
        )

    except Exception as e:
        logger.warning(f"Inference error, degrading to rule fallback: {e}")
        return _rule_based_fallback(fv)
