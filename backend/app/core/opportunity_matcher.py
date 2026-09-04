"""
opportunity_matcher.py — Regional Alternative Enterprise Recommendation Engine.

When the XGBoost ML Viability Classifier flags an enterprise as RECONSIDER,
this engine suggests alternative enterprise ideas that are better suited to
the applicant's location, financial capacity, and local infrastructure.

Architecture:
    Tier 1 (Primary):   Groq Cloud LLM — Contextual, intelligent recommendations
    Tier 2 (Fallback):  Deterministic 16-sector archetype catalog with composite scoring

Public API:
    get_alternative_recommendations(context: dict) -> list[dict]
"""

from __future__ import annotations

import json
import logging
import os
import math
from dataclasses import dataclass, asdict, field
from typing import Optional

logger = logging.getLogger("udyam_saathi.opportunity_matcher")

# ---------------------------------------------------------------------------
#  16-Sector Archetype Catalog (Deterministic Fallback)
# ---------------------------------------------------------------------------

SECTOR_CATALOG = [
    {
        "sector_id": "vermicompost",
        "enterprise_name": "Vermicompost & Organic Fertilizer Production Unit",
        "sector": "agriculture_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [150000, 500000],
        "typical_turnover_multiplier": 1.8,
        "opex_ratio": 0.55,
        "ideal_infra_min": 4.0,
        "weather_risk_max": 0.50,
        "state_affinities": ["Maharashtra", "Karnataka", "Tamil Nadu", "Madhya Pradesh", "Uttar Pradesh"],
        "description": "Organic vermicompost production using locally sourced agricultural waste. Low capital, high demand from organic farming sector.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "drone_custom_hiring",
        "enterprise_name": "Agricultural Drone Custom Hiring Centre",
        "sector": "service",
        "business_category": "service",
        "typical_project_cost_range": [400000, 1200000],
        "typical_turnover_multiplier": 2.2,
        "opex_ratio": 0.45,
        "ideal_infra_min": 5.0,
        "weather_risk_max": 0.40,
        "state_affinities": ["Maharashtra", "Telangana", "Andhra Pradesh", "Punjab", "Haryana", "Madhya Pradesh"],
        "description": "Drone-based crop spraying and aerial survey services for farmers. High-tech, growing government push for drone adoption.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "dairy_aggregation",
        "enterprise_name": "Dairy Milk Collection & Chilling Centre",
        "sector": "dairy",
        "business_category": "manufacturing",
        "typical_project_cost_range": [300000, 900000],
        "typical_turnover_multiplier": 1.6,
        "opex_ratio": 0.60,
        "ideal_infra_min": 5.0,
        "weather_risk_max": 0.45,
        "state_affinities": ["Gujarat", "Rajasthan", "Uttar Pradesh", "Maharashtra", "Karnataka", "West Bengal"],
        "description": "Village-level milk procurement, chilling, and supply to district cooperatives. Stable demand with assured buyback.",
        "relevant_scheme": "PMFME",
    },
    {
        "sector_id": "solar_pump_repair",
        "enterprise_name": "Solar Pump Installation & Repair Workshop",
        "sector": "service",
        "business_category": "service",
        "typical_project_cost_range": [200000, 600000],
        "typical_turnover_multiplier": 2.0,
        "opex_ratio": 0.40,
        "ideal_infra_min": 4.5,
        "weather_risk_max": 0.55,
        "state_affinities": ["Rajasthan", "Madhya Pradesh", "Gujarat", "Maharashtra", "Uttar Pradesh", "Bihar"],
        "description": "Installation, maintenance, and repair of solar-powered irrigation pumps under PM-KUSUM scheme.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "bamboo_crafts",
        "enterprise_name": "Bamboo Craft & Furniture Manufacturing Unit",
        "sector": "handicraft",
        "business_category": "manufacturing",
        "typical_project_cost_range": [200000, 800000],
        "typical_turnover_multiplier": 1.7,
        "opex_ratio": 0.50,
        "ideal_infra_min": 3.5,
        "weather_risk_max": 0.60,
        "state_affinities": ["Assam", "Tripura", "Meghalaya", "West Bengal", "Odisha", "Jharkhand", "Karnataka"],
        "description": "Bamboo-based furniture, baskets, and decorative items. National Bamboo Mission provides raw material support.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "millet_bakery",
        "enterprise_name": "Millet-Based Bakery & Snack Processing Unit",
        "sector": "food_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [250000, 750000],
        "typical_turnover_multiplier": 1.9,
        "opex_ratio": 0.52,
        "ideal_infra_min": 5.0,
        "weather_risk_max": 0.45,
        "state_affinities": ["Rajasthan", "Karnataka", "Andhra Pradesh", "Tamil Nadu", "Madhya Pradesh", "Odisha"],
        "description": "Processing millets (ragi, jowar, bajra) into cookies, breads, and health snacks. Aligned with International Year of Millets momentum.",
        "relevant_scheme": "PMFME",
    },
    {
        "sector_id": "tailoring_unit",
        "enterprise_name": "Women's Tailoring & Garment Production Unit",
        "sector": "textile",
        "business_category": "manufacturing",
        "typical_project_cost_range": [100000, 400000],
        "typical_turnover_multiplier": 2.0,
        "opex_ratio": 0.45,
        "ideal_infra_min": 3.0,
        "weather_risk_max": 0.70,
        "state_affinities": ["All"],
        "description": "Small-scale garment stitching and uniform production. Extremely low capital barrier, high local demand.",
        "relevant_scheme": "Stand-Up India",
    },
    {
        "sector_id": "honey_processing",
        "enterprise_name": "Honey Collection, Processing & Packaging Unit",
        "sector": "agriculture_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [200000, 600000],
        "typical_turnover_multiplier": 2.1,
        "opex_ratio": 0.48,
        "ideal_infra_min": 3.5,
        "weather_risk_max": 0.50,
        "state_affinities": ["West Bengal", "Rajasthan", "Uttar Pradesh", "Bihar", "Jharkhand", "Uttarakhand"],
        "description": "Beekeeping, honey extraction, and branded packaging. KVIC provides subsidized bee colonies.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "fish_feed",
        "enterprise_name": "Fish Feed Manufacturing & Supply Unit",
        "sector": "aquaculture",
        "business_category": "manufacturing",
        "typical_project_cost_range": [300000, 900000],
        "typical_turnover_multiplier": 1.8,
        "opex_ratio": 0.55,
        "ideal_infra_min": 5.0,
        "weather_risk_max": 0.45,
        "state_affinities": ["Andhra Pradesh", "West Bengal", "Odisha", "Bihar", "Assam", "Tamil Nadu"],
        "description": "Compounded fish feed pellets for inland aquaculture. Growing demand as India pushes fish production.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "turmeric_processing",
        "enterprise_name": "Turmeric Grinding, Polishing & Packaging Unit",
        "sector": "spice_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [200000, 700000],
        "typical_turnover_multiplier": 2.0,
        "opex_ratio": 0.50,
        "ideal_infra_min": 4.5,
        "weather_risk_max": 0.50,
        "state_affinities": ["Telangana", "Andhra Pradesh", "Tamil Nadu", "Maharashtra", "Karnataka", "Odisha"],
        "description": "Value-addition to raw turmeric — cleaning, polishing, grinding, and retail-ready packaging.",
        "relevant_scheme": "PMFME",
    },
    {
        "sector_id": "atta_chakki",
        "enterprise_name": "Automatic Flour Mill (Atta Chakki) Unit",
        "sector": "food_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [150000, 500000],
        "typical_turnover_multiplier": 1.7,
        "opex_ratio": 0.58,
        "ideal_infra_min": 4.0,
        "weather_risk_max": 0.60,
        "state_affinities": ["All"],
        "description": "Automated wheat/grain flour milling. Universal demand, simple operations, low maintenance.",
        "relevant_scheme": "MUDRA",
    },
    {
        "sector_id": "electric_vehicle_repair",
        "enterprise_name": "E-Vehicle & Battery Repair Service Centre",
        "sector": "service",
        "business_category": "service",
        "typical_project_cost_range": [300000, 800000],
        "typical_turnover_multiplier": 2.3,
        "opex_ratio": 0.40,
        "ideal_infra_min": 5.5,
        "weather_risk_max": 0.50,
        "state_affinities": ["Uttar Pradesh", "Delhi", "Maharashtra", "Gujarat", "Tamil Nadu", "Karnataka", "Rajasthan"],
        "description": "Repair and servicing of e-rickshaws, e-scooters, and lithium-ion batteries. Rapidly growing market.",
        "relevant_scheme": "MUDRA",
    },
    {
        "sector_id": "mushroom_cultivation",
        "enterprise_name": "Oyster/Button Mushroom Cultivation & Supply Unit",
        "sector": "agriculture_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [100000, 400000],
        "typical_turnover_multiplier": 2.5,
        "opex_ratio": 0.42,
        "ideal_infra_min": 3.0,
        "weather_risk_max": 0.55,
        "state_affinities": ["Himachal Pradesh", "Uttarakhand", "West Bengal", "Odisha", "Jharkhand", "Assam"],
        "description": "Indoor mushroom farming using paddy straw substrate. Very low space and capital requirement, high margins.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "detergent_soap",
        "enterprise_name": "Detergent Powder & Liquid Soap Manufacturing Unit",
        "sector": "chemicals",
        "business_category": "manufacturing",
        "typical_project_cost_range": [200000, 600000],
        "typical_turnover_multiplier": 1.9,
        "opex_ratio": 0.52,
        "ideal_infra_min": 4.5,
        "weather_risk_max": 0.60,
        "state_affinities": ["All"],
        "description": "Production of detergent powder, liquid soap, and cleaning agents. Constant household demand.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "led_assembly",
        "enterprise_name": "LED Bulb & Tube Light Assembly Unit",
        "sector": "electronics",
        "business_category": "manufacturing",
        "typical_project_cost_range": [250000, 700000],
        "typical_turnover_multiplier": 2.0,
        "opex_ratio": 0.48,
        "ideal_infra_min": 5.0,
        "weather_risk_max": 0.55,
        "state_affinities": ["Gujarat", "Maharashtra", "Uttar Pradesh", "Tamil Nadu", "Rajasthan"],
        "description": "Assembly of LED bulbs from imported/domestic components. Government procurement through EESL/UJALA creates demand.",
        "relevant_scheme": "PMEGP",
    },
    {
        "sector_id": "papad_pickle",
        "enterprise_name": "Papad, Pickle & Ready-to-Eat Snacks Unit",
        "sector": "food_processing",
        "business_category": "manufacturing",
        "typical_project_cost_range": [100000, 350000],
        "typical_turnover_multiplier": 2.2,
        "opex_ratio": 0.48,
        "ideal_infra_min": 3.0,
        "weather_risk_max": 0.60,
        "state_affinities": ["All"],
        "description": "Traditional papad, pickles, and snack foods. Women SHG-friendly, minimal mechanization, strong local demand.",
        "relevant_scheme": "PMFME",
    },
]


