"""Dependency-driven Mira session. Language extraction never controls deterministic decisions."""
from __future__ import annotations

import asyncio
import re
from copy import deepcopy

from app.models.onboarding import Facts
from app.core.intelligence.intents import INTENT_CATALOG
from app.core.udyam.activities.categories import map_nic_to_category, BUSINESS_CATEGORIES
from app.core.opportunity_matcher import SECTOR_CATALOG
from app.core.odop_matcher import find_district_odop
from app.core.financial_calculator import (
    calculate_asset_driven_capital_structure, rank_eligible_schemes, emi_with_moratorium,
    confirmed_project_outlay,
)

# Translates existing intelligence IDs into existing financial sector IDs; no new ontology.
FINANCIAL_SECTORS = {"dairy": "dairy", "kirana": "general", "tailoring": "apparel",
    "poultry": "poultry", "agro_processing": "food_processing", "fabrication": "fabrication",
    "mobile_repair": "repair", "beauty_salon": "service", "transport": "service", "construction": "general"}

# Each derived node declares its prerequisites. Corrections invalidate descendants only.
DEPENDENCIES = {
    "classification": {"idea", "activity", "products"},
    "business_confirmed": {"classification", "operations", "scale"},
    "regional": {"location", "classification"},
    "odop": {"location", "classification"},
    "recommendations": {"location", "budget", "budget_kind", "skills", "constraints", "odop_preference"},
    "premises_suitable": {"location", "classification", "operations", "scale", "premises", "space"},
    "estimate": {"classification", "operations", "scale", "premises", "space", "premises_suitable", "regional"},
    "assessment": {"location", "regional", "classification", "project_cost", "cost_basis", "personal_contribution",
                   "cost_items",
                   "premises", "rent_amount", "rent_period", "promoter_category", "gender", "budget", "budget_kind"},
    "financing_choice": {"assessment"},
}


def value(state, key, default=None):
    return state["fields"].get(key, {}).get("value", default)


def record(state, key, val, source="text", dependencies=()):
    state["fields"][key] = {"value": val, "source": source, "confirmed": True, "valid": True,
        "required": key not in ("odop_preference",), "dependencies": list(dependencies), "changed": True}


def invalidate(state, changed, *, clear_confirmed_inputs=True):
    if changed & {'location', 'idea', 'activity', 'products', 'scale', 'premises', 'rent_amount', 'rent_period', 'project_cost', 'cost_items', 'personal_contribution', 'monthly_sales', 'monthly_expenses', 'monthly_fixed_costs', 'variable_cost_pct'}:
        state.pop('financial_risk_accepted', None)
    if changed & {'idea', 'activity', 'products', 'scale'}:
        for key in ('monthly_sales', 'monthly_expenses', 'monthly_fixed_costs', 'variable_cost_pct', 'operating_basis'):
            if key not in changed:
                state['fields'].pop(key, None)
    if changed & {'location', 'idea', 'activity', 'products'}:
        state.pop('regional_risk_accepted', None)
    if changed & {'location', 'classification', 'idea', 'activity', 'products', 'scale', 'operations', 'premises'}:
        state['cost_proposal'] = None
        state.pop('rent_proposal', None)
    if "location" in changed:
        # Requirements and capital survive a move; suitability and rent belong to the site.
        for key in ("premises_suitable", "rent_amount", "rent_period"):
            state["fields"].pop(key, None)
        state["odop_explained"] = False
        state["odop_offered"] = False
        state['fields'].pop('odop_preference', None)
    affected = set(changed)
    progress = True
    while progress:
        progress = False
        for node, deps in DEPENDENCIES.items():
            if node not in affected and deps & affected:
                affected.add(node)
                progress = True
    for node in affected - set(changed):
        if node == "business_confirmed":
            state[node] = False
        elif node == "financing_choice":
            state["fields"].pop(node, None)
        elif node == "premises_suitable" and clear_confirmed_inputs:
            state["fields"].pop(node, None)
        elif node in state:
            state[node] = [] if node == "recommendations" else None
    if "odop" in affected:
        state["odop_offered"] = False
    if "estimate" in affected and clear_confirmed_inputs and "project_cost" not in changed:
        # A cost confirmed for a previous activity/scale/site cannot authorize the new one.
        for key in ("project_cost", "cost_basis", "cost_items"):
            state["fields"].pop(key, None)
        state["assessment"] = None
        state["fields"].pop("financing_choice", None)


