"""Bounded planning trials delegated to the unchanged final feasibility pipeline.

The existing opportunity catalogue supplies *cost references and ideas only*.
Its independent DSCR/loan approximations are deliberately never called here.
"""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from app.core.intelligence.models import BusinessIntent
from app.core.odop_matcher import match_odop
from app.core.opportunity_matcher import SECTOR_CATALOG
from app.models.planning import PlanningRequest
from app.models.schemas import UserInput, compute_business_status

logger = logging.getLogger(__name__)
REFERENCES = json.loads((Path(__file__).resolve().parents[1] / "data/planning_cost_references.v1.json").read_text(encoding="utf-8"))
REFERENCE_VERSION = REFERENCES["version"]
REFERENCE_NOTE = "Catalogue planning estimate, not a supplier quote. Confirm equipment, capacity, local demand and prices before borrowing."
CATALOGUE = {item["sector_id"]: {**item, "typical_project_cost_range": REFERENCES["project_cost_ranges"][item["sector_id"]]}
             for item in SECTOR_CATALOG}
CATEGORIES = {
    "dairy": "DAIRY", "textile": "TAILORING", "food_processing": "FOOD_PROCESSING",
    "spice_processing": "FOOD_PROCESSING", "agriculture_processing": "AGRICULTURE_SUPPORT",
    "aquaculture": "AGRICULTURE_SUPPORT", "service": "SERVICES", "repair": "SERVICES",
    "apparel": "TAILORING", "fabrication": "FABRICATION",
}


async def evaluate_finances(inputs: UserInput):
    # Direct delegation also runs the same scheme selection, machinery, SCA and DPR
    # logic as project creation. The outer persistence endpoint is never called.
    from app.routers.feasibility import _run_pipeline
    report, _dpr = await _run_pipeline(inputs.model_copy(deep=True))
    return report


async def evaluate_region(request: PlanningRequest, item: dict):
    from app.routers.market_intelligence import get_opportunity_engine
    category = CATEGORIES.get(item["sector"], "MANUFACTURING")
    intent = BusinessIntent(
        intent_id=item["sector_id"], display_name=item["enterprise_name"], primary_category=category,
        direct_categories=[category], search_keywords=item["enterprise_name"].upper().split(),
        description=item["description"],
    )
    try:
        report = await asyncio.wait_for(get_opportunity_engine().analyze_opportunity(
            state=request.state_name, district=request.district_name, village=request.village_name,
            business_intent=intent, radius_km=10, core_radius_km=5, max_records=300,
        ), timeout=45)
        data = report.to_dict()
        return {k: data[k] for k in ("recommendation", "composite_score", "confidence", "evidence", "supply_metrics", "demand_features", "data_lineage")}
    except Exception:
        logger.warning("Regional planning evidence unavailable", exc_info=True)
        return {"recommendation": "INSUFFICIENT_DATA", "composite_score": 0, "confidence": "INSUFFICIENT_DATA",
                "evidence": {"missing_evidence": ["Check local customers, competitors, raw materials and infrastructure in the village and within 5–10 km."]},
                "supply_metrics": {}, "demand_features": {}, "data_lineage": []}


def business_choices():
    return [{"id": item["sector_id"], "name": item["enterprise_name"], "description": item["description"]}
            for item in CATALOGUE.values()]


def configurations(item: dict, quote: float | None = None):
    if quote is not None:
        return [("Your equipment quote", round((quote / .55) / 1000) * 1000, "user_equipment_quote")]
    low, high = item.get("typical_project_cost_range", (250000.0, 1000000.0))
    return [(label, cost, REFERENCE_VERSION) for label, cost in (
        ("Starter estimate", low), ("Standard estimate", round((low + high) / 2000) * 1000), ("Larger estimate", high))]


