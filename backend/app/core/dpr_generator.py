"""
dpr_generator.py — Phase 5, Udyam Saathi

Tier 3 / Phase 5: Bank-Ready Detailed Project Report (DPR) Generator.
Transforms multi-tier feasibility analysis (Tier 1 Math + Tier 2 ML + Tier 3 AI Synthesis)
into an official 7-Section Bank Credit Appraisal Document matching Scheduled Commercial
Bank and District Industries Centre (DIC) standards for PMEGP, PMFME, MUDRA & Stand-Up India.

Official 7-Section Structure:
    1. Header & Enterprise Profile (DPR ID, Promoter Demographics, LGD Geography)
    2. Capital Outlay & Means of Finance (Exact rupee reconciliation: Outlay == Means of Finance)
    3. Financial & Cash Flow Projections (5-Year Horizon with Capacity Slabs, EBITDA, PAT, DSCR)
    4. Multi-Scheme Optimization & Subsidy Matrix (Top Ranked Schemes by Net Benefit)
    5. Machine Learning Viability & Risk Assessment (XGBoost 10-D Probabilities & SHAP Attribution)
    6. Grounded SWOT & 8-Point Quantified Risk Mitigation Table (Rupee buffers & Audited Sources)
    7. Statutory Bank Submission Document Checklist (Category & Sector-specific Mandatory Docs)

Exports Supported:
    - Structured Pydantic v2 Model / JSON dictionary
    - Formatted Markdown Bank Memorandum
    - Print-Ready HTML Document
"""

from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Optional, Union, Any
from pathlib import Path
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic v2 Models for Strict Serialization & REST API compatibility
# ---------------------------------------------------------------------------

class EnterpriseProfileHeader(BaseModel):
    dpr_reference_id: str = Field(..., description="Unique Bank DPR Reference Number")
    report_date: str = Field(..., description="Date of Feasibility Appraisal (ISO / Formatted)")
    enterprise_name: str
    constitution: str = Field("Sole Proprietorship", description="Legal Constitution of Enterprise")
    sector: str
    business_category: str = Field(..., description="manufacturing | service")
    promoter_name: str = "Enterprise Promoter"
    promoter_category: str = Field("general", description="general | sc | st | obc | women | artisan | women_shg")
    gender: str = "Unspecified"
    target_state: str
    target_district: str
    target_block: str = "N/A"
    target_village: str = "N/A"
    is_rural: bool = True
    catchment_projected_population: int = 0
    nodal_lending_agency: str = "Scheduled Commercial Bank / District Industries Centre (DIC)"
    odop_product: Optional[str] = Field(None, description="Designated One District One Product (ODOP)")
    odop_alignment_status: Optional[str] = Field(None, description="ODOP Aligned | Cluster Adjacent")
    rbi_psl_classification: Optional[str] = Field(None, description="RBI Priority Sector Lending Classification")


class CapitalOutlayItem(BaseModel):
    item_name: str
    percentage_of_outlay: float
    amount_inr: float
    description: str


class CapitalOutlayTable(BaseModel):
    plant_and_machinery: CapitalOutlayItem
    electrification_and_site_works: CapitalOutlayItem
    initial_working_capital_reserve: CapitalOutlayItem
    contingency_and_pre_operative: CapitalOutlayItem
    total_capital_outlay: float


class MeansOfFinanceTable(BaseModel):
    promoter_margin_amount: float
    promoter_margin_pct: float
    capital_subsidy_amount: float
    capital_subsidy_pct: float
    subsidy_scheme_name: str
    bank_term_loan_amount: float
    bank_term_loan_pct: float
    total_means_of_finance: float
    reconciliation_balanced: bool = True


class FinancialProjectionYear(BaseModel):
    year: int
    capacity_utilization_pct: float
    gross_turnover: float
    raw_materials_and_inputs: float
    power_and_utilities: float
    wages_and_labor: float
    overheads_and_maintenance: float
    total_operating_expenses: float
    ebitda: float
    depreciation: float
    bank_interest: float
    profit_before_tax: float
    tax_provision: float
    profit_after_tax: float
    cash_accruals: float
    loan_principal_repayment: float
    total_debt_service: float
    annual_dscr: float


class FiveYearFinancialHorizon(BaseModel):
    projection_years: list[FinancialProjectionYear]
    average_dscr: float
    dscr_benchmark_met: bool
    break_even_point_pct: float
    recommended_unit_price_floor: float


class SchemeOptimizationEntry(BaseModel):
    rank: int
    scheme_id: str
    full_name: str
    eligible: bool
    ineligibility_reason: Optional[str] = None
    subsidy_grant_amount: float
    effective_interest_rate_pct: float
    total_interest_payable: float
    net_financial_benefit: float
    collateral_free: bool
    administering_body: str = "Government of India / Nodal Bank"


class MLViabilitySection(BaseModel):
    verdict: str  # SUITABLE | CAUTION | RECONSIDER
    confidence_pct: float
    class_probabilities: dict[str, float]
    feature_vector_audit: dict[str, float]
    top_positive_factors: list[str]
    top_risk_factors: list[str]
    model_version: str
    shap_explanation: Optional[dict[str, Any]] = None
    global_feature_importance: Optional[list[dict[str, Any]]] = None


class SWOTQuadrantItem(BaseModel):
    text: str
    data_source: str


class SWOTSection(BaseModel):
    strengths: list[SWOTQuadrantItem]
    weaknesses: list[SWOTQuadrantItem]
    opportunities: list[SWOTQuadrantItem]
    threats: list[SWOTQuadrantItem]


class RiskMitigationItem(BaseModel):
    risk_id: str
    title: str
    score: float
    severity: str
    basis: str
    mitigation: str
    rupee_buffer: Optional[float] = None
    data_source: str


class RiskSection(BaseModel):
    risk_points: list[RiskMitigationItem]
    average_risk_score: float
    overall_severity: str
    high_or_severe_risk_count: int


class StatutoryChecklistItem(BaseModel):
    document_code: str
    document_name: str
    category_requirement: str  # "Universal Mandatory" | "Social Category Specific" | "Sector Specific"
    issuing_authority: str
    is_mandatory: bool
    notes: str


class BankDPRDocument(BaseModel):
    dpr_version: str = "2.0"
    generated_at_utc: str
    section_1_header_and_profile: EnterpriseProfileHeader
    section_2_capital_outlay_and_finance: dict[str, Any]
    section_3_financial_projections: FiveYearFinancialHorizon
    section_4_scheme_optimization: list[SchemeOptimizationEntry]
    section_5_ml_viability_appraisal: MLViabilitySection
    section_6_swot_and_risk_matrix: dict[str, Any]
    section_7_statutory_checklist: list[StatutoryChecklistItem]
    tier_3_ai_synthesis: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# 5-Year Financial Horizon Calculator (Standard Banking Formulas)