def apply_updates(state, updates, source="text", correction=False):
    if "cost_items" in updates and "idea" not in updates and "scale" not in updates:
        updates = {**updates, "cost_items": {**(value(state, "cost_items") or {}), **updates["cost_items"]}}
    updates = Facts(**updates).model_dump(exclude_none=True)
    changed = {k for k, v in updates.items() if value(state, k) != v}
    conflicts = {k: updates[k] for k in changed if k in state["fields"]}
    # Switching business invalidates only business-specific answers, retaining capital and location.
    if "idea" in changed and value(state, "idea") and correction:
        for key in ("activity", "products", "operations", "scale", "enterprise_name", "odop_preference", "cost_basis", "project_cost", "cost_items"):
            if key not in updates:
                state["fields"].pop(key, None)
        state["business_confirmed"] = False
    if conflicts and not correction:
        state["pending_changes"].update(updates)
        # Preserve both old and proposed values. No calculation can proceed while unresolved.
        state["assessment"] = None
        return
    invalidate(state, changed, clear_confirmed_inputs=bool(conflicts))
    for key in changed | (set(updates) - set(state["fields"])):
        record(state, key, updates[key], source)
    if "idea" in changed:
        record(state, "idea_status", "known", source)
    if value(state, "budget_kind") == "personal" and value(state, "budget") is not None and "personal_contribution" not in updates:
        if "budget" in changed or "budget_kind" in changed:
            record(state, "personal_contribution", value(state, "budget"), source, ("budget", "budget_kind"))
    elif "budget_kind" in changed and "personal_contribution" not in updates:
        if state["fields"].get("personal_contribution", {}).get("dependencies"):
            state["fields"].pop("personal_contribution", None)
    if "premises" in changed:
        if value(state, "premises") not in ("rented", "shared"):
            state["fields"].pop("rent_amount", None)
            state["fields"].pop("rent_period", None)
        if "premises_suitable" not in updates:
            state["fields"].pop("premises_suitable", None)
    if "idea_status" in changed and value(state, "idea_status") == "explore":
        for key in ("idea", "activity", "products", "operations", "scale", "enterprise_name", "project_cost", "cost_basis"):
            state["fields"].pop(key, None)
        invalidate(state, {"idea"})
    if "cost_items" in changed:
        total = confirmed_project_outlay(value(state, "cost_items"))
        stated = value(state, "project_cost")
        if stated is not None and abs(stated - total) > 0.01:
            state["pending_changes"]["project_cost"] = total
            state["assessment"] = None
        else:
            record(state, "project_cost", total, "deterministic_cost_sum", ("cost_items",))


def question(field, text, choices=(), explanation="", action=None):
    return {"field": field, "text": text, "choices": list(choices), "explanation": explanation,
            "action": action or "answer"}


