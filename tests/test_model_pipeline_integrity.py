import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = ROOT_DIR / "backend" / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import asyncio
from app.core.feature_extractor import extract_features
from app.core.inference import predict_viability
from app.core.executive_synthesizer import generate_executive_synthesis
from app.core.dpr_generator import dpr_to_printable_markdown, dpr_to_html
from app.core.chat_service import ChatService
from app.routers.feasibility import _run_pipeline
from app.models.schemas import UserInput


def test_xgboost_ml_viability():
    """1. Feature Extraction & XGBoost 10-D Viability Model with SHAP Attribution"""
    fv = extract_features(
        dscr=1.45,
        subsidy_grant_amount=175000.0,
        total_project_cost=500000.0,
        loan_principal=275000.0,
        annual_turnover=950000.0,
        projected_population=25000,
        msme_density_per_10k=12.5,
        infrastructure_score=7.2,
        cpi_inflation_pct=4.8,
        working_capital_months_buffer=2.5,
        competition_intensity=0.35,
        weather_risk_score=0.15,
    )
    pred = predict_viability(fv)
    print("\n[TEST 1: ML VIABILITY MODEL]")
    print("  Verdict:", pred.verdict)
    print("  Confidence:", f"{pred.confidence_pct:.2f}%")
    print("  Model version:", pred.model_version)
    print("  Is fallback:", pred.is_fallback)
    print("  Top Positives:", pred.top_positive_factors)
    print("  Top Risks:", pred.top_risk_factors)
    assert pred.verdict in ["SUITABLE", "CAUTION", "RECONSIDER"]
    assert 0 <= pred.confidence_pct <= 100
    assert not pred.is_fallback, "Expected true XGBoost model inference, not fallback"
    print("  => PASS")


def test_executive_ai_synthesizer():
    """2. Executive AI Synthesizer (Sarvam AI / Groq LLM)"""
    print("\n[TEST 2: EXECUTIVE AI SYNTHESIZER]")
    payload = {
        "enterprise_name": "Kaveri Spices Processing Unit",
        "business_category": "manufacturing",
        "sector": "food_processing",
        "location_str": "Hassan, Karnataka",
        "project_cost": 500000.0,
        "promoter_margin_amount": 50000.0,
        "top_scheme_name": "PMEGP",
        "subsidy_amount": 175000.0,
        "subsidy_pct": 35.0,
        "effective_loan": 275000.0,
        "monthly_emi": 5776.0,
        "dscr": 1.45,
        "dscr_verdict": "VIABLE",
        "annual_tam": 4500000.0,
        "cpi_adjusted_price_floor": 185.0,
        "ml_verdict": "SUITABLE",
        "ml_confidence_pct": 97.2,
        "top_positive_driver": "Strong Debt Service Coverage Ratio (DSCR: 1.45)",
        "top_risk_factor": "Seasonal heavy weather risk score",
    }
    synthesis = generate_executive_synthesis(payload, language="en")
    print("  Model used:", synthesis.model_name)
    print("  Source type:", "FALLBACK TEMPLATE" if synthesis.is_fallback else "AI GENERATED")
    print("  Summary length:", len(synthesis.executive_summary))
    assert len(synthesis.executive_summary) > 50
    assert len(synthesis.strategic_recommendations) >= 2
    assert len(synthesis.bank_appraisal_notes) > 20
    print("  => PASS")


def test_full_feasibility_pipeline_and_dpr():
    """3. Full Feasibility Pipeline with Intelligent Turnover, Break-Even & DPR"""
    print("\n[TEST 3: FULL FEASIBILITY PIPELINE & DPR]")
    async def run():
        inp = UserInput(
            enterprise_name="Kaveri Spices Processing Unit",
            state_name="Karnataka",
            district_name="Hassan",
            sector="food_processing",
            business_category="manufacturing",
            project_cost=650000.0,
            promoter_category="general",
            is_rural=True,
            tenure_years=5,
            moratorium_months=6,
        )
        report, dpr_doc = await _run_pipeline(inp)
        return report, dpr_doc

    report, dpr_doc = asyncio.run(run())
    print("  Report ID:", report.report_id)
    print("  Enterprise:", report.input_parameters.enterprise_name)
    fa = report.financial_analysis
    print("  Auto-computed Annual Turnover: Rs.", fa.get("annual_turnover_estimate", 0))
    print("  Monthly Net Profit: Rs.", fa.get("monthly_net_profit", 0))
    print("  ROI (%):", fa.get("roi_pct"))
    print("  Break-Even Horizon:", fa.get("break_even_milestone"))
    print("  Payback Period:", fa.get("payback_period_years"), "Years")
    print("  Equity Payback:", fa.get("equity_payback_years"), "Years")
    print("  Break-Even Rationale:", fa.get("break_even_rationale"))
    ml_v = report.ml_viability
    print("  ML Verdict:", ml_v.get("verdict"), f"({ml_v.get('confidence_pct')}%)")
    assert fa.get("annual_turnover_estimate", 0) > 0, "Intelligent turnover must be auto-computed"
    assert fa.get("break_even_milestone") is not None
    assert fa.get("payback_period_years") is not None
    assert ml_v.get("verdict") in ["SUITABLE", "CAUTION", "RECONSIDER"]

    # DPR Verification
    md_out = dpr_to_printable_markdown(dpr_doc)
    html_out = dpr_to_html(dpr_doc)
    print("\n[TEST 4: DPR EXPORT VALIDATION]")
    print("  DPR Markdown length:", len(md_out))
    print("  DPR HTML length:", len(html_out))
    assert len(md_out) > 500
    assert len(html_out) > 1000
    assert "Break-Even Horizon" in md_out or "Break-Even" in md_out
    assert "Commercial Gestation" in html_out or "Commercial Gestation" in md_out
    print("  => PASS")


def test_conversational_chat_service():
    """4. Conversational MSME Advisory Engine (ChatService)"""
    print("\n[TEST 5: CONVERSATIONAL CHAT SERVICE]")
    cs = ChatService.get_instance()
    messages = [{"role": "user", "content": "What is the PMEGP subsidy rate for a rural micro unit?"}]
    res = cs.generate_chat_response(messages=messages, language="en")
    reply_text = res.get("reply") or res.get("message", "")
    print("  Chat Model:", res.get("model"))
    print("  Is Fallback:", res.get("is_fallback"))
    print("  Data Sources:", res.get("sources"))
    print("  Reply Length:", len(reply_text))
    print("  Reply Excerpt:", reply_text[:180])
    assert len(reply_text) > 20, "Expected non-empty conversational reply"
    print("  => PASS")


if __name__ == "__main__":
    test_xgboost_ml_viability()
    test_executive_ai_synthesizer()
    test_full_feasibility_pipeline_and_dpr()
    test_conversational_chat_service()
    print("\n=======================================================")
    print("ALL AI & ML MODEL INTEGRITY CHECKS PASSED 100% SUCCESFULLY!")
    print("=======================================================\n")
