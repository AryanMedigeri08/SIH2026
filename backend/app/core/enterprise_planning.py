"""Bounded planning trials delegated to the unchanged final feasibility pipeline.

The existing opportunity catalogue supplies *cost references and ideas only*.
Its independent DSCR/loan approximations are deliberately never called here.
"""
from __future__ import annotations

import asyncio
import copy
import json
import logging
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
        # This is the existing machinery/outlay allocation, not a new financing rule.
        return [("Your equipment quote", round((quote / .55) / 1000) * 1000, "user_equipment_quote")]
    low, high = item["typical_project_cost_range"]
    return [(label, cost, REFERENCE_VERSION) for label, cost in (
        ("Starter estimate", low), ("Standard estimate", round((low + high) / 2000) * 1000), ("Larger estimate", high))]


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
    warnings = [REFERENCE_NOTE] if source == REFERENCE_VERSION else ["User equipment quote; other setup and working-capital costs remain estimates."]
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
            items = [{"sector_id": "custom", "enterprise_name": request.idea_description[:100],
                      "description": request.idea_description, "sector": request.custom_sector, "business_category": request.custom_category}]
        elif request.business_id in CATALOGUE:
            items = [CATALOGUE[request.business_id]]
        else:
            raise HTTPException(422, "Choose a supported business or provide another business with a setup quote.")
    else:
        # Shortlist six distinct businesses. This is explicitly not an exhaustive market search.
        # Cost bands are independent of own cash; no shrinking an expensive business to fit cash.
        def priority(item):
            odop = match_odop(request.state_name, request.district_name, item["sector"], item["enterprise_name"])
            local = request.state_name.casefold() in {s.casefold() for s in item["state_affinities"]}
            # Include lower-cost starters before regional affinities. A costly
            # ODOP sector must not hide all affordable catalogue starters.
            return (item["typical_project_cost_range"][0], -bool(odop.get("is_aligned")), -local)
        items = sorted(CATALOGUE.values(), key=priority)[:6]

    proposals, failed = [], 0
    # Sequential bounded evaluations avoid multiplying paid-provider traffic.
    for item in items:
        regional = await evaluate_region(request, item)
        options = configurations(item, request.machinery_quote if request.path == "idea_only" else None)
        if request.path == "budget_only":
            options = options[:1]
        for label, cost, source in options:
            if cost <= 0:
                raise HTTPException(422, "Equipment quote is too small to form a project estimate.")
            try:
                report = await evaluate_finances(trial_input(request, item, cost))
                proposals.append(describe_trial(request, item, label, source, report, regional))
            except Exception:
                failed += 1
                logger.warning("Planning trial failed for %s", item["sector_id"], exc_info=True)
    if not proposals:
        raise HTTPException(503, "Could not evaluate plans. Your inputs have not been saved as a business. Please retry.")
    if request.path == "budget_only":
        proposals.sort(key=lambda p: (p["affordable"] is not True, p["status"] != "estimated_fit",
            -p["regional"]["composite_score"], p["required_own_money"]))
        proposals = proposals[:3]
    return {"proposals": proposals, "evaluated_businesses": len(items), "failed_trials": failed,
            "reference_version": REFERENCE_VERSION,
            "search_note": "Compared six lower-cost catalogue starters, ranked by funding fit and regional evidence; not an exhaustive market survey." if request.path == "budget_only" else "Compared fixed cost references; supplier prices and capacity need confirmation."}


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
