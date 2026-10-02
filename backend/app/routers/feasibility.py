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
from fastapi import APIRouter, Query, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse

logger = logging.getLogger("udyam_saathi.feasibility")

from financial_calculator import (
    emi_with_moratorium, working_capital_estimate, compute_dscr, rank_eligible_schemes,
    compute_break_even_and_payback,
)
from market_analyzer import (
    project_population, estimate_tam, compute_msme_density, compute_competition_intensity,
)
from risk_analyzer import build_risk_matrix, overall_risk_verdict
from swot_analyzer import build_swot, SWOTMatrix
from pricing_engine import compute_pricing
from feature_extractor import extract_features_from_pipeline_objects
from inference import predict_viability
from executive_synthesizer import generate_executive_synthesis
from dpr_generator import build_bank_dpr, dpr_to_printable_markdown, dpr_to_html, BankDPRDocument
from amenities_client import fetch_village_amenities
from opportunity_matcher import get_alternative_recommendations

try:
    from app.core.machinery_matcher import calculate_intelligent_turnover
except ImportError:
    from backend.app.core.machinery_matcher import calculate_intelligent_turnover

from app.config import settings
from app.database import db_manager
from app.core.auth_dependency import get_current_user, get_current_user_optional, AuthenticatedUser
from app.core.translation_service import TranslationService
from app.core.odop_matcher import match_odop
from app.models.schemas import UserInput, FeasibilityReport

router = APIRouter(prefix="/feasibility", tags=["Feasibility Analysis & DPR"])