@dataclass
class AlternativeRecommendation:
    """A single alternative enterprise recommendation."""
    rank: int
    enterprise_name: str
    sector: str
    business_category: str
    estimated_project_cost: float
    estimated_annual_turnover: float
    estimated_dscr: float
    relevant_scheme: str
    rationale: str
    suitability_score: float  # 0-100 composite score
    source: str  # "GROQ_LLM" or "DETERMINISTIC_FALLBACK"

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
#  Tier 2: Deterministic Fallback Engine
# ---------------------------------------------------------------------------

def _compute_state_affinity(sector_entry: dict, state_name: str) -> float:
    """Score 0.0-1.0 for how well this sector matches the applicant's state."""
    affinities = sector_entry.get("state_affinities", [])
    if "All" in affinities:
        return 0.65  # Universal baseline
    state_lower = state_name.lower().strip()
    for s in affinities:
        if s.lower().strip() == state_lower:
            return 1.0
    return 0.25  # No specific affinity


def _compute_deterministic_dscr(
    project_cost: float,
    turnover_multiplier: float,
    opex_ratio: float,
    subsidy_pct: float = 0.25,
    promoter_pct: float = 0.10,
    interest_rate: float = 0.11,
    tenure_years: int = 7,
) -> float:
    """Simulate DSCR for a given sector archetype."""
    subsidy = project_cost * subsidy_pct
    promoter_margin = project_cost * promoter_pct
    loan_principal = max(project_cost - subsidy - promoter_margin, 1.0)
    
    annual_turnover = project_cost * turnover_multiplier
    annual_noi = annual_turnover * (1 - opex_ratio)
    
    # Simple EMI calculation
    monthly_rate = interest_rate / 12
    n_months = tenure_years * 12
    if monthly_rate > 0 and n_months > 0:
        monthly_emi = loan_principal * (monthly_rate * (1 + monthly_rate) ** n_months) / ((1 + monthly_rate) ** n_months - 1)
    else:
        monthly_emi = loan_principal / max(n_months, 1)
    
    annual_debt_service = monthly_emi * 12
    dscr = annual_noi / annual_debt_service if annual_debt_service > 0 else 5.0
    return round(dscr, 2)