def calculate_budget_tiers(own_cash: float, promoter_category: str, is_rural: bool = True) -> list[dict]:
    """Computes 3 project cost tiers designed to maximize utilization of the promoter's available cash.
    Under statutory PMEGP/credit guidelines:
      - Special Categories (SC/ST/OBC/Women/Artisan/SHG): 5% promoter equity.
      - General Category: 10% promoter equity."""
    is_special = promoter_category.lower() in ("sc", "st", "obc", "women", "artisan", "women_shg")
    margin_rate = 0.05 if is_special else 0.10

    # Maximum bankable outlay that absorbs ~100% of available cash
    max_outlay = round((own_cash / margin_rate) / 25000) * 25000
    # Clamped between Rs 1.0 Lakh and Rs 50.0 Lakh (PMEGP statutory manufacturing maximum)
    max_outlay = min(max(max_outlay, 100000.0), 5000000.0)

    # 3 Tiers targeting high cash absorption:
    tier_1_cost = max_outlay
    tier_2_cost = min(max(round((max_outlay * 0.80) / 25000) * 25000, 100000.0), max_outlay)
    if tier_2_cost == tier_1_cost and tier_1_cost > 100000:
        tier_2_cost = max(tier_1_cost - 25000, 100000.0)

    tier_3_cost = min(max(round((max_outlay * 0.60) / 25000) * 25000, 100000.0), tier_2_cost)
    if tier_3_cost == tier_2_cost and tier_2_cost > 100000:
        tier_3_cost = max(tier_2_cost - 25000, 100000.0)

    return [
        {"label": "Full Investment", "cost": tier_1_cost, "target_margin": round(tier_1_cost * margin_rate)},
        {"label": "Balanced Investment", "cost": tier_2_cost, "target_margin": round(tier_2_cost * margin_rate)},
        {"label": "Starter Investment", "cost": tier_3_cost, "target_margin": round(tier_3_cost * margin_rate)},
    ]


def _get_groq_client():
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_api_key:
        try:
            from app.config import settings
            groq_api_key = (settings.GROQ_API_KEY or "").strip()
        except Exception:
            try:
                from backend.app.config import settings
                groq_api_key = (settings.GROQ_API_KEY or "").strip()
            except Exception:
                pass
    if not groq_api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=groq_api_key, max_retries=1, timeout=12.0)
    except Exception:
        return None