async def _run_pipeline(input_data: UserInput) -> tuple[FeasibilityReport, BankDPRDocument]:
    """
    Executes the complete 4-tier pipeline querying live ground-truth databases and APIs:
      - Tier 1 (Market Demographics): census_raw (660k+ rows) + msme_district (788 rows)
      - Tier 1 (Financial Optimization): PMEGP, PMFME, MUDRA, Stand-Up India Slabs
      - Tier 2 (Amenities & Climate): 613 District Resource APIs + cpi_data + IMD Weather
      - Tier 2 (ML Viability): 10-Dimensional XGBoost Classifier
      - Tier 3 (Executive Narrative): Sarvam AI (sarvam-105b-conversations) Multi-Lingual Synthesis
      - Tier 4 (Bank Memorandum): 7-Section Bank DPR Compilation
    """
    logger.info(
        f"⚡ [PIPELINE START] Enterprise: '{input_data.enterprise_name}' | Sector: '{input_data.sector}' | "
        f"Outlay: ₹{input_data.project_cost:,.0f} | Location: {input_data.village_name}, {input_data.district_name}, {input_data.state_name}"
    )

    # 0. Geographic Coordinates Grounding (GPS or Village-level Gazetteer resolution)
    from app.core.udyam.geography.gazetteer import Gazetteer
    resolved_lat = input_data.latitude
    resolved_lon = input_data.longitude
    coord_source = "gps_user_detected" if (resolved_lat and resolved_lon) else "unresolved"

    if (resolved_lat is None or resolved_lon is None) and input_data.village_name:
        g = Gazetteer()
        v_coords = g.resolve_locality_coords(
            village=input_data.village_name,
            district=input_data.district_name,
            state=input_data.state_name,
        )
        if v_coords:
            resolved_lat, resolved_lon = v_coords
            coord_source = "gazetteer_village_resolved"
        elif input_data.district_name:
            d_centroid = g.get_district_centroid(input_data.state_name, input_data.district_name)
            if d_centroid:
                resolved_lat, resolved_lon = d_centroid
                coord_source = "gazetteer_district_centroid"

    # 1. Market & Ground-Truth Demographics (Tier 1)
    census_data = await db_manager.get_census_demographics(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
        village_name=input_data.village_name,
    )
    if resolved_lat is not None:
        census_data["latitude"] = resolved_lat
        census_data["longitude"] = resolved_lon
        census_data["coordinate_source"] = coord_source
    base_pop = census_data["base_population_2011"]
    dist_base_pop = census_data.get("district_population_2011") or max(base_pop * 250, 1000000)
    pop = project_population(base_pop, input_data.state_name, 2026)
    dist_pop = project_population(dist_base_pop, input_data.state_name, 2026)
    tam = estimate_tam(pop.projected_households, input_data.sector)
    logger.info(
        f"📊 [TIER 1 DEMOGRAPHICS] Querying Table: 'census_raw' | State: '{input_data.state_name}' | "
        f"District: '{input_data.district_name}' -> Base Catchment Pop 2011: {base_pop:,}, Projected 2026: {pop.projected_population:,}, District Pop 2026: {dist_pop.projected_population:,}, TAM: ₹{tam.annual_tam:,.0f}"
    )

    msme_data = await db_manager.get_district_msme_stats(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
    )
    msme_total = msme_data["total_msme"]
    dens = compute_msme_density(msme_total, dist_pop.projected_population)
    comp = compute_competition_intensity(msme_total, 0.05, pop.projected_population, district_population=dist_pop.projected_population)
    logger.info(
        f"🏢 [TIER 1 MSME] Querying Table: 'msme_district' | District: '{input_data.district_name}' -> "
        f"Total MSMEs: {msme_total:,}, District MSME Density: {dens.msme_density_per_10k:.2f}/10k | Est. Catchment Competitors: {comp.estimated_local_competitors}"
    )

    # 2. Financial & Scheme Optimization (Tier 1)
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

    # Intelligently ground annual turnover with physical machine capacity, Census TAM, and RBI debt solvency
    turnover_audit = calculate_intelligent_turnover(
        project_cost=input_data.project_cost,
        sector=input_data.sector,
        business_category=input_data.business_category,
        expected_monthly_units=input_data.expected_monthly_units,
        annual_tam=tam.annual_tam,
        monthly_emi=amort.monthly_emi,
    )
    if not input_data.annual_turnover_estimate or input_data.annual_turnover_estimate <= 0:
        input_data.annual_turnover_estimate = turnover_audit["projected_turnover"]

    wc = working_capital_estimate(input_data.annual_turnover_estimate, input_data.sector)
    monthly_noi = input_data.monthly_net_operating_income_override or (input_data.annual_turnover_estimate * 0.30 / 12)
    dscr_res = compute_dscr(monthly_noi, amort.monthly_emi)
    subsidy_coverage_ratio = top_scheme.subsidy_grant_amount / input_data.project_cost if input_data.project_cost else 0.0

    logger.info(
        f"🏛️ [TIER 1 SCHEMES] Querying Source: 'government_schemes.json' | Evaluated {len(schemes)} schemes -> "
        f"Top Scheme: {top_scheme.scheme_id} ({top_scheme.full_name}) | Subsidy: ₹{top_scheme.subsidy_grant_amount:,.0f} ({subsidy_coverage_ratio * 100:.1f}%) | "
        f"EMI: ₹{amort.monthly_emi:,.2f} | DSCR: {dscr_res.dscr:.2f} ({dscr_res.verdict}) | "
        f"Turnover: ₹{input_data.annual_turnover_estimate:,.0f} ({turnover_audit.get('derivation_basis', 'Triangulated')})"
    )

    # Compute additional key financial appraisal ratios (ROI & Break-Even)
    monthly_net_profit = max(monthly_noi - amort.monthly_emi, 0.0)
    annual_net_profit = monthly_net_profit * 12
    roi_pct = round((annual_net_profit / input_data.project_cost) * 100, 2) if input_data.project_cost > 0 else 0.0

    # Dynamic statutory Break-Even Horizon & Capital Payback Period
    bep_res = compute_break_even_and_payback(
        project_cost=input_data.project_cost,
        annual_turnover=input_data.annual_turnover_estimate,
        monthly_emi=amort.monthly_emi,
        monthly_working_capital_outlay=wc.monthly_working_capital_outlay,
        moratorium_months=input_data.moratorium_months,
        subsidy_amount=top_scheme.subsidy_grant_amount,
        promoter_margin_val=promoter_margin_val,
        loan_principal=loan_principal,
    )
    break_even_pct = bep_res.break_even_pct

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

    # Deterministic baseline SWOT
    deterministic_swot = build_swot(
        dscr_res.dscr, top_scheme.subsidy_grant_amount, top_scheme.full_name, input_data.project_cost,
        infra_score, tam.annual_tam, input_data.annual_turnover_estimate,
        comp.competition_intensity_normalized, dens.msme_density_per_10k, cpi_pct, weather_score,
        ml_pred.verdict, ml_pred.confidence_pct,
    )

    # 8. Executive AI Synthesis & Grounded SWOT (Tier 3)
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
        "top_positive_driver": ml_pred.top_positive_factors[0] if ml_pred.top_positive_factors else "Adequate debt service margin",
        "top_risk_factor": ml_pred.top_risk_factors[0] if ml_pred.top_risk_factors else "Competitive pressure",
        "key_risks": [r.title for r in risks if r.severity in ("HIGH", "SEVERE", "MODERATE")][:2],
        "infrastructure_score": infra_score,
        "competition_intensity_normalized": comp.competition_intensity_normalized,
        "msme_density_per_10k": dens.msme_density_per_10k,
        "cpi_inflation_pct": cpi_pct,
        "weather_risk_score": weather_score,
        "annual_turnover_estimate": input_data.annual_turnover_estimate,
        "additional_business_details": input_data.additional_business_details,
    }, language=input_data.language)
    logger.info(
        f"📝 [TIER 3 SYNTHESIS] Model: '{synthesis.model_name}' | Language: '{input_data.language.upper()}' | "
        f"Source: {'[DETERMINISTIC_TEMPLATE]' if synthesis.is_fallback else '[AI_GENERATED]'}"
    )

    # Use LLM-generated SWOT if available, fallback to deterministic
    if synthesis.swot_matrix and isinstance(synthesis.swot_matrix, dict):
        final_swot = SWOTMatrix.from_dict(
            synthesis.swot_matrix,
            generation_source=f"AI_SARVAM ({synthesis.model_name})" if not synthesis.is_fallback else "DETERMINISTIC_FALLBACK",
            is_fallback=synthesis.is_fallback,
        )
    else:
        deterministic_swot.generation_source = "DETERMINISTIC_FALLBACK"
        deterministic_swot.is_fallback = True
        final_swot = deterministic_swot

    # ODOP Statutory Cluster Evaluation (PMFME & DPIIT)
    odop_alignment = match_odop(
        state_name=input_data.state_name,
        district_name=input_data.district_name,
        sector=input_data.sector,
        enterprise_name=input_data.enterprise_name,
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
        swot_matrix=final_swot,
        pricing_result=pricing,
        ml_prediction=ml_pred,
        ai_synthesis=synthesis,
        odop_info=odop_alignment,
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
            "logical_source": f"Sarvam AI LLM ({synthesis.model_name})" if not synthesis.is_fallback else "Deterministic Statutory Template Engine",
            "table_or_file": "sarvam_api" if not synthesis.is_fallback else "deterministic_template_matrix",
            "records_matched": 1,
            "status": "Template Fallback" if synthesis.is_fallback else "AI Synthesized",
            "attribution": f"Language: {input_data.language.upper()} ({synthesis.model_name})",
        },
    ]

    data_sources_used.append({
        "layer": "Tier 1: ODOP Cluster Registry",
        "logical_source": "MoFPI PMFME & DPIIT One District One Product Registry",
        "table_or_file": "odop_registry.json",
        "records_matched": 1 if odop_alignment.get("has_odop_record") else 0,
        "status": "Cluster Aligned" if odop_alignment.get("is_aligned") else "Queried OK",
        "attribution": f"District: {odop_alignment.get('district_name')}, Product: {odop_alignment.get('odop_product')} ({odop_alignment.get('status_text')})",
    })

    data_sources_used.append({
        "layer": "Tier 1: Sales Demand & Machine Capacity",
        "logical_source": "Census 2011 Catchment TAM & 37-Profile MSME Machinery Capacity",
        "table_or_file": "msme_machinery_dataset.json + census_raw",
        "records_matched": 1,
        "status": "Calibrated OK",
        "attribution": f"Projected Sales: ₹{input_data.annual_turnover_estimate:,.0f} | Basis: {turnover_audit.get('derivation_basis', 'Triangulated Machine Capacity & Catchment TAM')}",
    })

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
            "annual_turnover_estimate": round(input_data.annual_turnover_estimate, 2),
            "gross_annual_sales": round(input_data.annual_turnover_estimate, 2),
            "working_capital": wc.to_dict(),
            "amortization": amort.to_dict(),
            "dscr": dscr_res.to_dict(),
            "loan_principal": loan_principal,
            "promoter_margin_amount": promoter_margin_val,
            "monthly_net_profit": round(monthly_net_profit, 2),
            "annual_net_profit": round(annual_net_profit, 2),
            "roi_pct": roi_pct,
            "break_even_pct": break_even_pct,
            "break_even_year": bep_res.break_even_year,
            "break_even_year_label": bep_res.break_even_year_label,
            "break_even_month": bep_res.break_even_month,
            "break_even_milestone": bep_res.break_even_milestone,
            "break_even_badge": bep_res.break_even_badge,
            "payback_period_years": bep_res.payback_period_years,
            "equity_payback_years": bep_res.equity_payback_years,
            "break_even_rationale": bep_res.rationale,
            "cpi_inflation_pct": cpi_pct,
            "turnover_derivation_basis": turnover_audit.get("derivation_basis", ""),
            "turnover_capacity_estimate": turnover_audit.get("capacity_turnover"),
            "turnover_velocity_estimate": turnover_audit.get("velocity_turnover"),
        },
        scheme_optimization=[s.to_dict() for s in schemes[:5]],
        ml_viability=ml_pred.to_dict(),
        risk_assessment={
            "risk_points": [r.to_dict() for r in risks],
            "verdict": risk_verdict,
            "composite_grade": risk_verdict.get("overall_severity", "MODERATE"),
            "average_risk_score": risk_verdict.get("average_risk_score", 3.0),
        },
        swot_matrix=final_swot.to_dict(),
        pricing_recommendation=pricing.to_dict(),
        executive_synthesis=synthesis.to_dict(),
        data_sources_used=data_sources_used,
        odop_alignment=odop_alignment,
        location={
            "latitude": resolved_lat,
            "longitude": resolved_lon,
            "source": coord_source,
            "village_name": input_data.village_name,
            "district_name": input_data.district_name,
            "state_name": input_data.state_name,
        } if resolved_lat is not None else None,
    )

    return feasibility_report, dpr_doc