def _deterministic_recommendations(
    rejected_sector: str,
    state_name: str,
    district_name: str,
    project_cost: float,
    margin_capital: float,
    infrastructure_score: float,
    weather_risk_score: float,
    cpi_inflation_pct: float,
    promoter_category: str,
    max_results: int = 5,
) -> list[AlternativeRecommendation]:
    """
    Deterministic fallback: scores each of the 16 sectors against the
    applicant's context and returns the top N ranked by composite score.
    """
    promoter_pct = 0.05 if promoter_category.lower() != "general" else 0.10
    candidates = []

    for entry in SECTOR_CATALOG:
        # Exclude the rejected sector (fuzzy match)
        if entry["sector_id"].lower() == rejected_sector.lower():
            continue
        if entry["sector"].lower() == rejected_sector.lower():
            continue
        
        # Infrastructure check
        if infrastructure_score < entry["ideal_infra_min"] * 0.7:
            continue  # Too poor infrastructure for this sector
        
        # Weather compatibility
        if weather_risk_score > entry["weather_risk_max"] * 1.3:
            continue  # Climate too hostile

        # Pick a project cost within applicant's budget range
        cost_range = entry["typical_project_cost_range"]
        # Scale to applicant's capital capacity (use their margin_capital as anchor)
        target_cost = min(
            max(margin_capital / promoter_pct, cost_range[0]),
            cost_range[1]
        )
        target_cost = max(target_cost, cost_range[0])

        turnover = target_cost * entry["typical_turnover_multiplier"]
        dscr = _compute_deterministic_dscr(
            target_cost,
            entry["typical_turnover_multiplier"],
            entry["opex_ratio"],
            subsidy_pct=0.25,
            promoter_pct=promoter_pct,
        )
        
        # Must meet minimum DSCR threshold
        if dscr < 1.25:
            continue
        
        # Composite scoring
        state_affinity = _compute_state_affinity(entry, state_name)
        dscr_score = min(dscr / 2.5, 1.0) * 30  # 0-30 points
        infra_compatibility = min(infrastructure_score / entry["ideal_infra_min"], 1.0) * 20  # 0-20 points
        affinity_score = state_affinity * 25  # 0-25 points
        cost_fit = (1 - abs(target_cost - project_cost) / max(project_cost, 1)) * 15  # 0-15 points
        weather_fit = max(1 - weather_risk_score / entry["weather_risk_max"], 0) * 10  # 0-10 points
        
        composite = dscr_score + infra_compatibility + affinity_score + max(cost_fit, 0) + weather_fit
        
        candidates.append({
            "entry": entry,
            "project_cost": round(target_cost),
            "turnover": round(turnover),
            "dscr": dscr,
            "composite": round(composite, 1),
        })
    
    # Sort by composite score descending, deduplicate by sector domain
    candidates.sort(key=lambda x: x["composite"], reverse=True)
    
    # Domain diversity: don't suggest 3 food_processing variants
    seen_sectors = set()
    results = []
    for c in candidates:
        sector_domain = c["entry"]["sector"]
        if sector_domain in seen_sectors:
            continue
        seen_sectors.add(sector_domain)
        
        results.append(AlternativeRecommendation(
            rank=len(results) + 1,
            enterprise_name=c["entry"]["enterprise_name"],
            sector=c["entry"]["sector"],
            business_category=c["entry"]["business_category"],
            estimated_project_cost=c["project_cost"],
            estimated_annual_turnover=c["turnover"],
            estimated_dscr=c["dscr"],
            relevant_scheme=c["entry"]["relevant_scheme"],
            rationale=c["entry"]["description"],
            suitability_score=c["composite"],
            source="DETERMINISTIC_FALLBACK",
        ))
        
        if len(results) >= max_results:
            break
    
    return results