def classify(state):
    if not all(value(state, key) for key in ("idea", "activity", "products")):
        return None
    text = f"{value(state, 'idea')} {value(state, 'products')}".lower()
    exact_entry = next((entry for entry in SECTOR_CATALOG if entry["enterprise_name"].lower() == value(state, "idea").lower()), None)
    if exact_entry:
        category_id, confidence, mapping_source = map_nic_to_category("", text)
        if category_id == "UNKNOWN":
            category_id = "MANUFACTURING" if value(state, "activity") in ("manufacture", "process") else "SERVICES"
        return {"intent_id": category_id.lower(), "category_id": category_id, "sector": exact_entry["sector"],
                "business_category": "manufacturing" if value(state, "activity") in ("manufacture", "process") else "service",
                "business_type": value(state, "activity"), "label": exact_entry["enterprise_name"], "source": "existing_sector_catalog"}
    matches = []
    for intent in INTENT_CATALOG.values():
        score = sum(1 for kw in intent.search_keywords if re.search(r"\b" + re.escape(kw.lower()), text))
        if score:
            matches.append((score, intent))
    matches.sort(key=lambda pair: pair[0], reverse=True)
    if not matches:
        category_id, confidence, mapping_source = map_nic_to_category("", text)
        if category_id == "UNKNOWN":
            return None
        # Reuse known category and sector identifiers; broad mappings still require user confirmation.
        sector = next((FINANCIAL_SECTORS[i.intent_id] for i in INTENT_CATALOG.values() if i.primary_category == category_id), "general")
        return {"intent_id": category_id.lower(), "category_id": category_id, "sector": sector,
                "business_category": "manufacturing" if value(state, "activity") in ("manufacture", "process") else "service",
                "business_type": value(state, "activity"), "label": BUSINESS_CATEGORIES[category_id]["label"], "source": mapping_source}
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        return None
    intent = matches[0][1]
    activity = value(state, "activity")
    if activity == "other":
        return None
    return {"intent_id": intent.intent_id, "category_id": intent.primary_category,
            "sector": FINANCIAL_SECTORS[intent.intent_id],
            "business_category": "manufacturing" if activity in ("manufacture", "process") else "service",
            "business_type": activity, "label": intent.display_name, "source": "existing_intent_catalog"}


def catalogue_entries(state):
    category = state.get("classification") or {}
    sector = category.get("sector")
    entries = [e for e in SECTOR_CATALOG if e["sector"] == sector]
    # Match the actual product/activity before offering a broad sector estimate.
    words = set(re.findall(r"[a-z]{4,}", f"{value(state, 'idea', '')} {value(state, 'products', '')}".lower()))
    ranked = sorted(entries, key=lambda e: len(words & set(re.findall(r"[a-z]{4,}", (e["enterprise_name"] + ' ' + e['description']).lower()))), reverse=True)
    return ranked[:1]


async def regional_assessment(state):
    from app.core.intelligence.engine import MarketOpportunityEngine
    from app.core.intelligence.models import BusinessIntent
    loc = state["location"]
    c = state['classification']
    intent = c['intent_id']
    if state.get('experience') == 'adaptive' and intent not in INTENT_CATALOG:
        # An exact generic category must not be fuzzily resolved into an
        # unrelated named business (e.g. manufacturing -> tailoring).
        intent = BusinessIntent(intent_id=intent, display_name=c.get('label') or value(state, 'idea'),
            primary_category=c['category_id'], direct_categories=[c['category_id']], related_categories=[],
            search_keywords=[value(state, 'products', '')], description=value(state, 'idea', ''))
    result = await MarketOpportunityEngine().analyze_opportunity(
        state=loc["state_name"], district=loc["district_name"], village=loc["village_name"],
        target_lat=loc.get("latitude"), target_lon=loc.get("longitude"),
        business_intent=intent, max_records=200)
    data = result.to_dict()
    return {"evidence": data.get("evidence", {}), "recommendation": data.get("recommendation"), "confidence": data.get("confidence"),
            "market": {key: data.get(key) for key in ('target_location', 'supply_metrics', 'demand_features', 'opportunity_indicators', 'sensitivity_analysis', 'classified_competitors')},
            "data_lineage": data.get("data_lineage", []), "source": "existing_market_opportunity_engine",
            "location": deepcopy(loc), "intent_id": state["classification"]["intent_id"]}


def verified_odop(state):
    loc = state["location"]
    record_ = find_district_odop(loc["state_name"], loc["district_name"])
    if not record_:
        return None
    # Existing matcher is fuzzy: require exact district/state match before an authoritative offer.
    normalize = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    if normalize(record_.get("matched_district_name", "")) != normalize(loc["district_name"]) or normalize(record_.get("matched_state_name", "")) != normalize(loc["state_name"]):
        return None
    return {"product": record_.get("odop_product"), "matching_sectors": record_.get("matching_sectors", []),
            "source": "existing_odop_registry", "aligned": (state.get("classification") or {}).get("sector") in record_.get("matching_sectors", [])}