@router.post("/generate", response_model=FeasibilityReport)
async def generate_feasibility(input_data: UserInput, current_user: AuthenticatedUser = Depends(get_current_user)):
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
        }, current_user.uid)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feasibility pipeline error: {str(e)}")


@router.get("/{report_id}", response_model=FeasibilityReport)
async def get_feasibility(report_id: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieves cached feasibility report by ID."""
    cached = await db_manager.get_feasibility_report(report_id, current_user.uid)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Feasibility report '{report_id}' not found.")
    return FeasibilityReport(**cached["report"])


@router.post("/dpr")
async def generate_direct_dpr(
    input_data: UserInput,
    format: str = Query("json", description="Output format: json | markdown | html"),
    lang: str = Query("en", description="Target language: en | hi | mr | ta | te | kn"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Directly transforms user input into official 7-Section Bank DPR with multilingual support."""
    try:
        report, dpr = await _run_pipeline(input_data)
        fmt = format.lower().strip()
        target_lang = lang.lower().strip() if lang else "en"
        trans_service = TranslationService.get_instance()

        if fmt == "html":
            raw_html = dpr_to_html(dpr)
            if target_lang != "en":
                res = await trans_service.translate_text(raw_html, target_language=target_lang, source_language="en", format_type="html")
                return HTMLResponse(content=res.get("translated_text", raw_html), media_type="text/html")
            return HTMLResponse(content=raw_html, media_type="text/html")
        elif fmt == "markdown":
            raw_md = dpr_to_printable_markdown(dpr)
            if target_lang != "en":
                res = await trans_service.translate_text(raw_md, target_language=target_lang, source_language="en", format_type="text")
                return PlainTextResponse(content=res.get("translated_text", raw_md), media_type="text/markdown")
            return PlainTextResponse(content=raw_md, media_type="text/markdown")
        return dpr.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_id}/dpr")