# ---------------------------------------------------------------------------
#  Tier 1: Groq Cloud LLM Recommendation Engine
# ---------------------------------------------------------------------------

def _build_llm_prompt(context: dict) -> str:
    """Build a structured prompt for Groq LLM to generate recommendations."""
    return f"""You are an expert MSME credit advisor and rural enterprise consultant for the Indian banking system.

An entrepreneur's proposed enterprise has been flagged as RECONSIDER by our ML viability classifier. 
Your task is to suggest 5 alternative enterprise ideas that are better suited for their location, 
financial capacity, and local conditions.

## Rejected Enterprise Context
- **Enterprise Name**: {context.get('enterprise_name', 'N/A')}
- **Sector**: {context.get('sector', 'N/A')}
- **ML Verdict**: RECONSIDER ({context.get('ml_confidence_pct', 0):.1f}% confidence)
- **DSCR**: {context.get('dscr', 0):.2f} (RBI benchmark: ≥1.33)
- **Top Risk Factor**: {context.get('top_risk_factor', 'N/A')}

## Applicant Profile
- **Location**: {context.get('village_name', '')}, {context.get('district_name', '')}, {context.get('state_name', '')}
- **Rural/Urban**: {'Rural' if context.get('is_rural', True) else 'Urban'}
- **Promoter Category**: {context.get('promoter_category', 'general')}
- **Available Margin Capital**: ₹{context.get('margin_capital', 0):,.0f}
- **Original Project Cost**: ₹{context.get('project_cost', 0):,.0f}

## Local Conditions
- **Infrastructure Score**: {context.get('infrastructure_score', 6.0):.1f}/10
- **MSME Density**: {context.get('msme_density_per_10k', 8.0):.1f} per 10,000 population
- **CPI Inflation**: {context.get('cpi_inflation_pct', 5.0):.1f}%
- **Weather Risk**: {context.get('weather_risk_score', 0.2):.2f}/1.0
- **Competition Intensity**: {context.get('competition_intensity', 0.3):.2f}/1.0

## Requirements
Suggest exactly 5 alternative enterprises that:
1. Are viable for this specific location and infrastructure level
2. Fit within the applicant's financial capacity (margin capital and project cost range)
3. Would likely achieve DSCR ≥ 1.40
4. Are eligible for PMEGP/PMFME/MUDRA/Stand-Up India schemes
5. Do NOT repeat the rejected sector

Respond ONLY with valid JSON array. Each object must have exactly these fields:
```json
[
  {{
    "enterprise_name": "...",
    "sector": "...",
    "business_category": "manufacturing or service",
    "estimated_project_cost": 500000,
    "estimated_annual_turnover": 900000,
    "estimated_dscr": 1.85,
    "relevant_scheme": "PMEGP",
    "rationale": "2-3 sentence explanation of why this enterprise suits this location and applicant"
  }}
]
```"""