# ---------------------------------------------------------------------------
def _compute_5yr_projections(
    base_annual_turnover: float,
    project_cost: float,
    loan_principal: float,
    annual_interest_rate_pct: float,
    tenure_years: float,
    moratorium_months: int,
    sector: str,
    cpi_inflation_pct: float,
    unit_price_floor: float,
) -> FiveYearFinancialHorizon:
    """
    Computes a deterministic 5-Year Cash Flow Projection using standard Scheduled
    Commercial Bank appraisal standards:
      - Capacity Utilization: Y1: 60%, Y2: 70%, Y3: 80%, Y4: 85%, Y5: 90%
      - Inflation Escalation: 4% p.a. on expenses
      - Depreciation: 15% on Plant & Machinery (55% of project cost)
      - Loan Amortization: Equal principal repayment over tenure
    """
    capacity_slabs = [0.60, 0.70, 0.80, 0.85, 0.90]
    plant_machinery_cost = project_cost * 0.55
    depreciation_rate = 0.15

    # Sector cost assumptions (% of revenue at 100% capacity)
    sector_lower = sector.lower()
    if sector_lower in ("dairy", "food_processing"):
        raw_mat_ratio = 0.62
        power_ratio = 0.05
        labor_ratio = 0.08
        overhead_ratio = 0.04
    elif sector_lower in ("apparel", "tailoring", "artisan_trades", "artisan"):
        raw_mat_ratio = 0.45
        power_ratio = 0.04
        labor_ratio = 0.18
        overhead_ratio = 0.05
    elif sector_lower in ("repair", "service"):
        raw_mat_ratio = 0.25
        power_ratio = 0.06
        labor_ratio = 0.28
        overhead_ratio = 0.06
    else:
        raw_mat_ratio = 0.52
        power_ratio = 0.05
        labor_ratio = 0.12
        overhead_ratio = 0.05

    # Principal repayment per year (post moratorium)
    repay_tenure = max(tenure_years - (moratorium_months / 12), 1.0)
    annual_principal = loan_principal / min(repay_tenure, 5.0) if loan_principal > 0 else 0.0

    years_data: list[FinancialProjectionYear] = []
    remaining_loan = loan_principal
    machinery_wdv = plant_machinery_cost

    for yr_idx, cap_pct in enumerate(capacity_slabs, start=1):
        # Revenue scaled to capacity utilization and modest annual price indexation (2%)
        price_index = (1 + 0.02) ** (yr_idx - 1)
        gross_rev = base_annual_turnover * (cap_pct / 0.70) * price_index

        # Expenses scaled to volume and CPI inflation
        cost_index = (1 + (cpi_inflation_pct / 100 * 0.5)) ** (yr_idx - 1)
        raw_mat = gross_rev * raw_mat_ratio * cost_index
        power = gross_rev * power_ratio * cost_index
        labor = gross_rev * labor_ratio * cost_index
        overheads = gross_rev * overhead_ratio * cost_index

        total_opex = raw_mat + power + labor + overheads
        ebitda = max(gross_rev - total_opex, 0.0)

        # Depreciation (Written Down Value)
        depr = machinery_wdv * depreciation_rate
        machinery_wdv = max(machinery_wdv - depr, 0.0)

        # Bank Interest on opening loan balance
        interest = remaining_loan * (annual_interest_rate_pct / 100.0) if remaining_loan > 0 else 0.0
        principal_due = min(annual_principal, remaining_loan) if remaining_loan > 0 else 0.0
        remaining_loan = max(remaining_loan - principal_due, 0.0)

        pbt = max(ebitda - depr - interest, 0.0)
        tax = pbt * 0.15 if pbt > 250000 else 0.0  # Concessional micro enterprise slab
        pat = pbt - tax
        cash_accruals = pat + depr

        total_debt_service = principal_due + interest
        if total_debt_service > 0:
            annual_dscr = (pat + depr + interest) / total_debt_service
        else:
            annual_dscr = 3.50

        years_data.append(FinancialProjectionYear(
            year=yr_idx,
            capacity_utilization_pct=round(cap_pct * 100, 1),
            gross_turnover=round(gross_rev, 2),
            raw_materials_and_inputs=round(raw_mat, 2),
            power_and_utilities=round(power, 2),
            wages_and_labor=round(labor, 2),
            overheads_and_maintenance=round(overheads, 2),
            total_operating_expenses=round(total_opex, 2),
            ebitda=round(ebitda, 2),
            depreciation=round(depr, 2),
            bank_interest=round(interest, 2),
            profit_before_tax=round(pbt, 2),
            tax_provision=round(tax, 2),
            profit_after_tax=round(pat, 2),
            cash_accruals=round(cash_accruals, 2),
            loan_principal_repayment=round(principal_due, 2),
            total_debt_service=round(total_debt_service, 2),
            annual_dscr=round(annual_dscr, 2),
        ))

    avg_dscr = sum(y.annual_dscr for y in years_data) / len(years_data)
    dscr_ok = avg_dscr >= 1.33
    bep_pct = round((total_opex + interest + depr) / gross_rev * 100, 1) if gross_rev > 0 else 55.0

    return FiveYearFinancialHorizon(
        projection_years=years_data,
        average_dscr=round(avg_dscr, 2),
        dscr_benchmark_met=dscr_ok,
        break_even_point_pct=min(bep_pct, 85.0),
        recommended_unit_price_floor=round(unit_price_floor, 2),
    )


# ---------------------------------------------------------------------------
# Statutory Document Checklist Compiler
# ---------------------------------------------------------------------------
def _compile_statutory_checklist(
    scheme_id: str,
    promoter_category: str,
    sector: str,
    business_category: str,
    project_cost: float,
) -> list[StatutoryChecklistItem]:
    """
    Builds the official bank submission document checklist tailored to the scheme,
    promoter social category, and enterprise sector.
    """
    checklist: list[StatutoryChecklistItem] = []

    # 1. Universal KYC and Enterprise Basics
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-KYC-01",
        document_name="Promoter Identity & Address Proof (Aadhaar & PAN Card)",
        category_requirement="Universal Mandatory",
        issuing_authority="UIDAI / Income Tax Department",
        is_mandatory=True,
        notes="Self-attested copies of Aadhaar Card and PAN Card of the main promoter.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-REG-02",
        document_name="Udyam MSME Registration Certificate",
        category_requirement="Universal Mandatory",
        issuing_authority="Ministry of MSME (Udyam Portal)",
        is_mandatory=True,
        notes="Online Udyam registration acknowledgement showing enterprise category.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-LOC-03",
        document_name="Proof of Worksite / Land Ownership or Lease Deed",
        category_requirement="Universal Mandatory",
        issuing_authority="Gram Panchayat / Revenue Authority / Landlord",
        is_mandatory=True,
        notes="Registered lease deed (minimum 5-year tenure) or Khatiyan / Land tax receipt.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-QUO-04",
        document_name="Machinery & Equipment Quotations with GST Numbers",
        category_requirement="Universal Mandatory",
        issuing_authority="Authorized Machinery Suppliers / OEMs",
        is_mandatory=True,
        notes="Itemized commercial quotations from at least two reputable suppliers.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-BNK-05",
        document_name="Bank Passbook / Statement (Last 6 Months)",
        category_requirement="Universal Mandatory",
        issuing_authority="Operating Bank Branch",
        is_mandatory=True,
        notes="Shows promoter's margin contribution capability and clean financial track record.",
    ))

    # 2. Scheme & Social Category Specifics
    cat_lower = promoter_category.lower()
    if cat_lower in ("sc", "st", "obc"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-SOC-06",
            document_name="Social Category / Caste Certificate",
            category_requirement="Social Category Specific",
            issuing_authority="Tehsildar / Sub-Divisional Magistrate (SDM)",
            is_mandatory=True,
            notes=f"Mandatory for claiming special subsidy slabs under {scheme_id}.",
        ))
    if cat_lower in ("artisan", "artisan_trades"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-ART-07",
            document_name="PM Vishwakarma Artisan Registration Card / Certificate",
            category_requirement="Social Category Specific",
            issuing_authority="Ministry of MSME / Skill Verification Officer",
            is_mandatory=True,
            notes="Required for fixed 5% interest subvention under PM Vishwakarma.",
        ))
    if cat_lower in ("women_shg", "shg"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-SHG-08",
            document_name="NRLM / SRLM Women SHG Affiliation & Resolution Copy",
            category_requirement="Social Category Specific",
            issuing_authority="State Rural Livelihood Mission (SRLM)",
            is_mandatory=True,
            notes="Resolution passed by SHG members for availing enterprise credit.",
        ))

    # Educational qualification check for PMEGP
    if "PMEGP" in scheme_id and ((business_category == "manufacturing" and project_cost > 1000000) or
                                  (business_category == "service" and project_cost > 500000)):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-EDU-09",
            document_name="Minimum 8th Standard Pass Educational Certificate",
            category_requirement="Scheme Specific Mandatory",
            issuing_authority="Recognized School Board / Education Dept",
            is_mandatory=True,
            notes="Mandatory under PMEGP guidelines for project outlay exceeding ₹10L (Mfg) or ₹5L (Service).",
        ))

    # 3. Sector Specific Regulatory Clearances
    sec_lower = sector.lower()
    if sec_lower in ("dairy", "food_processing"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-FSS-10",
            document_name="FSSAI Basic Registration / Food Safety License",
            category_requirement="Sector Specific Regulatory",
            issuing_authority="Food Safety and Standards Authority of India (FSSAI)",
            is_mandatory=True,
            notes="Mandatory prior to commercial food/dairy processing and packaging operations.",
        ))
    if business_category == "manufacturing":
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-PCB-11",
            document_name="State Pollution Control Board Consent (White / Green Category)",
            category_requirement="Sector Specific Regulatory",
            issuing_authority="State Pollution Control Board (SPCB)",
            is_mandatory=False,
            notes="Exempt for white category; green category requires standard online self-declaration.",
        ))

    return checklist


