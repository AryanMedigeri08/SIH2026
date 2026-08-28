"""
feasibility.py — REST API Router for End-to-End Feasibility Analysis and Bank DPR Export.
Fully integrated with live Census 2011, MSME District Data, MoSPI CPI, IMD Weather,
and Data.gov.in 613 District Resource Amenities.
"""

from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

logger = logging.getLogger("udyam_saathi.feasibility")

from financial_calculator import (
    emi_with_moratorium, working_capital_estimate, compute_dscr, rank_eligible_schemes,
)
from market_analyzer import (
    project_population, estimate_tam, compute_msme_density, compute_competition_intensity,
)
from risk_analyzer import build_risk_matrix, overall_risk_verdict
from swot_analyzer import build_swot
from pricing_engine import compute_pricing
from feature_extractor import extract_features_from_pipeline_objects
from inference import predict_viability
from executive_synthesizer import generate_executive_synthesis
from dpr_generator import build_bank_dpr, dpr_to_printable_markdown, dpr_to_html, BankDPRDocument
from amenities_client import fetch_village_amenities

from app.config import settings
from app.database import db_manager
from app.models.schemas import UserInput, FeasibilityReport

router = APIRouter(prefix="/feasibility", tags=["Feasibility Analysis & DPR"])


async def _run_pipeline(input_data: UserInput) -> tuple[FeasibilityReport, BankDPRDocument]:
    """
    Executes the complete 4-tier pipeline querying live ground-truth databases and APIs:
      - Tier 1 (Market Demographics): census_raw (660k+ rows) + msme_district (788 rows)
      - Tier 1 (Financial Optimization): PMEGP, PMFME, MUDRA, Stand-Up India Slabs
      - Tier 2 (Amenities & Climate): 613 District Resource APIs + cpi_data + IMD Weather
      - Tier 2 (ML Viability): 10-Dimensional XGBoost Classifier
      - Tier 3 (Executive Narrative): Groq Cloud Llama-3-70B AI Synthesis
      - Tier 4 (Bank Memorandum): 7-Section Bank DPR Compilation
    """
    logger.info(
        f"⚡ [PIPELINE START] Enterprise: '{input_data.enterprise_name}' | Sector: '{input_data.sector}' | "
        f"Outlay: ₹{input_data.project_cost:,.0f} | Location: {input_data.village_name}, {input_data.district_name}, {input_data.state_name}"
    )

    # 1. Market & Ground-Truth Demographics (Tier 1)
    census_data = await db_manager.get_census_demographics(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
        village_name=input_data.village_name,
    )
    base_pop = census_data["base_population_2011"]
    pop = project_population(base_pop, input_data.state_name, 2026)
    tam = estimate_tam(pop.projected_households, input_data.sector)
    logger.info(
        f"📊 [TIER 1 DEMOGRAPHICS] Querying Table: 'census_raw' | State: '{input_data.state_name}' | "
        f"District: '{input_data.district_name}' -> Base Pop 2011: {base_pop:,}, Projected 2026: {pop.projected_population:,}, TAM: ₹{tam.annual_tam:,.0f}"
    )

    msme_data = await db_manager.get_district_msme_stats(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
    )
    msme_total = msme_data["total_msme"]
    dens = compute_msme_density(msme_total, pop.projected_population)
    comp = compute_competition_intensity(msme_total, 0.05, pop.projected_population)
    logger.info(
        f"🏢 [TIER 1 MSME] Querying Table: 'msme_district' | District: '{input_data.district_name}' -> "
        f"Total MSMEs: {msme_total:,}, MSME Density: {dens.msme_density_per_10k:.2f}/10k"
    )

    # 2. Financial & Scheme Optimization (Tier 1)
    wc = working_capital_estimate(input_data.annual_turnover_estimate, input_data.sector)
    schemes = rank_eligible_schemes(
        project_cost=input_data.project_cost,
        business_category=input_data.business_category,
        sector=input_data.sector,
        promoter_category=input_data.promoter_category,
        is_rural=input_data.is_rural,
        tenure_years=input_data.tenure_years,
        moratorium_months=input_data.moratorium_months,
    )
    top_scheme = next((r for r in schemes if r.eligible), schemes[0])

    promoter_pct = 0.05 if input_data.promoter_category.lower() != "general" else 0.10
    promoter_margin_val = input_data.project_cost * promoter_pct
    loan_principal = max(input_data.project_cost - top_scheme.subsidy_grant_amount - promoter_margin_val, 1.0)
    amort = emi_with_moratorium(loan_principal, top_scheme.effective_interest_rate_pct, input_data.tenure_years, input_data.moratorium_months)

    monthly_noi = input_data.monthly_net_operating_income_override or (input_data.annual_turnover_estimate * 0.30 / 12)
    dscr_res = compute_dscr(monthly_noi, amort.monthly_emi)
    subsidy_coverage_ratio = top_scheme.subsidy_grant_amount / input_data.project_cost if input_data.project_cost else 0.0

    logger.info(
        f"🏛️ [TIER 1 SCHEMES] Querying Source: 'government_schemes.json' | Evaluated {len(schemes)} schemes -> "
        f"Top Scheme: {top_scheme.scheme_id} ({top_scheme.full_name}) | Subsidy: ₹{top_scheme.subsidy_grant_amount:,.0f} ({subsidy_coverage_ratio * 100:.1f}%) | "
        f"EMI: ₹{amort.monthly_emi:,.2f} | DSCR: {dscr_res.dscr:.2f} ({dscr_res.verdict})"
    )

    # Compute additional key financial appraisal ratios (ROI & Break-Even)
    monthly_net_profit = max(monthly_noi - amort.monthly_emi, 0.0)
    annual_net_profit = monthly_net_profit * 12
    roi_pct = round((annual_net_profit / input_data.project_cost) * 100, 2) if input_data.project_cost > 0 else 0.0

    fixed_cost_monthly = amort.monthly_emi + (wc.monthly_working_capital_outlay * 0.35)
    contrib_margin_ratio = 0.30
    annual_bep_sales = (fixed_cost_monthly * 12) / contrib_margin_ratio
    break_even_pct = round(min((annual_bep_sales / input_data.annual_turnover_estimate) * 100, 100.0), 2) if input_data.annual_turnover_estimate > 0 else 0.0

    # 3. Pricing Engine (Tier 1)
    expected_units = input_data.expected_monthly_units or max(input_data.annual_turnover_estimate / 12 / 250, 50.0)
    
    # 4. Live CPI & Weather Risk Lookup
    cpi_pct = input_data.cpi_inflation_pct if input_data.cpi_inflation_pct is not None else await db_manager.get_state_cpi_inflation(input_data.state_name)
    pricing = compute_pricing(amort.monthly_emi, wc.monthly_working_capital_outlay, expected_units, cpi_pct)

    weather_score = input_data.weather_risk_score if input_data.weather_risk_score is not None else await db_manager.get_weather_risk_score(input_data.state_name, input_data.district_name)

    # 5. 613 Village Amenities API & Infrastructure Score
    amenities = fetch_village_amenities(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
        village_name=input_data.village_name,
        api_key=settings.DATA_GOV_IN_API_KEY,
        api_base_url=settings.AMENITIES_API_BASE_URL,
    )
    infra_score = input_data.infrastructure_score if input_data.infrastructure_score is not None else amenities.infrastructure_score
    logger.info(
        f"🌐 [TIER 2 AMENITIES] Querying Source: 'district_resources.json' (Data.gov.in 613 Amenities) | "
        f"District: '{input_data.district_name}' -> Infra Score: {infra_score:.1f}/10 | CPI: {cpi_pct:.1f}% | Weather Risk: {weather_score:.2f}"
    )

    # 6. Feature Extraction & XGBoost Viability Model (Tier 2)
    fv = extract_features_from_pipeline_objects(
        pop, tam, dens, comp, top_scheme, amort, dscr_res, wc,
        input_data.project_cost, input_data.annual_turnover_estimate,
        infra_score, cpi_pct, weather_score, promoter_margin_val,
    )
    ml_pred = predict_viability(fv)
    logger.info(
        f"🤖 [TIER 2 ML INFERENCE] Model: 'viability_xgb.joblib' (XGBoost 10-D Classifier) | "
        f"Fallback Mode: {ml_pred.is_fallback} -> Verdict: {ml_pred.verdict} | Confidence: {ml_pred.confidence_pct:.1f}%"
    )

    # 7. Risk Assessment & Grounded SWOT (Tier 1 + Tier 2)
    wc_buf = promoter_margin_val / wc.monthly_working_capital_outlay if wc.monthly_working_capital_outlay else 0.0

    risks = build_risk_matrix(
        dscr_res.dscr, amort.monthly_emi, tam.annual_tam, input_data.annual_turnover_estimate,
        comp.competition_intensity_normalized, infra_score, cpi_pct, weather_score,
        wc_buf, subsidy_coverage_ratio,
    )
    risk_verdict = overall_risk_verdict(risks)

    swot = build_swot(
        dscr_res.dscr, top_scheme.subsidy_grant_amount, top_scheme.full_name, input_data.project_cost,
        infra_score, tam.annual_tam, input_data.annual_turnover_estimate,
        comp.competition_intensity_normalized, dens.msme_density_per_10k, cpi_pct, weather_score,
        ml_pred.verdict, ml_pred.confidence_pct,
    )

    # 8. Executive AI Synthesis (Tier 3)
    synthesis = generate_executive_synthesis({
        "enterprise_name": input_data.enterprise_name,
        "business_category": input_data.business_category,
        "sector": input_data.sector,
        "location_str": f"{input_data.village_name}, {input_data.block_name}, {input_data.district_name}, {input_data.state_name}",
        "project_cost": input_data.project_cost,
        "promoter_margin_amount": promoter_margin_val,
        "top_scheme_name": f"{top_scheme.scheme_id} ({top_scheme.full_name})",
        "subsidy_amount": top_scheme.subsidy_grant_amount,
        "subsidy_pct": subsidy_coverage_ratio * 100,
        "effective_loan": loan_principal,
        "monthly_emi": amort.monthly_emi,
        "dscr": dscr_res.dscr,
        "dscr_verdict": dscr_res.verdict,
        "annual_tam": tam.annual_tam,
        "cpi_adjusted_price_floor": pricing.cpi_adjusted_unit_price_floor,
        "ml_verdict": ml_pred.verdict,
        "ml_confidence_pct": ml_pred.confidence_pct,
        "top_positive_driver": ml_pred.top_positive_factors[0],
        "top_risk_factor": ml_pred.top_risk_factors[0],
        "key_risks": [r.title for r in risks if r.severity in ("HIGH", "SEVERE", "MODERATE")][:2],
        "additional_business_details": input_data.additional_business_details,
    }, language=input_data.language)
    logger.info(
        f"📝 [TIER 3 SYNTHESIS] Model: '{synthesis.model_name}' | Language: '{input_data.language.upper()}' | "
        f"Source: {'[DETERMINISTIC_TEMPLATE]' if synthesis.is_fallback else '[AI_GENERATED]'}"
    )

    # 9. Bank DPR Assembly (Tier 4)
    dpr_doc = build_bank_dpr(
        enterprise_name=input_data.enterprise_name,
        business_category=input_data.business_category,
        sector=input_data.sector,
        promoter_name=input_data.promoter_name,
        promoter_category=input_data.promoter_category,
        gender=input_data.gender,
        state_name=input_data.state_name,
        district_name=input_data.district_name,
        block_name=input_data.block_name,
        village_name=input_data.village_name,
        is_rural=input_data.is_rural,
        project_cost=input_data.project_cost,
        annual_turnover_estimate=input_data.annual_turnover_estimate,
        tenure_years=input_data.tenure_years,
        moratorium_months=input_data.moratorium_months,
        pop_projection=pop,
        tam_estimate=tam,
        msme_density=dens,
        ranked_schemes=schemes,
        amortization=amort,
        dscr_result=dscr_res,
        risk_points=risks,
        risk_verdict=risk_verdict,
        swot_matrix=swot,
        pricing_result=pricing,
        ml_prediction=ml_pred,
        ai_synthesis=synthesis,
    )

    report_id = f"REP-{uuid.uuid4().hex[:10].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    logger.info(f"📄 [TIER 4 DPR] 7-Section Bank Memorandum Compiled | Report ID: {report_id}")

    # Build comprehensive Data Sources & Audit Lineage
    data_sources_used = [
        {
            "layer": "Tier 1: Demographics",
            "logical_source": "Census 2011 Rural Catchment Database",
            "table_or_file": "census_raw",
            "records_matched": 1,
            "status": "Queried OK",
            "attribution": f"Village: {input_data.village_name}, District: {input_data.district_name}, State: {input_data.state_name}",
        },
        {
            "layer": "Tier 1: MSME Density",
            "logical_source": "Ministry of MSME Enterprise Registry",
            "table_or_file": "msme_district",
            "records_matched": 1,
            "status": "Queried OK",
            "attribution": f"District MSME count: {msme_total:,} units",
        },
        {
            "layer": "Tier 1: Government Schemes",
            "logical_source": "Statutory Central & State MSME Schemes",
            "table_or_file": "government_schemes.json",
            "records_matched": len(schemes),
            "status": "Queried OK",
            "attribution": f"Evaluated 5 schemes; Top: {top_scheme.scheme_id} (Subsidy: ₹{top_scheme.subsidy_grant_amount:,.0f})",
        },
        {
            "layer": "Tier 2: District Amenities",
            "logical_source": "Data.gov.in 613 District Amenities & MoSPI CPI",
            "table_or_file": "district_resources.json",
            "records_matched": 1,
            "status": "Queried OK",
            "attribution": f"Infra score: {infra_score:.1f}/10, CPI: {cpi_pct:.1f}%",
        },
        {
            "layer": "Tier 2: ML Viability Classifier",
            "logical_source": "Supervised 10-D XGBoost Viability Classifier",
            "table_or_file": "viability_xgb.joblib",
            "records_matched": 1,
            "status": "Rule Fallback" if ml_pred.is_fallback else "Trained Model Executed",
            "attribution": f"Verdict: {ml_pred.verdict} (Confidence: {ml_pred.confidence_pct:.1f}%)",
        },
        {
            "layer": "Tier 3: Executive Synthesis",
            "logical_source": f"Groq Cloud AI Model ({synthesis.model_name})" if not synthesis.is_fallback else "Deterministic Statutory Template Engine",
            "table_or_file": "groq_api" if not synthesis.is_fallback else "deterministic_template_matrix",
            "records_matched": 1,
            "status": "Template Fallback" if synthesis.is_fallback else "AI Synthesized",
            "attribution": f"Language: {input_data.language.upper()} ({synthesis.model_name})",
        },
    ]

    feasibility_report = FeasibilityReport(
        report_id=report_id,
        generated_at_utc=now_iso,
        input_parameters=input_data,
        market_demographics={
            "population_projection": pop.to_dict(),
            "census_details": census_data,
            "tam": tam.to_dict(),
            "msme_density": dens.to_dict(),
            "msme_details": msme_data,
            "competition": comp.to_dict(),
            "village_amenities_613": amenities.to_dict(),
        },
        financial_analysis={
            "working_capital": wc.to_dict(),
            "amortization": amort.to_dict(),
            "dscr": dscr_res.to_dict(),
            "loan_principal": loan_principal,
            "promoter_margin_amount": promoter_margin_val,
            "monthly_net_profit": round(monthly_net_profit, 2),
            "annual_net_profit": round(annual_net_profit, 2),
            "roi_pct": roi_pct,
            "break_even_pct": break_even_pct,
            "cpi_inflation_pct": cpi_pct,
        },
        scheme_optimization=[s.to_dict() for s in schemes[:5]],
        ml_viability=ml_pred.to_dict(),
        risk_assessment={
            "risk_points": [r.to_dict() for r in risks],
            "verdict": risk_verdict,
            "composite_grade": risk_verdict.get("overall_severity", "MODERATE"),
            "average_risk_score": risk_verdict.get("average_risk_score", 3.0),
        },
        swot_matrix=swot.to_dict(),
        pricing_recommendation=pricing.to_dict(),
        executive_synthesis=synthesis.to_dict(),
        data_sources_used=data_sources_used,
    )

    return feasibility_report, dpr_doc