def recommendations(state, limit=3):
    loc = state["location"]
    budget = value(state, "budget")
    kind = value(state, "budget_kind")
    interests = (value(state, "skills", "") + " " + value(state, "constraints", "")).lower()
    items = []
    for entry in SECTOR_CATALOG:
        if entry["sector_id"] in state.get("rejected", []):
            continue
        affinities = entry.get("state_affinities", [])
        odop = state.get("odop") or {}
        is_odop = entry["sector"] in odop.get("matching_sectors", [])
        regional = loc["state_name"].lower() in [s.lower() for s in affinities]
        if not regional and not is_odop:
            continue
        low, high = entry["typical_project_cost_range"]
        cs = calculate_asset_driven_capital_structure(0, budget if kind == "personal" else 0,
                promoter_category=value(state, "promoter_category"), gender=value(state, "gender"),
                is_rural=loc["is_rural"], target_project_cost=low)
        if (kind == "total" and low > budget) or (kind == "personal" and cs.required_promoter_equity > budget):
            continue
        terms = set(re.findall(r"[a-z]{4,}", (entry["enterprise_name"] + " " + entry["description"]).lower()))
        fit = sum(word in interests for word in terms)
        if not fit and str(value(state, "skills", "")).strip().lower() != "open to learning":
            continue
        items.append({"id": entry["sector_id"], "idea": entry["enterprise_name"], "description": entry["description"].split(". ", 1)[0].rstrip(".") + ".",
            "why_region": f"{loc['state_name']} is listed in the existing sector catalogue's regional affinities." if regional else f"Matches the recorded district ODOP product: {odop.get('product')}.",
            "market_evidence": "Regional catalogue screening only; local demand and site suitability still need assessment.",
            "outlay_range": [low, high], "space": "Space and utility requirements must be checked for the chosen capacity and equipment layout.",
            "potential_financing": max(low - budget, 0) if kind in ("personal", "total") else None,
            "scheme": entry["relevant_scheme"], "scheme_note": "Candidate scheme; eligibility is evaluated by the existing engine, not guaranteed.",
            "odop_aligned": is_odop, "source": "existing_sector_catalog", "score": fit + int(is_odop)})
    return sorted(items, key=lambda e: e["score"], reverse=True)[:limit]


async def assess_recommendations(state, limit=3):
    """Screen catalogue candidates against the existing village intelligence engine."""
    async def assess(candidate):
        proposed = deepcopy(state)
        entry = next(e for e in SECTOR_CATALOG if e["sector_id"] == candidate["id"])
        record(proposed, "idea", entry["enterprise_name"], "existing_catalogue")
        record(proposed, "products", entry["description"], "existing_catalogue")
        record(proposed, "activity", "manufacture" if entry["business_category"] == "manufacturing" else "service", "existing_catalogue")
        proposed["classification"] = classify(proposed)
        try:
            regional = await asyncio.wait_for(regional_assessment(proposed), timeout=30)
            verdict = regional.get("recommendation")
            if verdict in ("NOT_RECOMMENDED", "RECONSIDER", "UNSUITABLE"):
                return None
            candidate["regional_assessment"] = regional
            evidence = regional.get("evidence", {})
            if evidence.get("plain_language_summary"):
                candidate["market_evidence"] += " " + evidence["plain_language_summary"]
            candidate["confidence"] = evidence.get("confidence") or regional.get("confidence") or "INSUFFICIENT_DATA"
        except Exception:
            candidate["confidence"] = "INSUFFICIENT_DATA"
            candidate["market_evidence"] += " Village evidence is unavailable; suitability has not been established."
        return candidate
    results = await asyncio.gather(*(assess(candidate) for candidate in recommendations(state, limit)))
    return [result for result in results if result is not None]