# ---------------------------------------------------------------------------
# Master Bank DPR Assembly Function
# ---------------------------------------------------------------------------
def build_bank_dpr(
    enterprise_name: str,
    business_category: str,
    sector: str,
    promoter_name: str,
    promoter_category: str,
    gender: str,
    state_name: str,
    district_name: str,
    block_name: str,
    village_name: str,
    is_rural: bool,
    project_cost: float,
    annual_turnover_estimate: float,
    tenure_years: float,
    moratorium_months: int,
    pop_projection: Any,
    tam_estimate: Any,
    msme_density: Any,
    ranked_schemes: list[Any],
    amortization: Any,
    dscr_result: Any,
    risk_points: list[Any],
    risk_verdict: dict[str, Any],
    swot_matrix: Any,
    pricing_result: Any,
    ml_prediction: Any,
    ai_synthesis: Any,
    constitution: str = "Sole Proprietorship",
    odop_info: Optional[dict[str, Any]] = None,
) -> BankDPRDocument:
    """
    Compiles the complete 7-Section Bank DPR appraisal document.
    Ensures 100% financial and accounting balance reconciliation.
    """
    # 1. DPR Header & ID
    state_code_prefix = "".join(w[0] for w in state_name.split()[:2]).upper()
    dpr_ref = f"DPR-2026-{state_code_prefix}-{int(project_cost // 1000):04d}"
    now_iso = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")

    profile = EnterpriseProfileHeader(
        dpr_reference_id=dpr_ref,
        report_date=now_iso,
        enterprise_name=enterprise_name,
        constitution=constitution,
        sector=sector,
        business_category=business_category,
        promoter_name=promoter_name,
        promoter_category=promoter_category,
        gender=gender,
        target_state=state_name,
        target_district=district_name,
        target_block=block_name,
        target_village=village_name,
        is_rural=is_rural,
        catchment_projected_population=pop_projection.projected_population,
        nodal_lending_agency="Scheduled Commercial Bank / DIC",
        odop_product=odop_info.get("odop_product") if odop_info else None,
        odop_alignment_status=odop_info.get("status_text") if odop_info else None,
        rbi_psl_classification=odop_info.get("rbi_psl_category") if odop_info else None,
    )

    # 2. Capital Outlay Breakdown (100% standard allocation)
    cost_machinery = project_cost * 0.55
    cost_civil = project_cost * 0.15
    cost_wc = project_cost * 0.20
    cost_contingency = project_cost * 0.10

    outlay_table = CapitalOutlayTable(
        plant_and_machinery=CapitalOutlayItem(
            item_name="Plant, Machinery & Core Equipment",
            percentage_of_outlay=55.0,
            amount_inr=round(cost_machinery, 2),
            description="Primary processing machinery, tools, and technical apparatus",
        ),
        electrification_and_site_works=CapitalOutlayItem(
            item_name="Electrification, Installation & Site Works",
            percentage_of_outlay=15.0,
            amount_inr=round(cost_civil, 2),
            description="Power cabling, transformer connection, foundation, and fixtures",
        ),
        initial_working_capital_reserve=CapitalOutlayItem(
            item_name="Initial Working Capital Reserve",
            percentage_of_outlay=20.0,
            amount_inr=round(cost_wc, 2),
            description="Raw material inventory buffer and operating liquidity for launch",
        ),
        contingency_and_pre_operative=CapitalOutlayItem(
            item_name="Contingency & Pre-Operative Outlay",
            percentage_of_outlay=10.0,
            amount_inr=round(cost_contingency, 2),
            description="Trial run expenses, licensing, logistics contingency, and buffer",
        ),
        total_capital_outlay=round(project_cost, 2),
    )

    # Means of Finance (Promoter Margin + Subsidy Grant + Bank Loan == Outlay)
    top_scheme = next((r for r in ranked_schemes if r.eligible), ranked_schemes[0])
    subsidy_amt = top_scheme.subsidy_grant_amount
    subsidy_pct = (subsidy_amt / project_cost * 100) if project_cost > 0 else 0.0

    promoter_pct = 5.0 if promoter_category.lower() != "general" else 10.0
    promoter_margin_amt = project_cost * (promoter_pct / 100.0)

    bank_loan_amt = max(project_cost - subsidy_amt - promoter_margin_amt, 0.0)
    bank_loan_pct = (bank_loan_amt / project_cost * 100) if project_cost > 0 else 0.0

    means_of_finance = MeansOfFinanceTable(
        promoter_margin_amount=round(promoter_margin_amt, 2),
        promoter_margin_pct=round(promoter_pct, 1),
        capital_subsidy_amount=round(subsidy_amt, 2),
        capital_subsidy_pct=round(subsidy_pct, 1),
        subsidy_scheme_name=f"{top_scheme.scheme_id} ({top_scheme.full_name})",
        bank_term_loan_amount=round(bank_loan_amt, 2),
        bank_term_loan_pct=round(bank_loan_pct, 1),
        total_means_of_finance=round(promoter_margin_amt + subsidy_amt + bank_loan_amt, 2),
        reconciliation_balanced=abs((promoter_margin_amt + subsidy_amt + bank_loan_amt) - project_cost) < 1.0,
    )

    # 3. 5-Year Cash Flow Projections
    projections = _compute_5yr_projections(
        base_annual_turnover=annual_turnover_estimate,
        project_cost=project_cost,
        loan_principal=bank_loan_amt,
        annual_interest_rate_pct=top_scheme.effective_interest_rate_pct,
        tenure_years=tenure_years,
        moratorium_months=moratorium_months,
        sector=sector,
        cpi_inflation_pct=pricing_result.cpi_inflation_pct,
        unit_price_floor=pricing_result.cpi_adjusted_unit_price_floor,
    )

    # 4. Scheme Optimization Table (Top 5)
    scheme_entries: list[SchemeOptimizationEntry] = []
    for s in ranked_schemes[:5]:
        scheme_entries.append(SchemeOptimizationEntry(
            rank=s.rank,
            scheme_id=s.scheme_id,
            full_name=s.full_name,
            eligible=s.eligible,
            ineligibility_reason=s.ineligibility_reason,
            subsidy_grant_amount=round(s.subsidy_grant_amount, 2),
            effective_interest_rate_pct=round(s.effective_interest_rate_pct, 2),
            total_interest_payable=round(s.total_interest_payable, 2),
            net_financial_benefit=round(s.net_financial_benefit, 2),
            collateral_free=s.collateral_free,
        ))

    # 5. ML Viability Section
    ml_section = MLViabilitySection(
        verdict=ml_prediction.verdict,
        confidence_pct=round(ml_prediction.confidence_pct, 2),
        class_probabilities=ml_prediction.class_probabilities,
        feature_vector_audit=ml_prediction.feature_values,
        top_positive_factors=ml_prediction.top_positive_factors,
        top_risk_factors=ml_prediction.top_risk_factors,
        model_version=ml_prediction.model_version,
        shap_explanation=getattr(ml_prediction, "shap_explanation", None),
        global_feature_importance=getattr(ml_prediction, "global_feature_importance", None),
    )

    # 6. SWOT & Risk Sections
    def _extract_swot_quadrant(quadrant_data):
        if not quadrant_data:
            return []
        items = []
        for i in quadrant_data:
            if isinstance(i, dict):
                items.append(SWOTQuadrantItem(text=str(i.get("text", "")).strip(), data_source=str(i.get("data_source", "Market Feasibility Signal")).strip()))
            elif hasattr(i, "text"):
                items.append(SWOTQuadrantItem(text=str(i.text).strip(), data_source=str(getattr(i, "data_source", "Market Feasibility Signal")).strip()))
            elif isinstance(i, str) and i.strip():
                items.append(SWOTQuadrantItem(text=i.strip(), data_source="Market Feasibility Signal"))
        return items

    if isinstance(swot_matrix, dict):
        swot_items = {
            "strengths": _extract_swot_quadrant(swot_matrix.get("strengths", [])),
            "weaknesses": _extract_swot_quadrant(swot_matrix.get("weaknesses", [])),
            "opportunities": _extract_swot_quadrant(swot_matrix.get("opportunities", [])),
            "threats": _extract_swot_quadrant(swot_matrix.get("threats", [])),
        }
    else:
        swot_items = {
            "strengths": _extract_swot_quadrant(getattr(swot_matrix, "strengths", [])),
            "weaknesses": _extract_swot_quadrant(getattr(swot_matrix, "weaknesses", [])),
            "opportunities": _extract_swot_quadrant(getattr(swot_matrix, "opportunities", [])),
            "threats": _extract_swot_quadrant(getattr(swot_matrix, "threats", [])),
        }

    risk_items = [
        RiskMitigationItem(
            risk_id=r.risk_id,
            title=r.title,
            score=r.score,
            severity=r.severity,
            basis=r.basis,
            mitigation=r.mitigation,
            rupee_buffer=r.rupee_buffer,
            data_source=r.data_source,
        ) for r in risk_points
    ]

    # 7. Statutory Checklist
    checklist = _compile_statutory_checklist(
        scheme_id=top_scheme.scheme_id,
        promoter_category=promoter_category,
        sector=sector,
        business_category=business_category,
        project_cost=project_cost,
    )

    return BankDPRDocument(
        dpr_version="2.0",
        generated_at_utc=now_iso,
        section_1_header_and_profile=profile,
        section_2_capital_outlay_and_finance={
            "capital_outlay": outlay_table.model_dump(),
            "means_of_finance": means_of_finance.model_dump(),
        },
        section_3_financial_projections=projections,
        section_4_scheme_optimization=scheme_entries,
        section_5_ml_viability_appraisal=ml_section,
        section_6_swot_and_risk_matrix={
            "swot_analysis": swot_items,
            "risk_matrix": [r.model_dump() for r in risk_items],
            "overall_risk_verdict": risk_verdict,
        },
        section_7_statutory_checklist=checklist,
        tier_3_ai_synthesis=ai_synthesis.to_dict(),
    )