async def get_report_dpr(
    report_id: str,
    format: str = Query("json", description="Output format: json | markdown | html"),
    lang: str = Query("en", description="Target language: en | hi | mr | ta | te | kn"),
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user_optional),
):
    """Retrieves 7-Section Bank DPR for an existing feasibility report with multilingual translation."""
    user_id = current_user.uid if current_user else None
    cached = await db_manager.get_feasibility_report(report_id, user_id)
    if not cached:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    dpr_dict = cached["dpr"]
    dpr_doc = BankDPRDocument(**dpr_dict)

    fmt = format.lower().strip()
    target_lang = lang.lower().strip() if lang else "en"
    trans_service = TranslationService.get_instance()

    if fmt == "html":
        raw_html = dpr_to_html(dpr_doc)
        if target_lang != "en":
            res = await trans_service.translate_text(raw_html, target_language=target_lang, source_language="en", format_type="html")
            return HTMLResponse(content=res.get("translated_text", raw_html), media_type="text/html")
        return HTMLResponse(content=raw_html, media_type="text/html")
    elif fmt == "markdown":
        raw_md = dpr_to_printable_markdown(dpr_doc)
        if target_lang != "en":
            res = await trans_service.translate_text(raw_md, target_language=target_lang, source_language="en", format_type="text")
            return PlainTextResponse(content=res.get("translated_text", raw_md), media_type="text/markdown")
        return PlainTextResponse(content=raw_md, media_type="text/markdown")
    return dpr_dict