async def generate_dynamic_business_ideas(request: PlanningRequest, tiers: list[dict]) -> list[dict]:
    """Generates 3 localized, ODOP-aligned, and cash-optimized enterprise opportunities.
    Uses Groq Cloud LLM for personalized generation with intelligent heuristic fallback."""
    odop_info = match_odop(request.state_name, request.district_name, "general", "")
    odop_prod = odop_info.get("odop_product") or ""
    has_odop = odop_info.get("has_odop_record", False)

    client = _get_groq_client()
    if client:
        try:
            system_prompt = (
                "You are a Senior Rural Industrialization & MSME Project Specialist for the Ministry of MSME, Government of India.\n"
                "Recommend exactly 3 distinct, highly viable, realistic rural/semi-urban micro or small business opportunities.\n"
                "The opportunities must be personalized to the entrepreneur's location, district ODOP cluster, skills, and target project costs.\n"
                "Return a valid JSON object matching this schema:\n"
                "{\n"
                '  "proposals": [\n'
                "    {\n"
                '      "tier_index": 0,\n'
                '      "enterprise_name": "<Specific business title, e.g. \'Bankura Chhana & Ghee Processing Unit\'>",\n'
                '      "sector": "<one of: dairy, food_processing, manufacturing, fabrication, service, repair, apparel>",\n'
                '      "business_category": "<manufacturing or service>",\n'
                '      "description": "<Concise 1-2 sentence rationale explaining why this business excels in this specific district, local raw materials, and customer base>"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Include exactly 3 proposals for tier_index 0 (Full Investment), 1 (Balanced Investment), and 2 (Starter Investment).\n"
                "Do NOT recommend generic placeholders. Ground them in local regional reality. Output strictly in JSON format."
            )
            user_content = (
                f"Applicant Location: Village: {request.village_name}, Block: {request.block_name}, District: {request.district_name}, State: {request.state_name} ({'Rural' if request.is_rural else 'Urban'})\n"
                f"District ODOP Focus: {odop_prod if has_odop else 'General Agrarian / Rural Industrial Cluster'}\n"
                f"Promoter Category: {request.promoter_category.upper()} | Gender: {request.gender}\n"
                f"Promoter Notes / Space / Skills: {request.idea_description or 'Local entrepreneur ready for micro-enterprise setup'}\n"
                f"Available Cash Budget: INR {request.own_cash:,.0f}\n"
                f"Tier 1 Target Project Cost: INR {tiers[0]['cost']:,.0f}\n"
                f"Tier 2 Target Project Cost: INR {tiers[1]['cost']:,.0f}\n"
                f"Tier 3 Target Project Cost: INR {tiers[2]['cost']:,.0f}\n"
                f"Respond with the 3 proposals in JSON."
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                temperature=0.2,
                max_tokens=2500,
                response_format={"type": "json_object"},
            )
            content = chat_completion.choices[0].message.content
            parsed = json.loads(content)
            raw_proposals = parsed.get("proposals", [])
            if len(raw_proposals) >= 3:
                results = []
                for idx, p in enumerate(raw_proposals[:3]):
                    tier_cfg = tiers[idx]
                    results.append({
                        "sector_id": f"dynamic_{idx+1}",
                        "enterprise_name": p.get("enterprise_name", f"{request.district_name} Enterprise Unit"),
                        "sector": p.get("sector", "manufacturing").lower(),
                        "business_category": p.get("business_category", "manufacturing").lower(),
                        "description": p.get("description", "Localized commercial enterprise calibrated to regional demand."),
                        "configuration_label": tier_cfg["label"],
                        "target_cost": tier_cfg["cost"],
                        "source": "dynamic_ai_recommendation",
                    })
                return results
        except Exception as e:
            logger.warning("Dynamic LLM planning idea generation failed (%s); switching to intelligent location fallback.", e)

    # Intelligent Location & ODOP Fallback
    fallback_sectors = []
    dist = request.district_name
    if has_odop and odop_prod:
        sec = "food_processing" if any(k in odop_prod.lower() for k in ("fruit", "chilli", "grain", "oil", "rice", "mango", "milk", "sweet", "spice")) else "manufacturing"
        fallback_sectors.append({
            "name": f"{dist} {odop_prod} Processing & Value Addition Hub",
            "sector": sec,
            "category": "manufacturing",
            "desc": f"Directly capitalizes on {dist}'s official ODOP focus on {odop_prod}, qualifying for priority cluster subsidies and GeM corridor sales.",
        })
    else:
        fallback_sectors.append({
            "name": f"{dist} Fresh Dairy Aggregation & Chilled Products Unit",
            "sector": "dairy",
            "category": "manufacturing",
            "desc": f"Captures daily cash-flow demand across {dist} and neighboring towns through hygienic milk chilling, paneer, and curd processing.",
        })

    fallback_sectors.append({
        "name": f"{dist} Agro-Equipment Fabrication & Metal Works",
        "sector": "fabrication",
        "category": "manufacturing",
        "desc": f"Supplies customized implements, gates, grilles, and repair support to agricultural holdings and rural infrastructure projects in {request.block_name}.",
    })
    fallback_sectors.append({
        "name": f"{dist} Bio-Organic Fertilizer & Agro-Input Processing",
        "sector": "manufacturing",
        "category": "manufacturing",
        "desc": f"Converts locally abundant agricultural and livestock residues into high-margin enriched organic manure for local cultivators.",
    })

    results = []
    for idx, (tier_cfg, sec_info) in enumerate(zip(tiers, fallback_sectors)):
        results.append({
            "sector_id": f"dynamic_{idx+1}",
            "enterprise_name": sec_info["name"],
            "sector": sec_info["sector"],
            "business_category": sec_info["category"],
            "description": sec_info["desc"],
            "configuration_label": tier_cfg["label"],
            "target_cost": tier_cfg["cost"],
            "source": "dynamic_odop_heuristic",
        })
    return results


def trial_input(request: PlanningRequest, item: dict, cost: float):
    # Explicitly match the current wizard's default loan terms, including the tier boundary.
    return UserInput(
        **request.model_dump(include={"state_name", "district_name", "block_name", "village_name", "promoter_name",
            "promoter_category", "gender", "is_rural", "premise_type", "monthly_rent"}),
        enterprise_name=item["enterprise_name"], sector=item["sector"], business_category=item["business_category"],
        project_cost=cost, available_margin_capital=request.own_cash,
        annual_turnover_estimate=None, tenure_years=3 if cost <= 140000 else 7,
        moratorium_months=3 if cost <= 140000 else 6,
        additional_business_details=request.idea_description or item["description"],
    )