async def _groq_llm_recommendations(
    context: dict,
    api_key: str,
    max_results: int = 5,
) -> list[AlternativeRecommendation]:
    """
    Call Groq Cloud LLM for intelligent, context-aware recommendations.
    Returns empty list on failure (triggers deterministic fallback).
    """
    if not api_key:
        logger.warning("GROQ_API_KEY_LLM not configured, skipping LLM recommendations")
        return []

    prompt = _build_llm_prompt(context)
    content = ""

    # Strategy A: Use official Groq SDK
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key, timeout=20.0)
        
        models_to_try = [
            os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
            "openai/gpt-oss-20b",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
        ]
        # Deduplicate while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        for model_name in models_to_try:
            try:
                chat_completion = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are an MSME credit advisory engine. Respond ONLY with valid JSON arrays. No markdown, no explanation, no commentary."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                content = chat_completion.choices[0].message.content
                if content:
                    logger.info(f"Groq LLM responded successfully using model '{model_name}'")
                    break
            except Exception as model_err:
                logger.warning(f"Groq model '{model_name}' failed ({model_err}), trying next candidate...")
                continue

    except Exception as sdk_err:
        logger.warning(f"Groq SDK invocation error: {sdk_err}")

    # If content still empty, return empty list (triggers deterministic fallback)
    if not content:
        return []

    try:
        # Parse JSON — handle both direct arrays and wrapped objects
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for key in ("recommendations", "alternatives", "enterprises", "results", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                if "enterprise_name" in parsed:
                    parsed = [parsed]
                else:
                    logger.warning(f"Groq LLM returned unexpected JSON structure: {list(parsed.keys())}")
                    return []

        if not isinstance(parsed, list):
            logger.warning("Groq LLM did not return a JSON array")
            return []

        recommendations = []
        for idx, item in enumerate(parsed[:max_results]):
            try:
                rec = AlternativeRecommendation(
                    rank=idx + 1,
                    enterprise_name=str(item.get("enterprise_name", "Alternative Enterprise")),
                    sector=str(item.get("sector", "general")),
                    business_category=str(item.get("business_category", "manufacturing")),
                    estimated_project_cost=float(item.get("estimated_project_cost", 500000)),
                    estimated_annual_turnover=float(item.get("estimated_annual_turnover", 800000)),
                    estimated_dscr=float(item.get("estimated_dscr", 1.50)),
                    relevant_scheme=str(item.get("relevant_scheme", "PMEGP")),
                    rationale=str(item.get("rationale", "Suitable for the location and financial profile.")),
                    suitability_score=80.0 - (idx * 5),
                    source="GROQ_LLM",
                )
                recommendations.append(rec)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed LLM recommendation {idx}: {e}")
                continue

        logger.info(f"Groq LLM returned {len(recommendations)} alternative recommendations")
        return recommendations

    except Exception as e:
        logger.error(f"Error parsing Groq LLM recommendations: {e}")
        return []


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

async def get_alternative_recommendations(context: dict) -> dict:
    """
    Main entry point. Tries Groq LLM first, falls back to deterministic engine.

    Args:
        context: Dictionary containing the rejected enterprise's full context:
            - enterprise_name, sector, business_category
            - state_name, district_name, village_name, is_rural
            - project_cost, margin_capital, annual_turnover_estimate
            - promoter_category, dscr, ml_confidence_pct
            - infrastructure_score, msme_density_per_10k
            - cpi_inflation_pct, weather_risk_score, competition_intensity
            - top_risk_factor

    Returns:
        dict with keys: recommendations (list), source (str), count (int)
    """
    from app.config import settings

    api_key = settings.GROQ_API_KEY_LLM or settings.GROQ_API_KEY or ""
    source = "GROQ_LLM"

    # Tier 1: Try Groq LLM
    recommendations = await _groq_llm_recommendations(context, api_key)

    # Tier 2: Deterministic fallback if LLM failed or returned nothing
    if not recommendations:
        source = "DETERMINISTIC_FALLBACK"
        recommendations = _deterministic_recommendations(
            rejected_sector=context.get("sector", ""),
            state_name=context.get("state_name", ""),
            district_name=context.get("district_name", ""),
            project_cost=context.get("project_cost", 500000),
            margin_capital=context.get("margin_capital", 50000),
            infrastructure_score=context.get("infrastructure_score", 6.0),
            weather_risk_score=context.get("weather_risk_score", 0.2),
            cpi_inflation_pct=context.get("cpi_inflation_pct", 5.0),
            promoter_category=context.get("promoter_category", "general"),
            max_results=5,
        )
        logger.info(f"📊 Deterministic fallback returned {len(recommendations)} recommendations")

    return {
        "recommendations": [r.to_dict() for r in recommendations],
        "source": source,
        "count": len(recommendations),
        "rejected_enterprise": context.get("enterprise_name", ""),
        "rejected_sector": context.get("sector", ""),
    }