def financial_assessment(state):
    """All banking terms and calculations delegated to unmodified existing functions."""
    outlay = value(state, "project_cost")
    own = value(state, "personal_contribution")
    classification = state["classification"]
    tenure, moratorium = (3.0, 3) if outlay <= 140000 else (7.0 if state.get('experience') == 'adaptive' else 5.0, 6)
    ranked = rank_eligible_schemes(project_cost=outlay, business_category=classification["business_category"],
        sector=classification["sector"], promoter_category=value(state, "promoter_category"),
        is_rural=state["location"]["is_rural"], tenure_years=tenure, moratorium_months=moratorium)
    top = next((s for s in ranked if s.eligible), ranked[0])
    cs = calculate_asset_driven_capital_structure(machinery_cost=(value(state, "cost_items") or {}).get("equipment", 0), available_promoter_cash=own,
        promoter_category=value(state, "promoter_category"), gender=value(state, "gender"),
        is_rural=state["location"]["is_rural"], target_project_cost=outlay,
        bank_interest_rate_pct=top.effective_interest_rate_pct, tenure_years=tenure, moratorium_months=moratorium,
        confirmed_project_cost=outlay)
    # Normal borrowing gap, subsidy and statutory margin remain separate quantities.
    gap = round(max(outlay - own, 0), 2)
    normal = emi_with_moratorium(gap, top.effective_interest_rate_pct, tenure, moratorium) if gap else None
    rent = value(state, "rent_amount", 0) / (12 if value(state, "rent_period") == "annual" else 1) if value(state, "premises") in ("rented", "shared") else 0
    budget = value(state, "budget")
    kind = value(state, "budget_kind")
    budget_shortfall = max((gap if kind == "borrowing" else outlay) - budget, 0) if budget is not None and kind in ("total", "personal", "borrowing") else None
    return {"project_outlay": outlay, "personal_contribution": own, "capital_deficit": gap,
            "financing_choice": value(state, 'financing_choice'),
            "budget": value(state, "budget"), "budget_kind": value(state, "budget_kind"),
            "budget_shortfall": round(budget_shortfall, 2) if budget_shortfall is not None else None,
            "monthly_rent": round(rent, 2), "normal_loan": {"amount": gap, "monthly_emi": round(normal.monthly_emi, 2) if normal else 0,
                "rate_pct": top.effective_interest_rate_pct, "tenure_years": tenure, "moratorium_months": moratorium},
            "capital_structure": cs.to_dict(), "candidate_schemes": [s.to_dict() for s in ranked],
            "subsidy_candidate": top.subsidy_grant_amount, "is_estimate": True,
            "cost_items": value(state, "cost_items"),
            "notice": "Indicative assessment using confirmed cost inputs and existing banking rules. A scheme, subsidy or SCA amount is not an approval. The full report separately shows the existing scheme-based appraisal assumptions."}