def describe_trial(request, item, label, source, report, regional):
    cap = report.capital_structure or report.financial_analysis["capital_structure"]
    # Both existing views are preserved. A gender/category discrepancy must not
    # understate the cash needed for the final report's own margin requirement.
    required = max(cap["required_promoter_equity"], report.financial_analysis["promoter_margin_amount"])
    gap = None if request.own_cash is None else max(round(required - request.own_cash, 2), 0)
    appraisal = compute_business_status({"report": {
        "financial_analysis": report.financial_analysis, "ml_viability": report.ml_viability,
        "risk_assessment": report.risk_assessment,
    }})
    warnings = [REFERENCE_NOTE] if source == REFERENCE_VERSION else ["Dynamic sector estimate; plant, machinery & equipment schedule configured automatically."]
    warnings.append("Sales are engine estimates, not verified local orders. A positive DSCR does not prove local demand.")
    if cap["required_promoter_equity"] != report.financial_analysis["promoter_margin_amount"]:
        warnings.append("Existing scheme and capital-structure margin views differ for this profile. The higher contribution is shown for planning; confirm eligibility with the lender.")
    concerns = []
    if gap:
        concerns.append("Available own money is below the planned contribution. Increase it, resize the project, or review existing SCA options in the wizard.")
    if appraisal.code != "healthy":
        concerns.append(f"The existing appraisal needs attention: {appraisal.reason}")
    if regional["recommendation"] in {"SATURATED_MARKET", "CONSTRAINED_MARKET"}:
        concerns.append("Regional evidence flags competition or infrastructure constraints.")
    provisional = regional["confidence"] not in {"HIGH", "MEDIUM"} or regional["recommendation"] == "INSUFFICIENT_DATA"
    if provisional:
        concerns.append("Local evidence is incomplete. Confirm customers, competition, supply and utilities before proceeding.")
    return {
        "proposal_id": uuid.uuid4().hex, "business_id": item["sector_id"], "name": item["enterprise_name"],
        "description": item["description"], "configuration": label, "cost_source": source,
        "project_cost": report.input_parameters.project_cost, "required_own_money": required,
        "available_own_money": request.own_cash, "equity_gap": gap,
        "affordable": gap == 0 if gap is not None else None,
        "status": "review_needed" if concerns else "estimated_fit", "appraisal_status": appraisal.model_dump(),
        "financial_analysis": report.financial_analysis, "scheme_optimization": report.scheme_optimization,
        "odop_alignment": report.odop_alignment, "regional": regional,
        "warnings": warnings, "concerns": concerns,
        "input_parameters": report.input_parameters.model_dump(mode="json"),
    }


async def build_plans(request: PlanningRequest):
    if request.path == "idea_only":
        if request.business_id == "custom":
            is_special = request.promoter_category.lower() in ("sc", "st", "obc", "women", "artisan", "women_shg") or request.is_rural
            m = 0.05 if is_special else 0.10
            if request.own_cash and request.own_cash > 0:
                tiers = calculate_budget_tiers(request.own_cash, request.promoter_category, request.is_rural)
                tier_costs = [t["cost"] for t in tiers]
            else:
                tier_costs = [250000.0, 500000.0, 1000000.0]

            custom_item = {
                "sector_id": "custom",
                "enterprise_name": request.idea_description[:60].strip() or "Custom Enterprise Project",
                "description": request.idea_description,
                "sector": request.custom_sector,
                "business_category": request.custom_category,
            }
            regional = await evaluate_region(request, custom_item)
            options = [
                ("Starter estimate", tier_costs[2] if len(tier_costs) > 2 else tier_costs[0], "dynamic_custom_estimate"),
                ("Standard estimate", tier_costs[1] if len(tier_costs) > 1 else tier_costs[0], "dynamic_custom_estimate"),
                ("Larger estimate", tier_costs[0], "dynamic_custom_estimate"),
            ]
            options.sort(key=lambda x: x[1])
            proposals, failed = [], 0
            for label, cost, source in options:
                try:
                    report = await evaluate_finances(trial_input(request, custom_item, cost))
                    proposals.append(describe_trial(request, custom_item, label, source, report, regional))
                except Exception:
                    failed += 1
                    logger.warning("Planning trial failed for custom %s", label, exc_info=True)
            if not proposals:
                raise HTTPException(503, "Could not evaluate plans for your custom idea. Please retry.")
            return {
                "proposals": proposals,
                "evaluated_businesses": 1,
                "failed_trials": failed,
                "reference_version": REFERENCE_VERSION,
                "search_note": f"Evaluated 3 project sizes for '{custom_item['enterprise_name']}' with auto-configured plant & machinery.",
            }
        elif request.business_id in CATALOGUE:
            item = CATALOGUE[request.business_id]
            regional = await evaluate_region(request, item)
            options = configurations(item)
            proposals, failed = [], 0
            for label, cost, source in options:
                try:
                    report = await evaluate_finances(trial_input(request, item, cost))
                    proposals.append(describe_trial(request, item, label, source, report, regional))
                except Exception:
                    failed += 1
                    logger.warning("Planning trial failed for %s", item["sector_id"], exc_info=True)
            if not proposals:
                raise HTTPException(503, "Could not evaluate plans. Please retry.")
            return {
                "proposals": proposals,
                "evaluated_businesses": 1,
                "failed_trials": failed,
                "reference_version": REFERENCE_VERSION,
                "search_note": f"Compared 3 project sizes for '{item['enterprise_name']}' from regional cost benchmarks.",
            }
        else:
            raise HTTPException(422, "Choose a supported business or describe your custom idea.")
    else:  # path == "budget_only"
        tiers = calculate_budget_tiers(request.own_cash, request.promoter_category, request.is_rural)
        dynamic_ideas = await generate_dynamic_business_ideas(request, tiers)

        proposals, failed = [], 0
        for idea in dynamic_ideas:
            regional = await evaluate_region(request, idea)
            try:
                report = await evaluate_finances(trial_input(request, idea, idea["target_cost"]))
                proposals.append(describe_trial(request, idea, idea["configuration_label"], idea["source"], report, regional))
            except Exception:
                failed += 1
                logger.warning("Planning trial failed for dynamic idea %s", idea["enterprise_name"], exc_info=True)

        if not proposals:
            raise HTTPException(503, "Could not evaluate plans. Your inputs have not been saved. Please retry.")

        # Sort so that proposals with highest affordability & cash utilization come first
        proposals.sort(key=lambda p: (
            p["affordable"] is not True,
            p["status"] != "estimated_fit",
            -p["project_cost"],
            -p["regional"]["composite_score"]
        ))

        return {
            "proposals": proposals,
            "evaluated_businesses": len(dynamic_ideas),
            "failed_trials": failed,
            "reference_version": REFERENCE_VERSION,
            "search_note": f"Generated personalized business opportunities tailored to {request.district_name}, {request.state_name} maximizing your ₹{request.own_cash:,.0f} investment.",
        }