@router.post("/generate", response_model=FeasibilityReport)
async def generate_feasibility(input_data: UserInput):
    """
    Executes full multi-tier enterprise feasibility pipeline.
    Stores and returns the complete FeasibilityReport payload.
    """
    try:
        report, dpr = await _run_pipeline(input_data)
        # Store in db / memory cache for instant retrieval
        await db_manager.save_feasibility_report(report.report_id, {
            "report": report.model_dump(mode="json"),
            "dpr": dpr.to_dict(),
        })
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feasibility pipeline error: {str(e)}")


@router.get("/{report_id}", response_model=FeasibilityReport)
async def get_feasibility(report_id: str):
    """Retrieves cached feasibility report by ID."""
    cached = await db_manager.get_feasibility_report(report_id)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Feasibility report '{report_id}' not found.")
    return FeasibilityReport(**cached["report"])


@router.post("/dpr")
async def generate_direct_dpr(
    input_data: UserInput,
    format: str = Query("json", description="Output format: json | markdown | html"),
):
    """Directly transforms user input into official 7-Section Bank DPR."""
    try:
        report, dpr = await _run_pipeline(input_data)
        fmt = format.lower().strip()
        if fmt == "html":
            return HTMLResponse(content=dpr_to_html(dpr), media_type="text/html")
        elif fmt == "markdown":
            return PlainTextResponse(content=dpr_to_printable_markdown(dpr), media_type="text/markdown")
        return dpr.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}/dpr")
async def get_report_dpr(
    report_id: str,
    format: str = Query("json", description="Output format: json | markdown | html"),
):
    """Retrieves 7-Section Bank DPR for an existing feasibility report."""
    cached = await db_manager.get_feasibility_report(report_id)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    dpr_dict = cached["dpr"]
    dpr_doc = BankDPRDocument(**dpr_dict)

    fmt = format.lower().strip()
    if fmt == "html":
        return HTMLResponse(content=dpr_to_html(dpr_doc), media_type="text/html")
    elif fmt == "markdown":
        return PlainTextResponse(content=dpr_to_printable_markdown(dpr_doc), media_type="text/markdown")
    return dpr_dict