@router.post("/recommendations")
async def generate_recommendations(
    input_data: UserInput,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate alternative enterprise recommendations when the original enterprise
    is flagged as RECONSIDER by the ML Viability Classifier.
    Uses Sarvam AI LLM (primary) with deterministic 16-sector catalog fallback.
    """
    try:
        # Build recommendation context from input data
        promoter_pct = 0.05 if input_data.promoter_category.lower() != "general" else 0.10
        margin_capital = input_data.project_cost * promoter_pct

        context = {
            "enterprise_name": input_data.enterprise_name,
            "sector": input_data.sector,
            "business_category": input_data.business_category,
            "state_name": input_data.state_name,
            "district_name": input_data.district_name,
            "village_name": input_data.village_name,
            "is_rural": input_data.is_rural,
            "project_cost": input_data.project_cost,
            "margin_capital": margin_capital,
            "annual_turnover_estimate": input_data.annual_turnover_estimate,
            "promoter_category": input_data.promoter_category,
            "infrastructure_score": input_data.infrastructure_score or 6.0,
            "cpi_inflation_pct": input_data.cpi_inflation_pct or 5.0,
            "weather_risk_score": input_data.weather_risk_score or 0.2,
            "msme_density_per_10k": 8.0,  # Default; actual value computed in pipeline
            "competition_intensity": 0.3,  # Default
            "dscr": 0.0,  # Will be populated from report if available
            "ml_confidence_pct": 0.0,
            "top_risk_factor": "Financial stress indicators",
        }

        result = await get_alternative_recommendations(context)
        logger.info(
            f"🔄 [RECOMMENDATIONS] Enterprise: '{input_data.enterprise_name}' | "
            f"Source: {result['source']} | Count: {result['count']}"
        )
        return result
    except Exception as e:
        logger.error(f"Recommendation engine error: {e}")
        raise HTTPException(status_code=400, detail=f"Recommendation engine error: {str(e)}")


@router.post("/recommendations/from-report")
async def generate_recommendations_from_report(
    report_id: str = Query(..., description="Existing feasibility report ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate alternative recommendations using data from an existing feasibility report.
    This extracts the full context (DSCR, ML confidence, risk factors, etc.) from the
    stored report for more accurate LLM and fallback recommendations.
    """
    try:
        cached = await db_manager.get_feasibility_report(report_id, current_user.uid)
        if not cached:
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

        report = cached.get("report", {})
        inp = report.get("input_parameters", {})
        fin = report.get("financial_analysis", {})
        ml = report.get("ml_viability", {})
        market = report.get("market_demographics", {})

        promoter_pct = 0.05 if str(inp.get("promoter_category", "general")).lower() != "general" else 0.10

        context = {
            "enterprise_name": inp.get("enterprise_name", ""),
            "sector": inp.get("sector", ""),
            "business_category": inp.get("business_category", ""),
            "state_name": inp.get("state_name", ""),
            "district_name": inp.get("district_name", ""),
            "village_name": inp.get("village_name", ""),
            "is_rural": inp.get("is_rural", True),
            "project_cost": inp.get("project_cost", 500000),
            "margin_capital": inp.get("project_cost", 500000) * promoter_pct,
            "annual_turnover_estimate": inp.get("annual_turnover_estimate", 800000),
            "promoter_category": inp.get("promoter_category", "general"),
            "infrastructure_score": fin.get("infrastructure_score", 6.0),
            "cpi_inflation_pct": fin.get("cpi_inflation_pct", 5.0),
            "weather_risk_score": ml.get("feature_values", {}).get("weather_risk_score", 0.2),
            "msme_density_per_10k": market.get("msme_density", {}).get("msme_density_per_10k", 8.0),
            "competition_intensity": market.get("competition", {}).get("competition_intensity_normalized", 0.3),
            "dscr": fin.get("dscr", {}).get("dscr", 0.0),
            "ml_confidence_pct": ml.get("confidence_pct", 0.0),
            "top_risk_factor": ml.get("top_risk_factors", ["Financial stress"])[0] if ml.get("top_risk_factors") else "Financial stress indicators",
        }

        result = await get_alternative_recommendations(context)
        logger.info(
            f"🔄 [RECOMMENDATIONS FROM REPORT] Report: '{report_id}' | "
            f"Source: {result['source']} | Count: {result['count']}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation from report error: {e}")
        raise HTTPException(status_code=400, detail=f"Recommendation engine error: {str(e)}")