def next_question(state):
    """Select an unsatisfied dependency; one utterance may satisfy any number of nodes."""
    v = lambda key: value(state, key)
    if state["paused"]:
        return question("paused", "Your progress is saved. Say ‘resume’ when you are ready.", action="resume")
    if state["pending_changes"]:
        changes = "; ".join(f"{k.replace('_', ' ')}: {value(state, k)} → {val}" if k not in ("name", "gender", "promoter_category") else f"updated {k.replace('_', ' ')}" for k, val in state["pending_changes"].items())
        return question("pending_changes", f"I heard a change: {changes}. Should I use the new information?", action="confirm_change")
    for key, text, choices in (
        ("name", "What is your full name?", ()),
        ("gender", "How would you describe your gender? You can choose not to say.", ("Male", "Female", "Other", "Unspecified")),
        ("promoter_category", "Which category should I use for scheme assessment? This helps check relevant eligibility and contribution rules.", ("general", "sc", "st", "obc", "minority", "ph", "artisan", "women", "women_shg")),
    ):
        if v(key) is None:
            return question(key, text, choices, "Your category is used only for relevant eligibility and financing assessment. You can correct it at any time.")
    if not state.get("location"):
        return question("location", "Let’s find where you want to establish your business. You can use your current location or choose another place.")
    loc = state["location"]
    if loc.get("is_rural") is None:
        return question("area_verification", "I found the place, but some area-classification data is unavailable. Retry the automatic data check or choose the correct village.", explanation="Official area status governs scheme calculations. Missing records are not replaced by a user-selected Rural/Urban answer.")
    if not state["location_confirmed"]:
        return question("location_confirmation", f"Your village is {loc['village_name']}, development block {loc['block_name']}, district {loc['district_name']}, {loc['state_name']}. The area status is {'rural' if loc['is_rural'] else 'urban or semi-urban'}. Is this where you want to establish your business?", action="confirm_location")
    if not v("idea_status") and not v("idea"):
        return question("idea", "Tell me about the business you have in mind, or say you would like help choosing one.")
    if v("idea_status") == "explore" and not v("idea"):
        if v("budget") is None:
            return question("budget", "How much money are you willing and able to invest?")
        if not v("budget_kind") or v("budget_kind") == "unknown_budget":
            return question("budget_kind", "Is that your own money, a total project budget, or money you expect to borrow?", ("personal", "total", "borrowing", "other"))
        for key, text in (("skills", "What skills, work experience or business interests would you like to use? You can also say ‘open to learning’."),
                          ("constraints", "What limits should I consider, such as space, time, electricity, travel or activities you want to avoid?")):
            if not v(key):
                return question(key, text)
        return question("recommendations", "Here are regional possibilities from our existing catalogue. Choose one to assess, describe a change, or ask for alternatives." if state["recommendations"] else "I don’t have a supported match for these constraints yet. Tell me another interest, change your budget, or describe an idea; I won’t invent local opportunities.")
    if not v("idea"):
        return question("idea", "What business would you like to establish?")
    if not v("activity"):
        return question("activity", "Will you make or process products, sell them, distribute them, or provide a service?", ("manufacture", "process", "retail", "distribute", "service", "other"))
    if not v("products"):
        return question("products", "What specific products will you make or sell, or what services will you provide?")
    if not state["classification"]:
        return question("idea", "I need to understand the main activity more clearly. What will you do for your customers, and what will they pay for?")
    # ODOP is offered while shaping the idea, not as an end-of-flow requirement.
    if state.get("odop") and not v("odop_preference"):
        odop = state["odop"]
        return question("odop_preference", f"Our district ODOP record lists {odop['product']}. Would you like to explore a connection, keep your original idea, or skip ODOP?", ("explore", "keep", "reject"), "ODOP is optional. Alignment does not establish scheme eligibility or require changing your idea.")
    if state.get("odop") and v("odop_preference") == "explore" and not state.get("odop_explained"):
        return question("odop_explore", f"The recorded ODOP product is {state['odop']['product']}. Your sector {'may align; product and scheme conditions still need checking' if state['odop']['aligned'] else 'is not a sector match; I will preserve your idea'}. Describe a modification or keep your idea.", ("keep", "reject"))
    for key, text in (("operations", "What equipment, supplies, electricity or people will you need to run this activity?"),
                      ("scale", f"What capacity do you plan for {v('products')}? For example, give products or customers per day or month.")):
        if not v(key):
            return question(key, text)
    if not state["business_confirmed"]:
        c = state["classification"]
        return question("business_confirmation", f"I understand: {v('products')}; activity: {v('activity')}; scale: {v('scale')}; requirements: {v('operations')}. This maps to {c['category_id']} / {c['sector']}. Is this correct?", action="confirm_business")
    if v("budget") is not None and v("budget_kind") is None:
        return question("budget_kind", "Does your investment amount mean your own contribution, the total project budget, or borrowing capacity?", ("personal", "total", "borrowing", "other"))
    if v("budget_kind") == "other" and not v("funding_source"):
        return question("funding_source", "Where will this money come from, and what part is your own contribution?")
    if not v("premises"):
        return question("premises", f"Where will you operate {v('products')}? Do you own premises, need to rent or buy, have shared space, or work without fixed premises?", ("owned", "rented", "shared", "purchase", "mobile"))
    if not v("space") and v("premises") != "mobile":
        return question("space", f"What space is available or required for {v('operations')} at your planned capacity? Include the area and unit if known.", explanation="Allow space for the actual equipment, safe working and storage. I cannot infer a floor area without a layout.")
    if v("premises_suitable") is not True:
        text = "Tell me what you’ll change about the space, equipment or capacity before we estimate costs." if v("premises_suitable") is False else "Is this site or operating arrangement suitable for your equipment, utilities and planned capacity?"
        return question("premises_suitable", text, (True, False), "If unsuitable, change the premises or capacity before estimating costs.")
    if v("premises") in ("rented", "shared"):
        if v("rent_amount") is None:
            return question("rent_amount", "What rent do you expect to pay? Please include whether it is per month or per year." if v("premises") == "rented" else "What fee do you expect for the shared facility, per month or per year? If it is free, tell me zero per month.")
        if not v("rent_period"):
            return question("rent_period", "Is that rent per month or per year?", ("monthly", "annual"))
    if not state["regional"]:
        return question("regional", "I couldn’t finish the regional assessment. Retry when connected; your answers are saved.")
    if not v("cost_items"):
        estimate = state.get("estimate")
        lead = f"The existing catalogue range for {estimate['label']} is ₹{estimate['low']:,.0f}–₹{estimate['high']:,.0f}. This is an indicative reference, not a quote for your capacity. " if estimate else "There is no supported catalogue cost for this exact activity. "
        return question("cost_items", lead + "Tell me the applicable setup costs: equipment or tools, premises preparation, initial stock, working capital and other setup expenses. You can enter only the items your business needs below.", explanation="Use supplier estimates and applicable costs. Avoid counting initial stock twice in working capital. Land purchase is excluded by the existing DPR rules, and rent remains an operating expense. No budget amount is silently used as project cost.")
    if not v("cost_basis"):
        return question("cost_basis", "What does this outlay cover, and what is its basis? Mention equipment or tools, stock/raw materials, setup and working capital where applicable.")
    if v("personal_contribution") is None:
        return question("personal_contribution", f"Your setup estimates add up to ₹{v('project_cost'):,.0f}. How much of your own money can you contribute? This is separate from a loan, a subsidy or a total budget; zero is a valid answer.")
    if not state["assessment"]:
        return question("calculation", "The financial assessment could not finish. Retry; I won’t use an old estimate.")
    if v("financing_choice") == "increase":
        return question("personal_contribution", "How much will your revised personal contribution be? I’ll recalculate the shortfall.")
    if not v("financing_choice"):
        gap = state["assessment"]["capital_deficit"]
        return question("financing_choice", f"Estimated outlay: ₹{v('project_cost'):,.0f}. Your own contribution: ₹{v('personal_contribution'):,.0f}. Remaining funding need: ₹{gap:,.0f}. Which financing path would you like to explore?", ("increase", "normal", "sca") if gap else ("self", "normal", "sca"), "Normal bank borrowing and SCA margin assistance use the existing loan rules. Subsidies are shown separately and are not guaranteed funds.")
    if v("financing_choice") == "self" and state["assessment"]["capital_deficit"] > 0:
        return question("financing_choice", "Your own contribution does not cover this outlay. Choose how to address the remaining need.", ("increase", "normal", "sca"))
    if not v("enterprise_name"):
        return question("enterprise_name", "What name would you like for your enterprise? Say ‘suggest names’ if you need ideas.")
    return question("ready", "Your details are ready to review. You can correct any answer or generate the existing feasibility report.")


