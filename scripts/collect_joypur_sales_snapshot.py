"""Freeze public evidence for a cross-model sales comparison; never call an LLM.

Uses a read-only PostgreSQL connection and fresh public HTTP requests. No saved
beneficiary reports, user tables, authentication tokens or API keys are exported.
Run from the repository root with the project's Python environment.
"""
import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import settings
from app.core.sales_forecast import build_payload, SYSTEM_PROMPT
from app.core.odop_matcher import match_odop
from app.models.schemas import UserInput

OUT = ROOT / "examples/llm_payloads/live_joypur_2026-10-30"
OGD = "https://api.data.gov.in/resource/"
UDYAM_ID = "8b68ae56-84cf-4728-a0a6-1be11028dea7"
AMENITIES_ID = "423cdbbe-0a01-4396-a9d0-638a28e89b83"
CPI_URL = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2322244&lang=1&reg=3"
DAIRY_URL = "https://banglardairy.com/api_bd/product_all"
CENSUS_URL = "https://censusindia.gov.in/nada/index.php/catalog/6530"


def serialise(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def save(name, value):
    text = json.dumps(value, indent=2, ensure_ascii=False, default=serialise) + "\n"
    for secret in [settings.DATA_GOV_IN_API_KEY, settings.DATABASE_URL,
                   settings.GROQ_API_KEY, settings.SARVAM_API_KEY]:
        if secret and secret in text:
            raise ValueError("Refusing to export a configured secret")
    (OUT / name).write_text(text, encoding="utf-8")


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row = []
        elif tag in ("td", "th") and self.row is not None: self.cell = []
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split())); self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row); self.row = None; self.cell = None


async def fresh_get(client, url, params=None):
    for attempt in range(2):
        try:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response
            if attempt:
                return {"status": "unavailable", "http_status": response.status_code}
        except Exception as exc:
            if attempt:
                return {"status": "unavailable", "error_type": type(exc).__name__}