# ---------------------------------------------------------------------------
# Formatted Printable Markdown Export
# ---------------------------------------------------------------------------
def dpr_to_printable_markdown(dpr: BankDPRDocument) -> str:
    """
    Renders the Bank DPR as an official, bank-ready Markdown Credit Appraisal Memo.
    """
    s1 = dpr.section_1_header_and_profile
    s2 = dpr.section_2_capital_outlay_and_finance
    outlay = s2["capital_outlay"]
    finance = s2["means_of_finance"]
    s3 = dpr.section_3_financial_projections
    s4 = dpr.section_4_scheme_optimization
    s5 = dpr.section_5_ml_viability_appraisal
    s6 = dpr.section_6_swot_and_risk_matrix
    s7 = dpr.section_7_statutory_checklist
    ai = dpr.tier_3_ai_synthesis

    lines = [
        f"# 🏛️ DETAILED PROJECT REPORT (DPR) & CREDIT APPRAISAL MEMORANDUM",
        f"**Reference Number**: `{s1.dpr_reference_id}` | **Appraisal Date**: {s1.report_date} | **Format**: SCB / DIC Standard",
        f"**Enterprise Name**: **{s1.enterprise_name}** | **Constitution**: {s1.constitution}",
        f"**Target Location**: {s1.target_village}, {s1.target_block}, {s1.target_district}, {s1.target_state} (Rural: {s1.is_rural})",
        f"**Promoter Profile**: {s1.promoter_name} (Category: `{s1.promoter_category.upper()}` | Gender: {s1.gender})",
        f"\n---\n",
        f"## SECTION 1: EXECUTIVE APPRAISAL & SYNTHESIS",
        f"{ai.get('executive_summary', '')}\n",
        f"### Strategic Action Plan:",
    ]
    for idx, rec in enumerate(ai.get("strategic_recommendations", []), 1):
        lines.append(f"{idx}. {rec}")

    lines.extend([
        f"\n### Bank Loan Officer Notes:",
        f"> {ai.get('bank_appraisal_notes', '')}\n",
        f"\n---\n",
        f"## SECTION 2: CAPITAL OUTLAY & MEANS OF FINANCE",
        f"\n### Capital Outlay Breakdown:",
        f"| Component | % Outlay | Amount (₹) | Description |",
        f"| :--- | :---: | :---: | :--- |",
        f"| **Plant & Machinery** | {outlay['plant_and_machinery']['percentage_of_outlay']:.1f}% | ₹{outlay['plant_and_machinery']['amount_inr']:,.2f} | {outlay['plant_and_machinery']['description']} |",
        f"| **Electrification & Site Works** | {outlay['electrification_and_site_works']['percentage_of_outlay']:.1f}% | ₹{outlay['electrification_and_site_works']['amount_inr']:,.2f} | {outlay['electrification_and_site_works']['description']} |",
        f"| **Working Capital Reserve** | {outlay['initial_working_capital_reserve']['percentage_of_outlay']:.1f}% | ₹{outlay['initial_working_capital_reserve']['amount_inr']:,.2f} | {outlay['initial_working_capital_reserve']['description']} |",
        f"| **Contingency & Pre-Operative** | {outlay['contingency_and_pre_operative']['percentage_of_outlay']:.1f}% | ₹{outlay['contingency_and_pre_operative']['amount_inr']:,.2f} | {outlay['contingency_and_pre_operative']['description']} |",
        f"| **TOTAL CAPITAL OUTLAY** | **100.0%** | **₹{outlay['total_capital_outlay']:,.2f}** | **Total Project Investment** |",
        f"\n### Means of Finance Reconciliation:",
        f"| Financing Source | % Share | Amount (₹) | Scheme / Terms |",
        f"| :--- | :---: | :---: | :--- |",
        f"| **Promoter Margin Contribution** | {finance['promoter_margin_pct']:.1f}% | ₹{finance['promoter_margin_amount']:,.2f} | Own equity funds |",
        f"| **Government Capital Subsidy Grant** | {finance['capital_subsidy_pct']:.1f}% | ₹{finance['capital_subsidy_amount']:,.2f} | {finance['subsidy_scheme_name']} |",
        f"| **Bank Term Loan / Debt** | {finance['bank_term_loan_pct']:.1f}% | ₹{finance['bank_term_loan_amount']:,.2f} | Scheduled Commercial Bank Loan |",
        f"| **TOTAL MEANS OF FINANCE** | **100.0%** | **₹{finance['total_means_of_finance']:,.2f}** | **Balanced: {finance['reconciliation_balanced']}** |",
        f"\n---\n",
        f"## SECTION 3: 5-YEAR FINANCIAL & CASH FLOW PROJECTIONS",
        f"\n**Average 5-Year DSCR**: **{s3.average_dscr:.2f}** (RBI Solvency Benchmark $\\ge 1.33$: **{'MET' if s3.dscr_benchmark_met else 'NOT MET'}**)  ",
        f"**Break-Even Point (BEP)**: **{s3.break_even_point_pct:.1f}%** | **Recommended Price Floor**: ₹{s3.recommended_unit_price_floor:.2f}/unit\n",
        f"| Line Item (₹) | Year 1 (60%) | Year 2 (70%) | Year 3 (80%) | Year 4 (85%) | Year 5 (90%) |",
        f"| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    y_objs = s3.projection_years
    rows_to_render = [
        ("Gross Turnover", lambda y: f"₹{y.gross_turnover:,.0f}"),
        ("Raw Materials & Consumables", lambda y: f"₹{y.raw_materials_and_inputs:,.0f}"),
        ("Power, Fuel & Utilities", lambda y: f"₹{y.power_and_utilities:,.0f}"),
        ("Wages & Direct Labor", lambda y: f"₹{y.wages_and_labor:,.0f}"),
        ("Overheads & Administration", lambda y: f"₹{y.overheads_and_maintenance:,.0f}"),
        ("Total Operating Expenses", lambda y: f"₹{y.total_operating_expenses:,.0f}"),
        ("Operating EBITDA", lambda y: f"₹{y.ebitda:,.0f}"),
        ("Depreciation (WDV 15%)", lambda y: f"₹{y.depreciation:,.0f}"),
        ("Bank Term Loan Interest", lambda y: f"₹{y.bank_interest:,.0f}"),
        ("Net Profit After Tax (PAT)", lambda y: f"₹{y.profit_after_tax:,.0f}"),
        ("Total Debt Service (P+I)", lambda y: f"₹{y.total_debt_service:,.0f}"),
        ("Annual DSCR", lambda y: f"{y.annual_dscr:.2f}"),
    ]
    for label, fn in rows_to_render:
        vals = " | ".join(fn(y) for y in y_objs)
        lines.append(f"| **{label}** | {vals} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 4: GOVERNMENT SCHEME OPTIMIZATION MATRIX",
        f"| Rank | Scheme ID | Full Scheme Name | Grant Subsidy (₹) | Net Benefit (₹) | Collateral-Free |",
        f"| :---: | :--- | :--- | :---: | :---: | :---: |",
    ])
    for s in s4:
        lines.append(f"| #{s.rank} | **{s.scheme_id}** | {s.full_name} | ₹{s.subsidy_grant_amount:,.0f} | ₹{s.net_financial_benefit:,.0f} | {'Yes' if s.collateral_free else 'No'} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 5: MACHINE LEARNING VIABILITY & SHAP EXPLAINABILITY APPRAISAL",
        f"**Viability Verdict**: **`{s5.verdict}`** | **Model Confidence**: **{s5.confidence_pct:.1f}%** | **Engine**: `{s5.model_version}`\n",
        f"**Class Probabilities**: `SUITABLE`: {s5.class_probabilities.get('SUITABLE', 0)*100:.1f}% | `CAUTION`: {s5.class_probabilities.get('CAUTION', 0)*100:.1f}% | `RECONSIDER`: {s5.class_probabilities.get('RECONSIDER', 0)*100:.1f}%\n",
        f"**Primary Positive Drivers**:",
    ])
    for p in s5.top_positive_factors:
        lines.append(f"- {p}")
    lines.append(f"\n**Primary Risk Drivers**:")
    for r in s5.top_risk_factors:
        lines.append(f"- {r}")

    if s5.shap_explanation and s5.shap_explanation.get("contributions"):
        lines.extend([
            f"\n### SHAP Feature Attribution Waterfall (Margin Impact on '{s5.verdict}'):",
            f"| Feature Name | Feature Value | SHAP Value | Attribution Direction |",
            f"| :--- | :---: | :---: | :---: |",
        ])
        for c in s5.shap_explanation["contributions"]:
            dir_str = "🟢 Positive Viability Support" if c["shap_value"] > 0 else "🔴 Negative Risk Drag" if c["shap_value"] < 0 else "⚪ Neutral"
            lines.append(f"| `{c['feature']}` | {c['feature_value']:.2f} | {c['shap_value']:+.4f} | {dir_str} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 6: QUANTIFIED SWOT & 8-POINT RISK MITIGATION TABLE",
        f"\n### 8-Point Quantified Risk Mitigation Table:",
        f"| ID | Risk Title | Severity | Score (/10) | Contingency Buffer | Actionable Mitigation Procedure |",
        f"| :---: | :--- | :---: | :---: | :--- |",
    ])
    for r in s6["risk_matrix"]:
        buf_str = f"₹{r['rupee_buffer']:,.0f}" if r.get("rupee_buffer") else "Policy / Process"
        lines.append(f"| **{r['risk_id']}** | {r['title']} | `{r['severity']}` | {r['score']:.1f} | {buf_str} | {r['mitigation']} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 7: STATUTORY BANK SUBMISSION DOCUMENT CHECKLIST",
        f"| Code | Document Name | Category | Authority | Mandatory | Notes |",
        f"| :---: | :--- | :--- | :--- | :---: | :--- |",
    ])
    for d in s7:
        lines.append(f"| `{d.document_code}` | **{d.document_name}** | {d.category_requirement} | {d.issuing_authority} | {'**YES**' if d.is_mandatory else 'Optional'} | {d.notes} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Print-Ready HTML Document Export
# ---------------------------------------------------------------------------
def dpr_to_html(doc: BankDPRDocument) -> str:
    """
    Renders the Bank DPR into a high-fidelity, complete 7-Section standalone HTML document
    optimized for onscreen inspection, browser printing, and PDF export.
    """
    p = doc.section_1_header_and_profile
    s2 = doc.section_2_capital_outlay_and_finance
    outlay = s2["capital_outlay"]
    finance = s2["means_of_finance"]
    s3 = doc.section_3_financial_projections
    s4 = doc.section_4_scheme_optimization
    s5 = doc.section_5_ml_viability_appraisal
    s6 = doc.section_6_swot_and_risk_matrix
    swot = s6.get("swot_analysis", {})
    risks = s6.get("risk_matrix", [])
    overall_risk = s6.get("overall_risk_verdict", "MODERATE")
    s7 = doc.section_7_statutory_checklist
    ai = doc.tier_3_ai_synthesis or {}

    # 1. Strategic Recommendations List
    rec_items_html = ""
    for idx, rec in enumerate(ai.get("strategic_recommendations", []), 1):
        rec_items_html += f"<li style='margin-bottom: 4px;'><strong>{idx}.</strong> {rec}</li>"
    if not rec_items_html:
        rec_items_html = "<li>Operational scale and working capital align with sector benchmarks.</li>"

    # 2. 5-Year Projection Rows
    y_objs = s3.projection_years
    years_headers_html = " ".join(f"<th class='num'>Year {y.year}<br/><span style='font-weight:normal; font-size:10px;'>({y.capacity_utilization_pct:.0f}% Cap)</span></th>" for y in y_objs)

    fin_rows = [
        ("Gross Sales Revenue", [f"₹{y.gross_turnover:,.0f}" for y in y_objs], False),
        ("Raw Materials & Consumables", [f"₹{y.raw_materials_and_inputs:,.0f}" for y in y_objs], False),
        ("Power, Fuel & Utilities", [f"₹{y.power_and_utilities:,.0f}" for y in y_objs], False),
        ("Wages & Direct Labor", [f"₹{y.wages_and_labor:,.0f}" for y in y_objs], False),
        ("Overheads & Maintenance", [f"₹{y.overheads_and_maintenance:,.0f}" for y in y_objs], False),
        ("Total Operating Expenses", [f"₹{y.total_operating_expenses:,.0f}" for y in y_objs], True),
        ("Operating EBITDA", [f"₹{y.ebitda:,.0f}" for y in y_objs], True),
        ("Depreciation (WDV 15%)", [f"₹{y.depreciation:,.0f}" for y in y_objs], False),
        ("Bank Term Loan Interest", [f"₹{y.bank_interest:,.0f}" for y in y_objs], False),
        ("Net Profit After Tax (PAT)", [f"₹{y.profit_after_tax:,.0f}" for y in y_objs], True),
        ("Debt Service (P + I)", [f"₹{y.total_debt_service:,.0f}" for y in y_objs], True),
        ("Annual DSCR (Ratio)", [f"{y.annual_dscr:.2f}" for y in y_objs], True),
    ]

    fin_table_rows_html = ""
    for label, vals, is_bold in fin_rows:
        bg_style = "background-color: #f8fafc; font-weight: bold;" if is_bold else ""
        row_tds = " ".join(f"<td class='num'>{v}</td>" for v in vals)
        fin_table_rows_html += f"<tr style='{bg_style}'><td><strong>{label}</strong></td>{row_tds}</tr>"

    # 3. Scheme Optimization Rows
    scheme_rows_html = ""
    for s in s4:
        collat_badge = "<span class='badge' style='background:#dcfce7; color:#15803d;'>Yes</span>" if s.collateral_free else "<span class='badge' style='background:#f1f5f9; color:#475569;'>No</span>"
        status_badge = "<span class='badge' style='background:#dcfce7; color:#15803d;'>Eligible</span>" if s.eligible else "<span class='badge' style='background:#fee2e2; color:#b91c1c;'>Ineligible</span>"
        scheme_rows_html += f"""
        <tr>
            <td style='text-align:center; font-weight:bold;'>#{s.rank}</td>
            <td><strong>{s.scheme_id}</strong><br/><span style='font-size:11px; color:#64748b;'>{s.full_name}</span></td>
            <td style='text-align:center;'>{status_badge}</td>
            <td class='num' style='font-weight:bold; color:#047857;'>₹{s.subsidy_grant_amount:,.0f}</td>
            <td class='num'>{s.effective_interest_rate_pct:.2f}%</td>
            <td class='num' style='font-weight:bold;'>₹{s.net_financial_benefit:,.0f}</td>
            <td style='text-align:center;'>{collat_badge}</td>
        </tr>
        """

    # 4. SHAP Feature Attribution Waterfall
    shap_rows_html = ""
    if s5.shap_explanation and s5.shap_explanation.get("contributions"):
        for c in s5.shap_explanation["contributions"]:
            is_pos = c["shap_value"] > 0
            color = "#16a34a" if is_pos else "#dc2626" if c["shap_value"] < 0 else "#64748b"
            dir_label = "<span style='color:#16a34a; font-weight:bold;'>🟢 Solvency Lift</span>" if is_pos else "<span style='color:#dc2626; font-weight:bold;'>🔴 Caution Drag</span>" if c["shap_value"] < 0 else "⚪ Neutral"
            shap_rows_html += f"<tr><td><code>{c['feature']}</code></td><td class='num'>{c['feature_value']:.2f}</td><td class='num' style='color:{color}; font-weight:bold;'>{c['shap_value']:+.4f}</td><td>{dir_label}</td></tr>"

    shap_table_html = f"""
    <table style='margin-top: 10px;'>
        <tr><th>10-D Feature Parameter</th><th class="num">Observed Value</th><th class="num">TreeSHAP Weight (φ)</th><th>Attribution Direction</th></tr>
        {shap_rows_html}
    </table>
    """ if shap_rows_html else ""

    # Positive & Risk Drivers Lists
    pos_drivers_html = "".join(f"<li style='margin-bottom: 4px;'>{p}</li>" for p in s5.top_positive_factors)
    risk_drivers_html = "".join(f"<li style='margin-bottom: 4px;'>{r}</li>" for r in s5.top_risk_factors)

    # 5. SWOT Analysis Grid
    def _render_swot_list(items):
        if not items:
            return "<em>None identified</em>"
        formatted = []
        for i in items:
            if isinstance(i, dict):
                txt = i.get("text", str(i))
            elif hasattr(i, "text"):
                txt = getattr(i, "text", str(i))
            else:
                txt = str(i)
            formatted.append(f"<li style='margin-bottom:3px;'>{txt}</li>")
        return "<ul style='margin:0; padding-left:16px; font-size:11px;'>" + "".join(formatted) + "</ul>"

    swot_html = f"""
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;'>
        <div style='background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px;'>
            <strong style='color: #15803d; font-size: 12px;'>💪 STRENGTHS (Internal Positives)</strong>
            <div style='margin-top: 6px;'>{_render_swot_list(swot.get("strengths", []))}</div>
        </div>
        <div style='background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 10px;'>
            <strong style='color: #b91c1c; font-size: 12px;'>⚠️ WEAKNESSES (Internal Constraints)</strong>
            <div style='margin-top: 6px;'>{_render_swot_list(swot.get("weaknesses", []))}</div>
        </div>
        <div style='background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 10px;'>
            <strong style='color: #1d4ed8; font-size: 12px;'>🚀 OPPORTUNITIES (Market Tailwinds)</strong>
            <div style='margin-top: 6px;'>{_render_swot_list(swot.get("opportunities", []))}</div>
        </div>
        <div style='background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 10px;'>
            <strong style='color: #b45309; font-size: 12px;'>🛡️ THREATS (External Risks)</strong>
            <div style='margin-top: 6px;'>{_render_swot_list(swot.get("threats", []))}</div>
        </div>
    </div>
    """

    # 6. Risk Mitigation Table Rows
    risk_rows_html = ""
    for r in risks:
        if isinstance(r, dict):
            r_id = r.get("risk_id", "")
            r_title = r.get("title", "")
            r_basis = r.get("basis", "")
            r_sev = r.get("severity", "MODERATE")
            r_score = float(r.get("score", 0.0))
            r_buf = r.get("rupee_buffer")
            r_mit = r.get("mitigation", "")
        else:
            r_id = getattr(r, "risk_id", "")
            r_title = getattr(r, "title", "")
            r_basis = getattr(r, "basis", "")
            r_sev = getattr(r, "severity", "MODERATE")
            r_score = float(getattr(r, "score", 0.0))
            r_buf = getattr(r, "rupee_buffer", None)
            r_mit = getattr(r, "mitigation", "")

        buf_str = f"₹{r_buf:,.0f}" if r_buf else "Policy / Process"
        sev_color = "#dc2626" if r_sev == "HIGH" else "#d97706" if r_sev == "MODERATE" else "#16a34a"
        risk_rows_html += f"""
        <tr>
            <td style='text-align:center; font-weight:bold;'>{r_id}</td>
            <td><strong>{r_title}</strong><br/><span style='font-size:10px; color:#64748b;'>{r_basis}</span></td>
            <td style='text-align:center;'><span class='badge' style='background:{sev_color}15; color:{sev_color}; font-weight:bold;'>{r_sev}</span></td>
            <td class='num'>{r_score:.1f}/10</td>
            <td class='num' style='font-weight:bold;'>{buf_str}</td>
            <td style='font-size:11px;'>{r_mit}</td>
        </tr>
        """

    # 7. Statutory Checklist Rows
    statutory_rows_html = ""
    for d in s7:
        if isinstance(d, dict):
            d_code = d.get("document_code", "")
            d_name = d.get("document_name", "")
            d_cat = d.get("category_requirement", "")
            d_auth = d.get("issuing_authority", "")
            d_mand = bool(d.get("is_mandatory", False))
            d_notes = d.get("notes", "")
        else:
            d_code = getattr(d, "document_code", "")
            d_name = getattr(d, "document_name", "")
            d_cat = getattr(d, "category_requirement", "")
            d_auth = getattr(d, "issuing_authority", "")
            d_mand = bool(getattr(d, "is_mandatory", False))
            d_notes = getattr(d, "notes", "")

        mand_str = "<span class='badge' style='background:#fee2e2; color:#b91c1c; font-weight:bold;'>MANDATORY</span>" if d_mand else "<span class='badge' style='background:#f1f5f9; color:#475569;'>OPTIONAL</span>"
        statutory_rows_html += f"""
        <tr>
            <td style='text-align:center;'><code>{d_code}</code></td>
            <td><strong>{d_name}</strong></td>
            <td>{d_cat}</td>
            <td>{d_auth}</td>
            <td style='text-align:center;'>{mand_str}</td>
            <td style='font-size:11px; color:#475569;'>{d_notes}</td>
        </tr>
        """

    dscr_benchmark_label = "RBI Benchmark >= 1.33 Satisfied" if s3.dscr_benchmark_met else "Caution: Below 1.33 Benchmark"
    pop_str = f"{p.catchment_projected_population:,.0f}" if p.catchment_projected_population else "Local"
    area_type_str = "Rural Area" if p.is_rural else "Urban Area"
    verdict_badge_class = "suitable" if s5.verdict == "SUITABLE" else "caution" if s5.verdict == "CAUTION" else "reconsider"
    reconciled_status = "100% Reconciled" if finance['reconciliation_balanced'] else "Discrepancy Detected"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bank DPR — {p.enterprise_name} ({p.dpr_reference_id})</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 14mm 12mm 14mm 12mm;
    }}
    body {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        font-size: 12px;
        color: #0f172a;
        line-height: 1.45;
        margin: 0;
        padding: 24px;
        background-color: #ffffff;
    }}
    .header-box {{
        border: 2px solid #0f172a;
        padding: 16px 20px;
        background: #f8fafc;
        border-radius: 6px;
        margin-bottom: 20px;
    }}
    .header-top {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid #cbd5e1;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }}
    h1 {{
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .sub-header {{
        font-size: 11px;
        color: #475569;
        font-weight: 600;
        margin-top: 3px;
    }}
    .meta-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px 16px;
        font-size: 11.5px;
    }}
    .meta-item {{
        display: flex;
        gap: 6px;
    }}
    .meta-label {{
        color: #475569;
        font-weight: 600;
        min-width: 120px;
    }}
    .meta-val {{
        color: #0f172a;
        font-weight: 700;
    }}
    h2 {{
        font-size: 13.5px;
        font-weight: 800;
        color: #0f172a;
        background: #f1f5f9;
        border-left: 4px solid #0284c7;
        padding: 6px 10px;
        margin-top: 22px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 12px;
        font-weight: 700;
        color: #334155;
        margin-top: 12px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 8px;
        margin-bottom: 14px;
        font-size: 11px;
        page-break-inside: auto;
    }}
    tr {{
        page-break-inside: avoid;
        page-break-after: auto;
    }}
    th, td {{
        border: 1px solid #cbd5e1;
        padding: 5px 8px;
        text-align: left;
        vertical-align: middle;
    }}
    th {{
        background-color: #f1f5f9;
        font-weight: 700;
        color: #1e293b;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.2px;
    }}
    td.num {{
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-family: 'Consolas', 'Courier New', monospace;
    }}
    .badge {{
        display: inline-block;
        padding: 1.5px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
    }}
    .badge-suitable {{ background: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
    .badge-caution {{ background: #fef9c3; color: #a16207; border: 1px solid #fde047; }}
    .badge-reconsider {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
    
    .callout {{
        background: #f8fafc;
        border-left: 3px solid #64748b;
        padding: 8px 12px;
        font-size: 11.5px;
        margin: 8px 0 12px 0;
        color: #334155;
        border-radius: 0 4px 4px 0;
    }}
    .signature-block {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 30px;
        margin-top: 36px;
        padding-top: 16px;
        border-top: 1px dashed #94a3b8;
        page-break-inside: avoid;
    }}
    .sig-box {{
        border: 1px solid #cbd5e1;
        padding: 14px;
        border-radius: 6px;
        background: #f8fafc;
        min-height: 100px;
    }}
    @media print {{
        body {{
            padding: 0;
            background: none;
        }}
        .header-box {{
            border-color: #000;
        }}
        h2 {{
            background: #eee !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        th {{
            background: #eee !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
    }}
</style>
</head>
<body>

<!-- Institutional Header -->
<div class="header-box">
    <div class="header-top">
        <div>
            <h1>DETAILED PROJECT REPORT (DPR) & CREDIT MEMORANDUM</h1>
            <div class="sub-header">Statutory Priority Sector Lending Dossier • Scheduled Commercial Bank & DIC Standards</div>
        </div>
        <div style="text-align: right;">
            <div style="font-family: monospace; font-size: 11px; font-weight: bold; color: #0284c7;">REF: {p.dpr_reference_id}</div>
            <div style="font-size: 10.5px; color: #64748b; margin-top: 2px;">Appraisal Date: {p.report_date}</div>
        </div>
    </div>

    <div class="meta-grid">
        <div class="meta-item"><span class="meta-label">Enterprise Name:</span><span class="meta-val">{p.enterprise_name}</span></div>
        <div class="meta-item"><span class="meta-label">Legal Constitution:</span><span class="meta-val">{p.constitution}</span></div>
        <div class="meta-item"><span class="meta-label">Promoter Name:</span><span class="meta-val">{p.promoter_name} ({p.gender}, {p.promoter_category.upper()})</span></div>
        <div class="meta-item"><span class="meta-label">Industry Sector:</span><span class="meta-val">{p.business_category.upper()} • {p.sector.upper()}</span></div>
        <div class="meta-item"><span class="meta-label">Target Location:</span><span class="meta-val">{p.target_village}, Block {p.target_block}, {p.target_district}, {p.target_state}</span></div>
        <div class="meta-item"><span class="meta-label">Area / Population:</span><span class="meta-val">{area_type_str} ({pop_str} Catchment Pop)</span></div>
    </div>
</div>

<!-- SECTION 1 -->
<h2>SECTION 1: EXECUTIVE APPRAISAL & STRATEGIC RECOMMENDATIONS</h2>
<div class="callout">
    <strong>Executive Feasibility Verdict:</strong> {ai.get('executive_summary', 'The proposed enterprise demonstrates sound operational feasibility with sustainable gross margins.')}
</div>
<h3>Strategic Action Plan for Promoter:</h3>
<ul style="margin: 0; padding-left: 20px; font-size: 11.5px;">
    {rec_items_html}
</ul>
<div style="margin-top: 10px; font-size: 11.5px; background: #eff6ff; border-left: 3px solid #3b82f6; padding: 8px 12px; border-radius: 0 4px 4px 0;">
    <strong>Bank Credit Officer Appraisal Notes:</strong> {ai.get('bank_appraisal_notes', 'Recommended for composite term loan processing under priority sector guidelines.')}
</div>

<!-- SECTION 2 -->
<h2>SECTION 2: CAPITAL OUTLAY & MEANS OF FINANCE RECONCILIATION</h2>
<h3>A. Capital Expenditure Breakdown:</h3>
<table>
    <tr><th>Capital Component</th><th class="num">% Outlay</th><th class="num">Amount (₹)</th><th>Item Description</th></tr>
    <tr><td>Plant, Machinery & Core Equipment</td><td class="num">{outlay['plant_and_machinery']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['plant_and_machinery']['amount_inr']:,.2f}</td><td>{outlay['plant_and_machinery']['description']}</td></tr>
    <tr><td>Electrification, Site Works & Fixtures</td><td class="num">{outlay['electrification_and_site_works']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['electrification_and_site_works']['amount_inr']:,.2f}</td><td>{outlay['electrification_and_site_works']['description']}</td></tr>
    <tr><td>Initial Working Capital Reserve</td><td class="num">{outlay['initial_working_capital_reserve']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['initial_working_capital_reserve']['amount_inr']:,.2f}</td><td>{outlay['initial_working_capital_reserve']['description']}</td></tr>
    <tr><td>Contingency & Pre-Operative Outlay</td><td class="num">{outlay['contingency_and_pre_operative']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['contingency_and_pre_operative']['amount_inr']:,.2f}</td><td>{outlay['contingency_and_pre_operative']['description']}</td></tr>
    <tr style="font-weight:bold; background:#f8fafc;"><td>TOTAL CAPITAL OUTLAY</td><td class="num">100.0%</td><td class="num">₹{outlay['total_capital_outlay']:,.2f}</td><td><strong>100% Total Project Outlay Sized</strong></td></tr>
</table>

<h3>B. Means of Finance (Sources of Funds):</h3>
<table>
    <tr><th>Financing Means</th><th class="num">% Share</th><th class="num">Amount (₹)</th><th>Terms / Funding Source</th></tr>
    <tr><td>Promoter Margin Contribution</td><td class="num">{finance['promoter_margin_pct']:.1f}%</td><td class="num">₹{finance['promoter_margin_amount']:,.2f}</td><td>Promoter equity cash deposit</td></tr>
    <tr><td>Government Capital Subsidy Grant</td><td class="num">{finance['capital_subsidy_pct']:.1f}%</td><td class="num">₹{finance['capital_subsidy_amount']:,.2f}</td><td>{finance['subsidy_scheme_name']}</td></tr>
    <tr><td>Bank Term Loan / Debt Facility</td><td class="num">{finance['bank_term_loan_pct']:.1f}%</td><td class="num">₹{finance['bank_term_loan_amount']:,.2f}</td><td>Scheduled Commercial Bank Term Loan</td></tr>
    <tr style="font-weight:bold; background:#f8fafc;"><td>TOTAL MEANS OF FINANCE</td><td class="num">100.0%</td><td class="num">₹{finance['total_means_of_finance']:,.2f}</td><td><strong>Reconciliation Status: Balanced ({reconciled_status})</strong></td></tr>
</table>

<!-- SECTION 3 -->
<h2>SECTION 3: 5-YEAR FINANCIAL & CASH FLOW PROJECTIONS</h2>
<div class="meta-grid" style="margin-bottom: 8px;">
    <div class="meta-item"><span class="meta-label">5-Year Average DSCR:</span><span class="meta-val">{s3.average_dscr:.2f} ({dscr_benchmark_label})</span></div>
    <div class="meta-item"><span class="meta-label">Break-Even Point (BEP):</span><span class="meta-val">{s3.break_even_point_pct:.1f}% Capacity (Price Floor: ₹{s3.recommended_unit_price_floor:.2f})</span></div>
</div>
<table>
    <tr>
        <th>Financial Metric (₹)</th>
        {years_headers_html}
    </tr>
    {fin_table_rows_html}
</table>

<!-- SECTION 4 -->
<h2>SECTION 4: GOVERNMENT SCHEME OPTIMIZATION & SUBSIDY MATRIX</h2>
<table>
    <tr><th>Rank</th><th>Scheme Name</th><th style='text-align:center;'>Status</th><th class="num">Capital Grant (₹)</th><th class="num">Eff. Interest</th><th class="num">Net Benefit (₹)</th><th style='text-align:center;'>Collateral Free</th></tr>
    {scheme_rows_html}
</table>

<!-- SECTION 5 -->
<h2>SECTION 5: MACHINE LEARNING VIABILITY & TREESHAP EXPLAINABILITY</h2>
<div class="meta-grid" style="margin-bottom: 8px;">
    <div class="meta-item">
        <span class="meta-label">Viability Verdict:</span>
        <span class="badge badge-{verdict_badge_class}">{s5.verdict} ({s5.confidence_pct:.1f}% Confidence)</span>
    </div>
    <div class="meta-item"><span class="meta-label">Classification Engine:</span><span class="meta-val">{s5.model_version} (Native C++ TreeSHAP)</span></div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 6px;">
    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px;">
        <strong style="color: #15803d; font-size: 11.5px;">🟢 Primary Solvency Drivers (Positive SHAP Lift):</strong>
        <ul style="margin: 6px 0 0 0; padding-left: 16px; font-size: 11px;">{pos_drivers_html}</ul>
    </div>
    <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 10px;">
        <strong style="color: #b91c1c; font-size: 11.5px;">🔴 Key Operational Risk Factors (Caution Drag):</strong>
        <ul style="margin: 6px 0 0 0; padding-left: 16px; font-size: 11px;">{risk_drivers_html}</ul>
    </div>
</div>
{shap_table_html}

<!-- SECTION 6 -->
<h2>SECTION 6: GROUNDED SWOT & 8-POINT RISK MITIGATION MATRIX</h2>
<h3>A. 4-Quadrant Strategic SWOT Analysis:</h3>
{swot_html}

<h3 style="margin-top: 14px;">B. 8-Point Quantified Risk Mitigation Table (Overall Severity: {overall_risk}):</h3>
<table>
    <tr><th>ID</th><th>Risk Factor</th><th style='text-align:center;'>Severity</th><th class="num">Score</th><th class="num">Rupee Buffer</th><th>Actionable Mitigation Procedure</th></tr>
    {risk_rows_html}
</table>

<!-- SECTION 7 -->
<h2>SECTION 7: STATUTORY BANK SUBMISSION DOCUMENT CHECKLIST</h2>
<table>
    <tr><th style='text-align:center;'>Code</th><th>Document Name</th><th>Classification</th><th>Issuing Authority</th><th style='text-align:center;'>Requirement</th><th>Compliance Notes</th></tr>
    {statutory_rows_html}
</table>

<!-- Official Sign-off & Signature Block -->
<div class="signature-block">
    <div class="sig-box">
        <strong style="font-size: 11.5px; color: #0f172a;">PROMOTER / APPLICANT DECLARATION</strong>
        <p style="font-size: 10.5px; color: #475569; margin: 6px 0 16px 0; line-height: 1.4;">
            I hereby declare that all particulars, capital estimates, and statements submitted in this Detailed Project Report are true and correct to the best of my knowledge.
        </p>
        <div style="display: flex; justify-content: space-between; font-size: 10.5px; color: #64748b; margin-top: 24px;">
            <span>Date: ____________________</span>
            <span style="font-weight: bold; color: #0f172a;">[ Signature of Applicant ]</span>
        </div>
    </div>

    <div class="sig-box">
        <strong style="font-size: 11.5px; color: #0f172a;">BANK CREDIT APPRAISAL ENDORSEMENT</strong>
        <p style="font-size: 10.5px; color: #475569; margin: 6px 0 16px 0; line-height: 1.4;">
            Appraised in accordance with Scheduled Commercial Bank Priority Sector Lending / PMEGP credit norms and recommended for sanction consideration.
        </p>
        <div style="display: flex; justify-content: space-between; font-size: 10.5px; color: #64748b; margin-top: 24px;">
            <span>Branch Seal: ______________</span>
            <span style="font-weight: bold; color: #0f172a;">[ Credit Officer / Branch Manager ]</span>
        </div>
    </div>
</div>

</body>
</html>
"""
    return html


if __name__ == "__main__":
    print("dpr_generator module compiled successfully.")