async def advance(state):
    if state.get('experience') == 'adaptive':
        from app.core.adaptive_onboarding import advance as adaptive_advance
        return await adaptive_advance(state)
    costs = value(state, "cost_items")
    if costs:
        total = confirmed_project_outlay(costs)
        if value(state, "project_cost") is not None and abs(value(state, "project_cost") - total) > 0.01:
            state["pending_changes"]["project_cost"] = total
            state["assessment"] = None
    state["classification"] = classify(state)
    if state.get("location") and state["location_confirmed"] and not state["pending_changes"] and not state["paused"]:
        if state.get("odop") is None:
            state["odop"] = verified_odop(state)
        if value(state, "idea_status") == "explore" and all(value(state, k) is not None for k in ("budget", "budget_kind", "skills", "constraints")):
            if not state["recommendations"] or any(r["id"] in state["rejected"] for r in state["recommendations"]):
                state["recommendations"] = await assess_recommendations(state)
        c = state["classification"]
        if c and state["business_confirmed"] and state["regional"] is None:
            try:
                state["regional"] = await asyncio.wait_for(regional_assessment(state), timeout=30)
                state.pop("regional_error", None)
            except Exception:
                state["regional"] = None
                state["regional_error"] = "Regional data is temporarily unavailable. Please retry."
        if c and state["regional"] and all(value(state, k) is not None for k in ("operations", "scale", "premises")) and value(state, "premises_suitable"):
            entries = catalogue_entries(state)
            if entries:
                e = entries[0]
                state["estimate"] = {"label": e["enterprise_name"], "low": e["typical_project_cost_range"][0], "high": e["typical_project_cost_range"][1], "source": "existing_sector_catalog", "is_estimate": True}
        prerequisites = ("project_cost", "cost_items", "cost_basis", "personal_contribution", "promoter_category", "gender", "operations", "scale", "premises")
        rent_ready = value(state, "premises") not in ("rented", "shared") or all(value(state, k) is not None for k in ("rent_amount", "rent_period"))
        budget_ready = (value(state, "budget") is None or value(state, "budget_kind") not in (None, "unknown_budget")) and (value(state, "budget_kind") != "other" or value(state, "funding_source"))
        space_ready = value(state, "premises") == "mobile" or value(state, "space") is not None
        if not state["assessment"] and c and state["business_confirmed"] and state["regional"] and value(state, "premises_suitable") and rent_ready and space_ready and budget_ready and all(value(state, k) is not None for k in prerequisites):
            try:
                state["assessment"] = financial_assessment(state)
                state.pop("calculation_error", None)
                for f in state["fields"].values():
                    f["changed"] = False
            except Exception:
                state["assessment"] = None
                state["calculation_error"] = "The financial engine could not calculate this input. Check your amounts and retry."
    state["next"] = next_question(state)
    if state["next"]["field"] == "odop_preference":
        state["odop_offered"] = True
    if state.get("language_ambiguities") and state["next"]["field"] in ("activity", "products", "operations", "scale", "budget_kind", "space", "rent_period"):
        clarification = state["language_ambiguities"][0]
        # A contextual question cannot insert money, eligibility or geographical claims.
        if not re.search(r"[₹\d]|eligible|subsid|interest rate", clarification, re.I):
            state["next"]["text"] = clarification + " " + state["next"]["text"]
    state["missing_information"] = [state["next"]["field"]] if state["next"]["field"] != "ready" else []
    state["unresolved_ambiguities"] = list(state.get("pending_changes", {}).keys())
    return state