async def database_evidence():
    import asyncpg
    if not settings.DATABASE_URL:
        raise ValueError("A configured public-data database is required for this snapshot")
    c = await asyncpg.connect(settings.DATABASE_URL, timeout=12,
        server_settings={"default_transaction_read_only": "on", "statement_timeout": "18000"})
    try:
        row = await c.fetchrow("""SELECT id,state,district,subdistt,town_village,administrative_level,
            area_name,town_rural_urban,total_households,total_population,male_population,female_population,
            sc_population,st_population,literate_population,total_workers,main_workers,marginal_workers
            FROM census_raw WHERE state='19' AND district='339' AND subdistt='02368'
              AND town_village='328046' AND administrative_level='VILLAGE'""")
        if not row or row["total_population"] != 3136:
            raise ValueError("Jaypur village identity or Census record needs review")
        lgd = await c.fetchrow("""SELECT v.village_code,v.village_census_2011_code,v.village_name,
            v.district_code,v.state_code,v.development_block_code,b.development_block_name
            FROM villages v LEFT JOIN blocks b USING(development_block_code)
            WHERE v.village_census_2011_code=328046 AND v.district_code=305""")
        msme = await c.fetchrow("""SELECT state_name,district_name,lg_dt_code,micro,small,medium,total
            FROM msme_district WHERE district_name='Bankura' AND state_name='West Bengal'""")
        cpi = await c.fetch("""SELECT base_year,year,month,state,sector,index,inflation
            FROM cpi_data WHERE state='West Bengal' AND sector='Rural'
              AND division='CPI (General)' AND year=2026""")
        months = {name: i for i, name in enumerate(
            ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
        cpi = sorted([dict(r) for r in cpi], key=lambda r: (r["year"], months.get(r["month"], 0)), reverse=True)
        return {"village_census_2011": dict(row), "lgd": dict(lgd) if lgd else None,
                "district_msme": dict(msme) if msme else None, "database_cpi_latest": cpi[0] if cpi else None}
    finally:
        await c.close()


async def registered_businesses(client):
    records, metadata, reported_total = [], [], None
    if not settings.DATA_GOV_IN_API_KEY:
        return {"status": "unavailable", "reason": "No configured API key"}, []
    for offset in (0, 500, 1000, 1500):
        response = await fresh_get(client, OGD + UDYAM_ID, {
            "api-key": settings.DATA_GOV_IN_API_KEY, "format": "json", "limit": 500, "offset": offset,
            "filters[State]": "WEST BENGAL", "filters[District]": "BANKURA", "filters[Pincode]": "722138"})
        if isinstance(response, dict):
            metadata.append(response); break
        data = response.json()
        page = data.get("records", [])
        reported_total = int(data.get("total", 0))
        metadata.append({"offset": offset, "count": len(page), "reported_total": reported_total,
                         "title": data.get("title"), "updated_date": data.get("updated_date")})
        records.extend(page)
        if len(records) >= reported_total or not page:
            break
    unique = {}
    for row in records:
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        unique[fingerprint] = row
    dairy = []
    for fingerprint, row in unique.items():
        haystack = str(row.get("EnterpriseName", "")) + " " + str(row.get("Activities", ""))
        if re.search(r"\b(milk|dairy|dairies)\b", haystack, re.I):
            try: activities = json.loads(row.get("Activities") or "[]")
            except (TypeError, ValueError): activities = row.get("Activities")
            dairy.append({"enterprise_name": row.get("EnterpriseName"), "activities": activities,
                          "pincode": str(row.get("Pincode")), "registration_date": row.get("RegistrationDate"),
                          "record_fingerprint": fingerprint, "distance_km": None,
                          "operating_status": "not_verified"})
    summary = {"status": "live_api_registered_business_sample", "source_url": OGD + UDYAM_ID,
        "geographic_scope": "PIN 722138, Bankura; not a verified 5/10-km circle",
        "filters": {"state": "WEST BENGAL", "district": "BANKURA", "pincode": "722138"},
        "api_reported_total": reported_total, "retrieved_records": len(records), "unique_records": len(unique),
        "complete_reported_postcode_result": reported_total is not None and len(records) >= reported_total,
        "explicit_milk_dairy_keyword_matches": len(dairy), "dairy_businesses": dairy,
        "pages": metadata,
        "limitations": ["Postal areas cover multiple localities; no verified radius-based competitor count.",
                        "Milk/dairy keyword matching misses general grocers selling milk and informal businesses.",
                        "Registration is not proof of current operation, revenue, market share or active customers."]}
    return summary, dairy


async def village_amenities(client):
    response = await fresh_get(client, OGD + AMENITIES_ID, {
        "api-key": settings.DATA_GOV_IN_API_KEY, "format": "json", "limit": 10, "filters[village_name]": "Jaypur"})
    if isinstance(response, dict): return response, None
    data = response.json()
    records = data.get("records", [])
    # OGD preserves Excel's leading apostrophe on Census codes, e.g. "'328046".
    selected = [r for r in records if str(r.get("village_code", "")).strip().lstrip("'").lstrip("0") in ("328046", "328046.0")]
    if len(selected) != 1:
        return {"status": "unavailable", "reason": "Exact Census village code did not resolve uniquely"}, None
    row = selected[0]
    def flag(key):
        value = str(row.get(key, "")).strip()
        return True if value == "1" else False if value == "2" else None
    def number(key):
        try: return float(row[key])
        except (KeyError, TypeError, ValueError): return None
    summary = {"status": "historical_village_record_fetched_live", "source_url": OGD + AMENITIES_ID,
        "dataset_title": data.get("title"), "reference_year": row.get("reference_year"),
        "village_code": "328046", "source_village_code": row.get("village_code"), "village_name": row.get("village_name"),
        "block_name": row.get("cd_block_name"), "records_with_same_village_name": data.get("total"),
        "matched_by": "Census village code 328046, not first name match",
        "population_in_source": number("total_population_of_village"),
        "households_in_source": number("total__households_"),
        "commercial_power_hours_summer": number("power_supply_for_commercial_use_summer__april_sept___per_day__in_hours_"),
        "commercial_power_hours_winter": number("power_supply_for_commercial_use_winter__oct__march__per_day__in_hours_"),
        "paved_road_in_village": flag("black_topped__pucca__road__status_a_1__na_2__"),
        "commercial_bank_in_village": flag("commercial_bank__status_a_1__na_2__"),
        "cold_storage_in_village": flag("cold_storage__status_a_1__na_2__"),
        "internet_cafe_in_village": flag("internet_cafes_common_service_centre__csc___status_a_1__na_2__"),
        "nearest_statutory_town": row.get("nearest_statutory_town__name_"),
        "nearest_statutory_town_distance_km": number("nearest_statutory_town__distance_in_km_"),
        "notice": "Fetched now, but the observation year is historical. NA fields remain null; no default power/road/storage values are inserted."}
    return summary, row


async def published_cpi(client):
    response = await fresh_get(client, CPI_URL)
    if isinstance(response, dict):
        verified = OUT / "verified_cpi_publication.json"
        if verified.exists():
            result = json.loads(verified.read_text(encoding="utf-8"))
            result["automated_http_attempt"] = response
            return result
        return response
    parser = TableRows(); parser.feed(response.text)
    for row in parser.rows:
        if "West Bengal" in row:
            index = row.index("West Bengal")
            values = [float(x) for cell in row[index + 1:] for x in re.findall(r"\d+\.\d+", cell)]
            if len(values) >= 6:
                return {"status": "official_publication_fetched_live", "source_url": CPI_URL,
                    "publisher": "MoSPI / Press Information Bureau", "reference_period": "2026-09",
                    "published_on": "2026-10-12", "provisional": True, "base_year": 2024,
                    "state": "West Bengal", "rural_index": values[0], "urban_index": values[1],
                    "combined_index": values[2], "rural_inflation_pct": values[3],
                    "urban_inflation_pct": values[4], "combined_inflation_pct": values[5],
                    "notice": "Latest September release; October CPI is not yet published. CPI is not a milk price or household-income measure."}
    return {"status": "unavailable", "source_url": CPI_URL, "reason": "State CPI row could not be parsed"}


async def producer_products(client):
    response = await fresh_get(client, DAIRY_URL)
    if isinstance(response, dict): return response
    data = response.json()
    products = []
    for row in data.get("data", []):
        if row.get("category_name") != "Milk" or row.get("p_activate_status") != "Active": continue
        def price(key):
            try: return float(row.get(key, 0)) or None
            except (TypeError, ValueError): return None
        products.append({"product_id": row.get("id"), "product_name": row.get("product_name"),
                         "type": row.get("others"), "website_availability": row.get("availability"),
                         "listed_mrp_inr": price("mrp"), "listed_offer_price_inr": price("o_price")})
    return {"status": "producer_catalogue_fetched_live", "publisher": "Banglar Dairy Limited",
            "source_url": DAIRY_URL, "active_milk_products": products,
            "notice": "The producer API reports 0.00 for milk prices; its public website treats that as no displayed price. Null means unavailable, not free milk. Website availability does not confirm stock or delivery in Jaypur."}


async def main():
    import httpx
    OUT.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=18, follow_redirects=True, headers={"User-Agent": "UdyamSaathi/2.0"}) as client:
        db, registered, amenities, cpi, dairy = await asyncio.gather(
            database_evidence(), registered_businesses(client), village_amenities(client),
            published_cpi(client), producer_products(client))
    now = datetime.now(timezone.utc).isoformat()
    registry, _ = registered
    infrastructure, raw_amenities = amenities
    census = db["village_census_2011"]
    rates = json.loads((ROOT / "backend/app/data/growth_rates.json").read_text())
    rate = rates["state_cagr"]["West Bengal"]
    growth = (1 + rate) ** 15
    odop = match_odop(state_name="West Bengal", district_name="Bankura", sector="dairy", enterprise_name="Milk pasteurisation")
    evidence = {
        "demographics": {"status": "historical_census_record_queried_live", "source_url": CENSUS_URL,
            "database_table": "census_raw", "reference_year": 2011, "village": census,
            "lgd_identity": db["lgd"], "population_within_5km": None, "population_within_10km": None,
            "notice": "Village population is not a measured 5/10-km catchment and is not a count of active customers."},
        "population_projection": {"status": "deterministic_projection_assumption", "target_year": 2026,
            "annual_growth_rate": rate, "growth_source": "local growth_rates.json; approximate historical CAGR",
            "projected_population": round(census["total_population"] * growth),
            "projected_households": round(census["total_households"] * growth),
            "formula": "2011 observed value * (1 + state annual CAGR)^15",
            "notice": "Households are projected from the observed 741 households, not estimated by dividing population by a universal household size. Not a new Census count."},
        "district_msme": {"status": "database_record_queried_live", "source_table": "msme_district",
            "record": db["district_msme"], "reference_date": None,
            "notice": "Dataset observation date is unavailable; district registration totals are not village competitors."},
        "registered_businesses": registry, "amenities": infrastructure, "cpi": cpi,
        "database_cpi_for_comparison": {"status": "stored_database_record", "record": db["database_cpi_latest"],
            "notice": "Chronologically sorted by month, not alphabetically. Use the newer official publication above when available."},
        "producer_market_context": dairy,
        "odop": {"status": "local_curated_registry", "record": odop,
            "public_crosscheck_url": "https://msme.wb.gov.in/audit/sites/default/files/ODOP-Bengal%20brochure.pdf",
            "notice": "Local registry is a reference snapshot, not a fresh sanction or proof of dairy demand."},
        "missing_business_evidence": {"confirmed_orders": None, "actual_sales": None,
            "verified_jaypur_milk_selling_price_inr_per_litre": None,
            "verified_raw_milk_supply_litres_per_day": None,
            "verified_raw_milk_procurement_price_inr_per_litre": None},
    }
    user = UserInput(enterprise_name="Proposed Jaypur Milk Pasteurisation and Delivery",
        business_category="manufacturing", sector="dairy", project_cost=2000000,
        annual_turnover_estimate=0, state_name="West Bengal", district_name="Bankura",
        block_name="Jaypur", village_name="Jaypur", sales_forecast_mode="estimate",
        forecast_start_month="2026-11-01", additional_business_details=(
            "Proposed startup buying raw milk, pasteurising it and selling milk by the litre. "
            "Recurring home delivery and occasional direct retail are separate customer groups; do not double-count purchases. "
            "Estimate repeat deliveries per active household according to the proposed route. "
            "There is no supplied evidence of existing customers, orders, prices or raw-milk supply contracts."),
        sales_context={"target_customers": "Households reachable from Jaypur village", "sales_channels": "Home delivery and direct retail",
            "operating_days_per_month": 26, "hours_per_day": 8, "staff_count": 2,
            "local_observations": "Budget, staffing, channels and schedule are proposed comparison-case inputs, not facts fetched from government datasets."})
    payload = build_payload(user, evidence)
    payload["machinery_options"] = [p for p in payload["machinery_options"] if p["profile_id"] == "fa5e4fba9e3e"]
    payload["allowed_profile_ids"] = [None, "fa5e4fba9e3e"]
    payload["output_schema"]["$defs"]["Product"]["properties"]["profile_id"] = {"enum": payload["allowed_profile_ids"]}
    for profile in payload["machinery_options"]:
        profile["capacity_variants"] = [{k: v[k] for k in ("variant_id", "capacity", "total_machinery_cost_inr", "cost_source")}
                                        for v in profile["capacity_variants"]]
    payload["snapshot"] = {"collected_at_utc": now, "location": "Jaypur/Joypur, Bankura, West Bengal; Census village 328046",
        "collection_mode": "fresh_public_API_requests_and_read_only_database_queries",
        "business_input_status": "proposed_case_inputs_not_observed_business_records",
        "machinery_price_status": "existing_catalogue_estimates_not_live_supplier_quotes"}
    payload["known_data_gaps"] += [
        "Freshly fetched historical records do not describe current village operations with certainty.",
        "No verified 5/10-km population, exact operating coordinates, current power hours, achievable selling price or actual new-business customer count.",
        "The official dairy catalogue does not publish nonzero milk prices in the API; do not convert that absence to a zero selling price.",
        "PIN-level registered businesses must not be treated as radius-based direct competitors."]
    save("payload.json", payload)
    data_only = {k: v for k, v in payload.items() if k not in
        {"output_schema", "output_shape_example", "driver_unit_contract", "demand_equations"}}
    save("data.json", data_only)
    save("messages.json", {"messages": [{"role": "system", "content": SYSTEM_PROMPT},
          {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=serialise, separators=(",", ":"))}],
          "temperature": .2, "max_tokens": 8000, "response_format": {"type": "json_object"}})
    save("raw_village_amenities.json", raw_amenities)
    digest = hashlib.sha256((OUT / "payload.json").read_bytes()).hexdigest()
    save("manifest.json", {"collected_at_utc": now, "payload_sha256": digest,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob("*.json") if p.name != "manifest.json"},
        "source_urls": [CENSUS_URL, CPI_URL, OGD + UDYAM_ID, OGD + AMENITIES_ID, DAIRY_URL],
        "notes": ["No LLM was called. Use this identical snapshot and system prompt across models.",
                  "No beneficiary records, authentication headers or configured secrets are exported."]})
    print(json.dumps({"output": str(OUT), "collected_at_utc": now, "payload_sha256": digest,
        "census_population": census["total_population"], "census_households": census["total_households"],
        "registered_businesses": {k: registry.get(k) for k in ["api_reported_total", "retrieved_records", "explicit_milk_dairy_keyword_matches"]},
        "amenities": infrastructure, "cpi": cpi, "producer_catalogue_status": dairy.get("status")}, default=serialise))


if __name__ == "__main__":
    asyncio.run(main())
