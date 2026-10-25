"""Business-specific LLM demand contracts; no free-form expression execution."""
from __future__ import annotations

import math
import json
import logging
import re
from typing import Literal, Any

from pydantic import BaseModel, ConfigDict, Field

from .llm_capacity import CalculationUnit
from .llm_json import response_object, structured_response_format

logger = logging.getLogger(__name__)


Method = Literal["customer_purchases", "service_bookings", "b2b_orders", "manufacturing_orders",
                 "ecommerce", "subscription", "occupancy", "market_share", "other"]
Buyer = Literal["people", "households", "organizations", "visitors", "vehicles", "website_users",
                "contracts", "subscribers", "inventory_units", "other"]
Role = Literal["active_buyers", "reachable_prospects", "conversion_rate", "transactions_per_buyer",
               "units_per_transaction", "qualified_traffic", "repeat_transactions", "starting_subscribers",
               "new_subscribers", "churned_subscribers", "units_per_subscriber", "available_inventory",
               "occupancy", "billing_units_per_inventory", "category_monthly_units", "market_share", "seasonality"]


class DemandInput(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    role: Role
    value: float = Field(ge=0, le=1e14)
    units: str = Field(min_length=1, max_length=100, description="Use buyer_base for count roles; transactions/buyer/month for frequency; output_units/transaction for basket size; fraction for rates. Output units mean the exact accepted sold unit. Explicit equivalent labels such as cups/transaction are allowed only when output_unit=cups.")
    reference_period: Literal["snapshot", "annual_average_month", "normal_month", "forecast_month"]
    source_kind: Literal["actual_records", "verified_local_data", "documented_benchmark", "comparable", "scenario_assumption"]
    source: str = Field(min_length=5, max_length=500)
    evidence_path: str | None = Field(default=None, description="Path to a supplied numeric fact, e.g. evidence.observed_monthly_customers. Required for non-scenario inputs; never fabricate a citation.")
    confidence: Literal["low", "medium", "high"]
    reasoning: str = Field(min_length=10, max_length=700)


class DemandScenario(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    inputs: list[DemandInput] = Field(min_length=2, max_length=8)
    monthly_demand_units: float = Field(ge=0, le=1e14)
    monthly_active_buyers: float | None = Field(default=None, ge=0, le=1e14)
    monthly_transactions: float | None = Field(default=None, ge=0, le=1e14)
    realized_monthly_units: float = Field(ge=0, le=1e14)
    daily_unit_sales: float = Field(ge=0, le=1e14)
    monthly_revenue_inr: float = Field(ge=0, le=1e16)
    capacity_utilization_pct: float = Field(ge=0, le=100)


class DemandScenarios(BaseModel):
    conservative: DemandScenario
    base: DemandScenario
    optimistic: DemandScenario


class IndependentEstimate(BaseModel):
    method: Method
    buyer_base: Buyer
    inputs: list[DemandInput] = Field(min_length=2, max_length=8)
    monthly_demand_units: float = Field(ge=0, le=1e14)
    equation_with_units: str = Field(min_length=10, max_length=800)
    basis: str = Field(min_length=15, max_length=1000)


class DemandForecast(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    industry: str = Field(min_length=2, max_length=120)
    business_model: str = Field(min_length=2, max_length=100, description="E.g. B2C local retail, B2B manufacturing, D2C, subscription.")
    product_service: str = Field(min_length=2, max_length=160)
    target_customer: str = Field(min_length=5, max_length=300)
    buyer_base: Buyer
    location: str = Field(min_length=2, max_length=250)
    maturity: str = Field(min_length=2, max_length=150)
    sales_channel: str = Field(min_length=2, max_length=250)
    buying_cycle: str = Field(min_length=5, max_length=300)
    acquisition_constraints: str = Field(min_length=10, max_length=700)
    method: Method
    output_unit: CalculationUnit
    period: Literal["annual_average_month", "normal_month", "forecast_month"]
    forecast_month: str | None = Field(default=None, description="YYYY-MM when period=forecast_month; otherwise null")
    equation_with_units: str = Field(min_length=10, max_length=900)
    method_reason: str = Field(min_length=20, max_length=900)
    effective_monthly_capacity: float = Field(gt=0, le=1e14)
    scenarios: DemandScenarios
    category_demand: IndependentEstimate | None = None
    independent_cross_check: IndependentEstimate | None = None
    reconciliation: str = Field(min_length=20, max_length=1200)
    uncertainty_drivers: list[str] = Field(min_length=1, max_length=8)
    warnings: list[str] = Field(default_factory=list, max_length=12)
    limitations: list[str] = Field(min_length=1, max_length=10)
    missing_data: list[str] = Field(default_factory=list, max_length=10)
    reality_review: str = Field(min_length=20, max_length=1400)
    reality_reexamined: bool = False
    source_review_required: bool = False
    provisional: bool


DEMAND_PROMPT = """
DEMAND FORECASTING RESPONSIBILITY
You are a senior market research analyst, business feasibility consultant and demand
forecasting specialist. Estimate realistic, defensible business-specific customer
demand. Never produce mechanically plausible but commercially meaningless estimates.
This contract replaces ANY universal household/penetration/frequency/share formula.
Classify industry, B2C/B2B/D2C/subscription/etc., product, sold unit, target customer,
location, maturity, price, channels, buying cycle and acquisition constraints first.
Choose the simplest appropriate method:
- customer_purchases: monthly active reachable buyers * transactions/buyer/month *
  output units/transaction; people or visitors are often more suitable than households.
- service_bookings: bookable active customers * visits/customer/month * sold units/visit.
- b2b_orders / manufacturing_orders: qualified reachable organizations * conversion
  probability * orders/customer/month * output units/order; alternatively use already
  captured active buyers WITHOUT applying conversion again. Describe distribution.
- ecommerce: qualified unique monthly traffic * purchase conversion + incremental
  repeat transactions, then multiply by units/transaction. Repeat transactions must
  exclude first purchases already counted; do not invent unique active buyers.
- subscription: (starting active subscribers + new - churned) * recognized output
  units/subscriber/month. Define the recognized billing unit independently of receipts.
- occupancy: available inventory * obtainable occupancy * billing output units per
  inventory unit/month. Booking counts may be null unless derivable.
- market_share: properly defined monthly category units * defensible competitive share;
  use ONLY for a top-down market-volume method, never after active buyers/conversions.
- other: use a justified customer/transaction equation with dimensionally explicit units.

The runtime supports these semantic input roles (do not add hidden multipliers):
active_buyers OR reachable_prospects + conversion_rate; transactions_per_buyer;
units_per_transaction; qualified_traffic + conversion_rate + repeat_transactions;
starting_subscribers + new_subscribers + churned_subscribers + units_per_subscriber;
available_inventory + occupancy + billing_units_per_inventory;
category_monthly_units + market_share. A seasonality role is optional ONLY when
normal-month inputs need a justified seasonal adjustment. It is forbidden when
frequency/traffic/category units already represent an annual-average month.
All transactions and frequency values are monthly; count snapshots are explicitly
marked snapshot. Fractions use units=fraction and lie in [0,1]. Buyer group,
denominator and reference period must be explicit.
For input units, use the schema's literal labels: count roles=buyer_base;
transactions_per_buyer=transactions/buyer/month; units_per_transaction=output_units/transaction;
qualified_traffic=website_users/month; repeat_transactions=transactions/month;
starting_subscribers=subscribers; new/churned_subscribers=subscribers/month;
units_per_subscriber=output_units/subscriber/month; available_inventory=inventory_units;
billing_units_per_inventory=output_units/inventory/month; category_monthly_units=output_units/month.
These labels are dimensional: output_units always denotes the accepted sold unit.
An already computed active_buyers count may be included alongside its exact
reachable_prospects * conversion_rate derivation, but it is an INTERMEDIATE
result, never an extra multiplier. The two definitions must agree exactly.
Monthly active buyers are already
business customers with at least one transaction that month. Their monthly
transactions_per_buyer must be >=1; express infrequent purchasing through a defined
reachable-prospect pool and monthly conversion probability. Never apply household
participation, penetration or market share again. Households are allowed only with
a clear household purchasing rationale.
For individually purchased food/drinks, use people or visitors unless there is a
reasoned family-basket or household purchasing model. Having household census data
does not make households the correct buyer unit. Missing observed buyer counts do
not justify defaulting to households; label the appropriate reachable buyer pool
as a scenario and review acquisition/frequency for that actual customer group.
Do not confuse total population, prospects, active customers, transactions and units.

Evidence priority: actual business records; supplied verified local/industry data;
relevant supplied comparables; explicitly reasoned scenarios. For EVERY material
input supply value, units, reference_period, source_kind, source, evidence_path,
confidence and reasoning. Only classify an input as non-scenario if its numeric value
is directly traceable to an actual path in supplied evidence. All inferred or derived
quantities are scenario_assumption unless the supplied record contains that exact
numeric quantity. LLM numbers are hypotheses, not verified facts. No web research or
external benchmarks have been fetched for this call. Say so in limitations. Never
fabricate citations or claim to have searched. Use provided evidence where relevant.

Separate category demand, accessible market and obtainable business demand. Where
possible provide category_demand and an independent_cross_check using its own inputs
and equation. Otherwise use null and explain missing evidence. Reconcile material
disagreement explicitly; never average incompatible estimates to manufacture a point.
Build coherent conservative/base/optimistic scenarios; downside must not be a chain
of arbitrary pessimistic guesses. Base is the most defensible central estimate,
optimistic is feasible. Explain uncertainty drivers. With inadequate evidence keep
provisional=true, supply a broad scenario range and missing_data; still return a
usable, clearly labelled base planning value so report generation continues.

Use effective_monthly_capacity from the EXISTING physical conversion, unchanged.
For EACH scenario: realized_monthly_units=min(monthly_demand_units, effective capacity),
daily_unit_sales=realized_monthly_units/working_days_per_month,
monthly_revenue_inr=realized_monthly_units*accepted average selling price,
capacity_utilization_pct=realized_monthly_units/effective capacity*100.
monthly_active_buyers and monthly_transactions are the implied pre-capacity demand
metrics, not extra multipliers; null if the chosen method cannot derive them.
Inspect transactions, buyers, basket size, daily volume, revenue, effective capacity
utilization, acquisition effort, competitors and stage together in reality_review.
Negligible sales from a sizable catchment, infrequent recurring-product purchases,
large conversion rates and extreme utilization require explicit re-examination of
definitions, units, evidence, double-counting and missing channels. Record warnings;
never automatically lift or suppress sales, change price or costs, or target DSCR.
On a BUSINESS REALITY RE-EXAMINATION request, explicitly reconsider the flagged
drivers, set reality_reexamined=true, record the unresolved concerns in warnings,
and explain in reality_review why you revised or retained the scenario inputs.

Return demand_forecast with classification, chosen method, explicit equation with
units, per-scenario assumption tables, three demand/realized-sales scenarios, effective
capacity, transactions, daily sales, revenue, utilization, warnings, limitations,
missing data and why this model fits. Keep other production/pricing/cost inputs
unchanged. For estimated sales, feed ONLY the base scenario realized_monthly_units
into calculations.monthly_sales_units. The existing annual report multiplies this
monthly quantity by 12, so this report's period MUST be annual_average_month.
Never annualize a peak forecast month or normal active-season month. Estimate the
annual-average buyer/frequency drivers explicitly for seasonal enterprises.
monthly_local_demand_units holds BASE obtainable
business demand (legacy API field name); set external_monthly_demand_units=0 because
all channels are already included in demand_forecast. Do not add demand twice.
Legacy household/market-share fields are compatibility metadata, NOT demand drivers.
An explicit user annual sales override stays immutable; disclose it as an override
and retain the independent demand forecast for comparison, not a replacement.
Keep internal arithmetic precise but explain that uncertainty makes the point
provisional; present scenario ranges rather than a spurious precise forecast.
"""


def _check(actual: float | None, expected: float | None, name: str) -> None:
    if actual is None or expected is None:
        if actual != expected:
            raise ValueError(f"{name} must be null when it cannot be derived from this method")
    elif not math.isclose(actual, expected, rel_tol=1e-5, abs_tol=.02):
        raise ValueError(f"{name} must equal {expected} from the stated input definitions")


def _source_value(path: str | None, evidence: dict) -> Any:
    if not path or not path.startswith("evidence."):
        raise ValueError("Non-scenario inputs need a numeric evidence.* path from the supplied payload")
    value: Any = evidence
    for part in path.split(".")[1:]:
        if not isinstance(value, dict) or part not in value:
            raise ValueError("Input cites an evidence path that was not supplied")
        value = value[part]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Evidence paths must identify the numeric quantity, not an unverified citation")
    return value


def demand_metrics(method: str, inputs: list[DemandInput], buyer_base: str, period: str,
                   evidence: dict, output_unit: str | None = None) -> tuple[float, float | None, float | None]:
    """Validate named roles and their units, then check the selected equation."""
    roles = {item.role: item for item in inputs}
    if len(roles) != len(inputs):
        raise ValueError("Each semantic demand role occurs once; do not duplicate reductions")
    for item in inputs:
        unit = item.units.strip().lower().replace(" per ", "/").replace(" ", "")
        if output_unit:
            # Check equivalent unit labels only. No quantities, time periods or
            # physical units are scaled or inferred by this validator.
            if unit.startswith(output_unit + "/"):
                unit = "output_units/" + unit[len(output_unit)+1:]
        if item.role == "transactions_per_buyer":
            for event in ("purchases", "orders", "visits", "bookings"):
                unit = unit.replace(event + "/", "transactions/")
            for buyer in ("customer", "customers", "buyers", buyer_base):
                unit = unit.replace("/" + buyer + "/", "/buyer/")
        if item.role == "units_per_transaction":
            for event in ("purchase", "order", "visit", "booking"):
                if unit.endswith("/" + event):
                    unit = unit[:-len(event)] + "transaction"
        for url in re.findall(r"https?://[^\s<>]+", item.source):
            if url.rstrip(".,);]\"'") not in json.dumps(evidence, ensure_ascii=False):
                raise ValueError("Do not invent a benchmark citation or external research source absent from supplied evidence")
        if item.source_kind != "scenario_assumption":
            path = item.evidence_path or ""
            demographic = path == "evidence.households" or path.startswith(("evidence.census.", "evidence.population_projection."))
            if demographic and (item.role != "reachable_prospects" or buyer_base not in {"people", "households"}):
                raise ValueError("Demographic counts cannot be cited as observed business buyers, transactions, traffic or product demand")
            _check(item.value, _source_value(item.evidence_path, evidence), item.role + " evidence value")
        elif item.confidence == "high":
            raise ValueError("Unsupported scenario hypotheses cannot be presented as high-confidence evidence")
        expected_units = {"active_buyers": buyer_base, "reachable_prospects": buyer_base,
            "qualified_traffic": "website_users/month", "repeat_transactions": "transactions/month",
            "starting_subscribers": "subscribers", "new_subscribers": "subscribers/month",
            "churned_subscribers": "subscribers/month", "units_per_subscriber": "output_units/subscriber/month",
            "available_inventory": "inventory_units", "billing_units_per_inventory": "output_units/inventory/month",
            "category_monthly_units": "output_units/month"}
        allowed_units = {expected_units[item.role]} if item.role in expected_units else set()
        if item.role in {"active_buyers", "reachable_prospects"}:
            allowed_units |= {buyer_base + "/month", "buyers", "customers", "buyers/month", "customers/month"}
        if item.role in expected_units and unit not in allowed_units:
            raise ValueError(f"{item.role} uses {item.units!r}; expected {expected_units[item.role]} units for this buyer definition")
        if item.role in {"conversion_rate", "occupancy", "market_share"}:
            if item.value > 1 or unit != "fraction":
                raise ValueError("Conversion, occupancy and share must be fractions with units=fraction")
        if item.role in {"transactions_per_buyer", "qualified_traffic", "repeat_transactions", "new_subscribers",
                         "churned_subscribers", "units_per_subscriber", "billing_units_per_inventory", "category_monthly_units"}:
            if "month" not in unit or item.reference_period == "snapshot":
                raise ValueError(item.role + " must use explicit monthly units and a monthly reference period")
        if item.role == "units_per_transaction" and unit != "output_units/transaction":
            raise ValueError(f"Basket size units {item.units!r} must be output_units/transaction (or the exact accepted sold unit per transaction)")
        if item.role == "transactions_per_buyer" and unit != "transactions/buyer/month":
            raise ValueError("Purchase frequency must be transactions/buyer/month for that buyer definition")
    def v(role):
        if role not in roles:
            raise ValueError("Missing required demand input role: " + role)
        return roles[role].value
    buyers = transactions = None
    if method in {"customer_purchases", "service_bookings", "b2b_orders", "manufacturing_orders", "other"}:
        if method in {"b2b_orders", "manufacturing_orders"} and buyer_base not in {"organizations", "contracts"}:
            raise ValueError("B2B/wholesale orders need organizations or contracts, not household penetration")
        capture = {"active_buyers"} if "active_buyers" in roles else {"reachable_prospects", "conversion_rate"}
        if {"active_buyers", "reachable_prospects", "conversion_rate"} <= set(roles):
            _check(v("active_buyers"), v("reachable_prospects") * v("conversion_rate"), "active_buyers derivation")
            capture = {"active_buyers", "reachable_prospects", "conversion_rate"}
        allowed = capture | {"transactions_per_buyer", "units_per_transaction", "seasonality"}
        buyers = v("active_buyers") if "active_buyers" in roles else v("reachable_prospects") * v("conversion_rate")
        if v("transactions_per_buyer") < 1:
            raise ValueError("Monthly active buyers must transact at least once; model infrequent demand through a reachable pool and monthly conversion probability")
        transactions = buyers * v("transactions_per_buyer")
        demand = transactions * v("units_per_transaction")
    elif method == "ecommerce":
        if buyer_base != "website_users":
            raise ValueError("E-commerce traffic uses website_users as the buyer base")
        allowed = {"qualified_traffic", "conversion_rate", "repeat_transactions", "units_per_transaction", "seasonality"}
        transactions = v("qualified_traffic") * v("conversion_rate") + v("repeat_transactions")
        demand = transactions * v("units_per_transaction")
    elif method == "subscription":
        if buyer_base != "subscribers":
            raise ValueError("Subscription demand uses subscribers")
        allowed = {"starting_subscribers", "new_subscribers", "churned_subscribers", "units_per_subscriber"}
        buyers = v("starting_subscribers") + v("new_subscribers") - v("churned_subscribers")
        if buyers < 0:
            raise ValueError("Churn cannot exceed starting plus new subscribers")
        transactions = buyers
        demand = buyers * v("units_per_subscriber")
    elif method == "occupancy":
        if buyer_base != "inventory_units":
            raise ValueError("Occupancy uses available inventory, not households")
        allowed = {"available_inventory", "occupancy", "billing_units_per_inventory", "seasonality"}
        demand = v("available_inventory") * v("occupancy") * v("billing_units_per_inventory")
    elif method == "market_share":
        allowed = {"category_monthly_units", "market_share", "seasonality"}
        demand = v("category_monthly_units") * v("market_share")
    else:
        raise ValueError("Unsupported demand method")
    if set(roles) - allowed:
        raise ValueError("Overlapping or irrelevant multipliers for this method: " + ", ".join(sorted(set(roles)-allowed)))
    if "seasonality" in roles:
        rate_inputs = [item for item in inputs if item.role not in {"seasonality", "active_buyers", "reachable_prospects", "conversion_rate", "market_share", "units_per_transaction"}]
        if period == "annual_average_month" or any(item.reference_period == "annual_average_month" for item in rate_inputs):
            raise ValueError("Do not apply seasonality again to annual-average monthly behaviour")
        if roles["seasonality"].units != "factor":
            raise ValueError("Seasonality needs units=factor and an explicit normal-month baseline")
        demand *= v("seasonality")
        if transactions is not None:
            transactions *= v("seasonality")
    return demand, buyers, transactions


def validate_forecast(forecast: DemandForecast, values, conversion, monthly_capacity: float,
                      context: dict) -> list[str]:
    if forecast.output_unit != values.output_unit:
        raise ValueError("Demand, production and pricing must use the SAME defined output unit")
    _check(forecast.effective_monthly_capacity, monthly_capacity, "effective_monthly_capacity")
    if forecast.period == "forecast_month" and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", forecast.forecast_month or ""):
        raise ValueError("Forecast-month seasonality needs an explicit YYYY-MM forecast month")
    uncertain = False
    volumes = []
    base_roles = {i.role for i in forecast.scenarios.base.inputs}
    for name in ("conservative", "base", "optimistic"):
        scenario = getattr(forecast.scenarios, name)
        if {i.role for i in scenario.inputs} != base_roles:
            raise ValueError("Scenarios must use a coherent common set of business drivers")
        demand, buyers, transactions = demand_metrics(forecast.method, scenario.inputs, forecast.buyer_base, forecast.period, context, forecast.output_unit)
        _check(scenario.monthly_demand_units, demand, name + " monthly_demand_units")
        _check(scenario.monthly_active_buyers, buyers, name + " monthly_active_buyers")
        _check(scenario.monthly_transactions, transactions, name + " monthly_transactions")
        sold = min(demand, monthly_capacity)
        for field, expected in (("realized_monthly_units", sold), ("daily_unit_sales", sold/conversion.working_days_per_month),
                                ("monthly_revenue_inr", sold*values.selling_price_inr),
                                ("capacity_utilization_pct", sold/monthly_capacity*100)):
            _check(getattr(scenario, field), expected, name + " " + field)
        uncertain |= any(i.source_kind == "scenario_assumption" or i.confidence == "low" for i in scenario.inputs)
        volumes.append(demand)
    if volumes != sorted(volumes):
        raise ValueError("Scenario demand must be ordered conservative <= base <= optimistic")
    if uncertain and not forecast.provisional:
        raise ValueError("Forecasts controlled by scenario/low-confidence inputs must be provisional")
    if uncertain and volumes[0] == volumes[2]:
        raise ValueError("Uncertain drivers need a genuine scenario range, not three identical point estimates")
    for independent in (forecast.category_demand, forecast.independent_cross_check):
        if independent:
            expected, _, _ = demand_metrics(independent.method, independent.inputs, independent.buyer_base, forecast.period, context, forecast.output_unit)
            _check(independent.monthly_demand_units, expected, "independent estimate")
    if forecast.category_demand and volumes[1] > forecast.category_demand.monthly_demand_units + .02:
        raise ValueError("Obtainable business demand cannot exceed the stated total category demand in the same units/period")
    if forecast.independent_cross_check:
        cross = forecast.independent_cross_check.monthly_demand_units
        if max(cross, volumes[1]) > max(min(cross, volumes[1]), 1e-9) * 2 and len(forecast.reconciliation) < 80:
            raise ValueError("Material top-down/bottom-up disagreement needs an explicit explanation of the conflicting inputs and chosen basis")
    return reality_flags(forecast, conversion.working_days_per_month, context)


def reality_flags(forecast: DemandForecast, days: float, context: dict) -> list[str]:
    """Review triggers, never floors that manufacture sales or profitability."""
    base = forecast.scenarios.base
    flags = []
    if forecast.buyer_base == "households" and not any(i.source_kind == "actual_records" for i in base.inputs):
        flags.append("Households are an assumed buyer group: re-examine whether purchases are household decisions or individual visits; census households alone do not establish buying behaviour.")
    sizeable = float(context.get("households") or 0) >= 200 or float((context.get("population_projection") or {}).get("projected_population") or 0) >= 1000
    if sizeable and forecast.method == "customer_purchases" and base.realized_monthly_units < days:
        flags.append("Fewer than one sold unit per operating day despite a sizeable catchment: review buyer definition, frequency, basket size and missing channels.")
    if base.capacity_utilization_pct < 1:
        flags.append("Demand uses less than 1% of effective capacity: review scale and acquisition assumptions; low sales may still be valid.")
    if base.capacity_utilization_pct >= 99 and any(i.source_kind == "scenario_assumption" for i in base.inputs):
        flags.append("The base scenario fills nearly all effective capacity using estimated demand: review acquisition, distribution and operational bottlenecks.")
    for item in base.inputs:
        if item.role == "conversion_rate" and item.value > .5 and item.source_kind == "scenario_assumption":
            flags.append("More than half of reachable prospects are assumed to convert: verify qualification and acquisition evidence.")
    return flags


def forecast_payload(forecast: DemandForecast, flags: list[str], reviewed: bool, model: str | None = None) -> dict:
    result = forecast.model_dump()
    result["warnings"] = list(dict.fromkeys(result["warnings"] + flags))
    result["review_status"] = "review_required" if forecast.source_review_required else "reexamined" if flags and reviewed else "review_required" if flags else "checks_passed"
    result["source"] = "llm_business_demand_scenarios"
    result["model"] = model
    result["research_status"] = "supplied_evidence_only"
    result["limitations"] = list(dict.fromkeys(result["limitations"] + ["No independent external market research was performed for this forecast; inferred inputs are scenario hypotheses."]))
    return result


def reconcile_forecast(forecast: DemandForecast, values, conversion, monthly_capacity: float,
                       context: dict) -> DemandForecast:
    """Only after invalid model arithmetic; retain structured driver hypotheses."""
    result = forecast.model_copy(deep=True)
    # Failed evidence claims retain their numerical hypotheses, never verified
    # status. Semantic/unit errors remain invalid and cannot pass this fallback.
    for estimate in [getattr(result.scenarios, n) for n in ("conservative", "base", "optimistic")] + [i for i in (result.category_demand, result.independent_cross_check) if i]:
        for item in estimate.inputs:
            try:
                if any(url.rstrip(".,);]\"'") not in json.dumps(context, ensure_ascii=False) for url in re.findall(r"https?://[^\s<>]+", item.source)):
                    raise ValueError("citation not supplied")
                if item.source_kind != "scenario_assumption":
                    demographic = (item.evidence_path or "") == "evidence.households" or (item.evidence_path or "").startswith(("evidence.census.", "evidence.population_projection."))
                    if demographic and (item.role != "reachable_prospects" or result.buyer_base not in {"people", "households"}):
                        raise ValueError("demographic count is not observed business demand")
                    _check(item.value, _source_value(item.evidence_path, context), item.role + " evidence value")
                elif item.confidence == "high":
                    raise ValueError("unsupported high confidence")
            except ValueError:
                item.source_kind, item.confidence, item.evidence_path = "scenario_assumption", "low", None
                item.source = "Unverified LLM planning hypothesis; matching business evidence was not supplied"
                item.reasoning = ("Source could not be verified; retain only as a scenario requiring local validation. " + re.sub(r"https?://\S+", "[unverified citation removed]", item.reasoning))[:700]
                result.provisional = result.source_review_required = True
                warning = "Unverified source claim for " + item.role + ": its value is retained only as a low-confidence scenario hypothesis, not a verified fact."
                if warning not in result.warnings:
                    result.warnings.append(warning)
    result.effective_monthly_capacity = monthly_capacity
    for name in ("conservative", "base", "optimistic"):
        scenario = getattr(result.scenarios, name)
        demand, buyers, transactions = demand_metrics(result.method, scenario.inputs, result.buyer_base, result.period, context, result.output_unit)
        scenario.monthly_demand_units = demand
        scenario.monthly_active_buyers, scenario.monthly_transactions = buyers, transactions
        sold = min(demand, monthly_capacity)
        scenario.realized_monthly_units = sold
        scenario.daily_unit_sales = sold/conversion.working_days_per_month
        scenario.monthly_revenue_inr = sold*values.selling_price_inr
        scenario.capacity_utilization_pct = sold/monthly_capacity*100
    validate_forecast(result, values, conversion, monthly_capacity, context)
    return result


def recover_forecast(context: dict, values, conversion, monthly_capacity: float,
                     previous: DemandForecast | None, error: str, llm_call):
    """Bounded demand-only recovery, with one correction, on frozen economics.

    Never re-request the recipe, prices, machine interpretation, expenses or loan.
    A provider can repair this smaller contract without changing other figures.
    """
    evidence = {key: value for key, value in context.items() if key not in
        {"project_cost", "gross_project_cost", "promoter_equity", "annual_sales_override", "expected_monthly_units", "machinery_profile"}}
    messages = [{"role": "system", "content": DEMAND_PROMPT +
        "\nThis focused recovery returns ONLY the DemandForecast JSON, no outer operating-plan objects. "
        "Accepted price, output unit, physical capacity and operating days are immutable. Re-examine the failed demand definitions/units and explicit warnings. Do not infer buyers from capacity or financing. Set reality_reexamined=true after reviewing the given issue."},
        {"role": "user", "content": json.dumps({"evidence": evidence,
            "accepted_facts": {"product": values.product, "output_unit": values.output_unit,
                "selling_price_inr": values.selling_price_inr, "effective_monthly_capacity": monthly_capacity,
                "working_days_per_month": conversion.working_days_per_month,
                "saleable_unit_definition": conversion.saleable_unit_definition},
            "previous_demand_forecast": previous.model_dump() if previous else None, "validation_issue": error}, ensure_ascii=False)}]
    for attempt in range(2):
        parsed = None
        try:
            content, tool, model = llm_call(messages=messages,
                response_format=structured_response_format(DemandForecast, "business_demand"),
                calculation_mode=True, temperature=.1, max_tokens=5000, timeout_s=24)
            parsed = response_object(content, tool, "submit_demand_forecast")
            candidate = DemandForecast.model_validate(parsed)
            if candidate.period != "annual_average_month":
                raise ValueError("Demand recovery must return an annual-average monthly estimate")
            # This outer path is already a labelled arithmetic fallback. Retain
            # hypotheses, reconcile their equations and make uncertainty explicit.
            candidate = reconcile_forecast(candidate, values, conversion, monthly_capacity, evidence)
            flags = validate_forecast(candidate, values, conversion, monthly_capacity, evidence)
            if flags and attempt == 0:
                raise ValueError("BUSINESS REALITY RE-EXAMINATION REQUIRED: " + " ".join(flags) +
                    " Explain a defensible buyer definition and review the scenario drivers, without targeting higher sales.")
            reviewed = candidate.reality_reexamined and bool(candidate.warnings)
            return candidate, flags, reviewed, model
        except Exception as exc:
            reason = [".".join(map(str, item["loc"])) for item in exc.errors(include_input=False)] if hasattr(exc, "errors") else str(exc)
            logger.warning("Business demand recovery validation (%s)", reason)
            if attempt == 0 and parsed is not None:
                messages.extend([{"role":"assistant", "content":json.dumps(parsed, ensure_ascii=False)},
                    {"role":"user", "content":"Correct the entire DemandForecast JSON after this exact validation error: " + str(reason) +
                     ". Re-examine the buyer definition and units; people and households are different and cannot be blindly relabelled. Keep accepted price, sold unit, operating days and capacity unchanged. Correct incompatible definitions and arithmetic without targeting a preferred sales level. Use scenario_assumption for unsupported numeric inputs and return explicit warnings."}])
                continue
            break
    return None, [], False, None