@dataclass
class Draft:
    owner: str
    expires: float
    request: PlanningRequest
    result: dict


class PlanningSessions:
    """Per-worker request limits and bounded fallback previews for isolated tests."""
    def __init__(self):
        self.drafts = OrderedDict()
        self.busy = set()
        self.last_started = OrderedDict()

    def start(self, owner):
        now = time.monotonic()
        if owner in self.busy or now - self.last_started.get(owner, -100) < 10 or len(self.busy) >= 4:
            raise HTTPException(429, "A planning request is running or was just submitted. Please wait before trying again.")
        self.last_started[owner] = now
        if len(self.last_started) > 1000:
            self.last_started.popitem(last=False)
        self.busy.add(owner)

    def save(self, owner, request, result):
        # Re-evaluation invalidates all earlier proposals for this owner.
        now = time.time()
        for key in list(self.drafts):
            if self.drafts[key].owner == owner or self.drafts[key].expires < now:
                del self.drafts[key]
        while len(self.drafts) >= 100:
            self.drafts.popitem(last=False)
        draft_id = uuid.uuid4().hex
        self.drafts[draft_id] = Draft(owner, now + 1800, request.model_copy(deep=True), copy.deepcopy(result))
        return draft_id

    def accept(self, owner, draft_id, acceptance, draft=None):
        draft = draft if draft is not None else self.drafts.get(draft_id)
        if not draft or draft.owner != owner:
            raise HTTPException(404, "Planning preview not found. Evaluate again.")
        if draft.expires < time.time():
            self.drafts.pop(draft_id, None)
            raise HTTPException(410, "This preview expired. Evaluate again with your latest details.")
        proposal = next((p for p in draft.result["proposals"] if p["proposal_id"] == acceptance.proposal_id), None)
        if not proposal:
            raise HTTPException(404, "Proposal not found in this preview.")
        if not acceptance.acknowledge_estimates or (proposal["concerns"] and not acceptance.accept_risks):
            raise HTTPException(409, "Confirm the estimates and any listed concerns before continuing.")
        inputs = copy.deepcopy(proposal["input_parameters"])
        # Unknown cash stays unknown until the user explicitly chooses this required
        # contribution. Explicit zero is retained rather than replaced with a default.
        cash = draft.request.own_cash
        inputs["available_margin_capital"] = proposal["required_own_money"] if cash is None else cash
        inputs["margin_capital"] = inputs["available_margin_capital"]
        return {"initial_data": inputs, "proposal_id": proposal["proposal_id"],
                "machinery_schedule": copy.deepcopy(proposal["financial_analysis"]["machinery_schedule"])}


sessions = PlanningSessions()