def report_input(state, language="en"):
    if state["next"]["field"] != "ready" or state["pending_changes"] or not state["assessment"]:
        raise ValueError("Please finish the missing details before generating an assessment.")
    c, loc = state["classification"], state["location"]
    premise = value(state, "premises")
    rent = state["assessment"]["monthly_rent"] if premise in ("rented", "shared") else 0
    capacity = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*(?:litres?|liters?|kg|units?|customers?|orders?|pieces?)\s*(?:per month|a month|/month)", value(state, "scale", ""), re.I)
    monthly_units = (float(capacity[1].replace(",", "")) or None) if capacity else None
    details = "; ".join(f"{k}: {value(state, k)}" for k in ("idea", "products", "operations", "scale", "space", "cost_basis", "odop_preference", "financing_choice") if value(state, k) is not None)
    return {"enterprise_name": value(state, "enterprise_name"), "business_category": c["business_category"],
        "sector": c["sector"], "promoter_name": value(state, "name"), "promoter_category": value(state, "promoter_category"),
        "gender": value(state, "gender"), **{k: loc[k] for k in ("state_name", "district_name", "block_name", "village_name", "is_rural", "latitude", "longitude")},
        "project_cost": value(state, "project_cost"), "project_cost_components": value(state, "cost_items"),
        "financing_choice": value(state, "financing_choice"), "odop_preference": value(state, "odop_preference"),
        "available_margin_capital": value(state, "personal_contribution"),
        "annual_turnover_estimate": 0, "premise_type": premise, "expected_monthly_units": monthly_units,
        "monthly_rent": rent, "tenure_years": state["assessment"]["normal_loan"]["tenure_years"],
        "moratorium_months": state["assessment"]["normal_loan"]["moratorium_months"],
        "language": language, "additional_business_details": details[:1000]}
