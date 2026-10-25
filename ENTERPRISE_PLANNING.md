# Enterprise interpretation and optimistic planning

The onboarding idea is sent to the existing Sarvam/Groq chat provider before the
business category and equipment are selected. The full local machinery catalogue
is supplied for semantic retrieval. Catalogue equipment retains its recorded cost
and quantity. Equipment gaps may be proposed as `llm_estimate`; these are planning
estimates, not supplier quotes. This implementation does not perform live vendor
web searches. Retail and services may need supporting equipment without needing
a manufacturing plant.

Reports gather the original idea, machinery, Census population projection,
households, amenities and their provenance, state CPI and competition before asking
for operating assumptions. LLM output is validated in Python; incomplete, invalid
or non-finite values fall back to labelled optimistic indicative values. Missing
prices or a failed LLM call do not suppress sales or stop report creation. This
does not mask unrelated failures such as invalid loan tenures or storage errors.

The deterministic initial capacity parser in `capacity_units.py` is temporarily
commented out. `parse_monthly_capacity` is now a compatibility adapter to the LLM.
The model receives the original capacity string unchanged and interprets input
throughput, output, storage or batch capacity. It performs all associated mass,
volume, time-period, yield, price and quantity conversions. No regex parser or
Python unit scaler runs on the normal path. If the model fails, a labelled
indicative monthly volume is used without parsing the source text.

The operating response contains assumptions, the interpreted capacity and final
calculated production, demand, sales, cost and cashflow values. Python validates
schema, finite numbers, consistent unit labels, explicit user sales and arithmetic
relationships; it uses
accepted model results directly without recalculating them. User-supplied annual
sales, including zero, remain immutable. Auto-estimates are recalculated by the
LLM with local evidence for the final report. No solvency floor increases sales.

A second LLM calculation response supplies EMI, capitalized moratorium interest,
working capital, five-year projections, DSCR, profit, ROI, pricing, break-even and
payback. Financing inputs and accepted operating sales cannot be changed by this
step. Shared dashboard/DPR fields must agree. One bounded LLM correction is allowed
for an incomplete or inconsistent response in the operating and financial stages. If that still fails, existing legacy
calculators provide a labelled non-blocking fallback. Demographic projection,
source-dataset retrieval and government-scheme eligibility/rules remain upstream.

Calculation requests first use the already configured Groq reasoning model
(`GROQ_LLM_MODEL`, with `GROQ_API_KEY_LLM` preferred), then the existing Sarvam/chat
provider fallback. Conversation requests keep their existing provider order. Both
Sarvam and Groq receive a JSON-schema response format. Nested definitions are
inlined and validated locally. Provider JSON fences and function-call responses
are supported. The primary path does not execute model-generated code. Schema
validation alone does not establish the factual or arithmetic correctness of model
estimates. See the [Sarvam structured output documentation](https://docs.sarvam.ai/api-reference/chat/chat-completions-v1).

Reports retain the original evidence, interpreted units, conversion basis,
assumptions, operating calculation source and financial calculation source/model.
The dashboard exposes the conversion basis and whether calculations came from the
LLM or the indicative fallback. No-debt cases retain `NO DEBT` with zero debt
service. Negative profits and poor coverage remain visible.

## Business-specific LLM demand estimates

The current LLM operating response now requires `demand_forecast`. Its forecasting
instructions replace the universal household × penetration × frequency × share ×
seasonality equation for new model responses. Classification selects customer
purchases, services/bookings, B2B orders, manufacturing/wholesale, e-commerce,
subscriptions, occupancy, a justified category-volume share model, or a simple
custom customer/transaction model. Household counts are context, not a universal
buyer base. Manufacturing sold directly to consumers can use B2C customer demand;
manufacturing/wholesale orders use reachable organizations/contracts.

Each conservative/base/optimistic scenario supplies named, nonoverlapping input
roles with values, units, monthly periods, sources, confidence and reasoning.
Non-scenario claims need a matching numeric path in supplied evidence; model
hypotheses cannot silently become verified records. No external research is
performed in this request. Category/independent estimates are optional when no
independent evidence exists, with explicit reconciliation and limitations.
After a failed model response, unsupported evidence claims may retain their
numbers only as low-confidence scenario hypotheses with source warnings and
`review_required`; fabricated citations are removed. They never retain verified
status. Unit-label equivalence (for example cups/transaction when output_unit is
cups) is checked without parsing physical capacity or scaling any numbers.

The validator rejects additional conversion/share after active buyers are already
captured, household bases for B2B orders, incompatible units/periods and seasonal
reductions on annual-average monthly behaviour. Monthly active buyers have at
least one transaction; infrequent category purchasing belongs in an explicit
prospect-to-active-buyer step. Scenario outputs include implied buyers,
transactions, daily units, realized sales, revenue and effective capacity usage.
An uncertain forecast needs an actual range and remains provisional. Extremely
low daily sales, near-zero/full effective capacity usage and large assumed
conversion rates request one explicit reality re-examination. No numeric floor
or DSCR target manufactures sales. Unresolved concerns remain visible.

Only the base scenario's capacity-constrained sales feed the existing monthly
volume. The report requires an annual-average month because its existing annual
sales formula multiplies by 12. It cannot annualize an unadjusted peak month.
Explicit user sales, including zero, remain immutable; scenarios are then a
separate comparison. Existing price mixes, recipes, unit conversions, costs,
funding and financial formulas are unchanged. Once conversion/pricing pass
validation, demand repairs cannot change those accepted inputs. A replay with
identical base sales must retain identical finances.

Validated demand assumptions/scenarios survive an invalid arithmetic response
through the labelled calculation fallback. If the provider supplies no usable
model after physically valid units/pricing are accepted, one focused demand-only
recovery (at most one correction) can repair its smaller contract while those
facts remain immutable. Unavailable providers do not trigger an unbounded retry.
If that also fails, no new demand response is presented as validated. If no usable
business model is available, the pre-existing indicative fallback still keeps reports
available and is labelled as needing demand review. Historical reports and legacy
offline calculations do not need the new schema. The dashboard and both DPR
formats show the classification, equation, scenario range, assumption tables,
warnings, missing data and reality review. No stored reports are rewritten.


Validation:

Average-price experiment (uncommitted for review): `selling_price_inr` now means
quantity-weighted average realized selling price for the defined output unit.
The operating response requires `pricing.sales_mix` with sold-quantity shares,
quoted price, output units per quoted pack/billing quantity, discount percentage
and net realized price per output unit. Shares must sum to one; the model's ASP
must match the weighted net prices. A uniform-price enterprise can use one row.
No generic retail/wholesale split is fabricated when the model is unavailable.

All monthly/annual sales, cashflows, pricing simulation and DSCR consume this ASP.
Discounts are included once, before averaging; pack prices are normalized before
weighting. Prices for incompatible units/products cannot be averaged without a
common saleable-unit/basket conversion and matching cost basis. The fallback may
repair arithmetic using valid model quote/share assumptions while retaining the
validated production conversion. Invalid shares/units produce a labelled uniform
price fallback rather than silently normalizing or inventing a sales mix.

The dashboard displays the mix, discounts, net prices and a same-volume comparison
against an explicitly estimated regular undiscounted price. This is a reference
scenario, not a historical before/after claim. Explicit user annual sales stay
unchanged and have no price-only comparison. The price simulator holds monthly
units fixed as its slider changes, so price changes affect revenue and profit.
The DPR records average realized price and the supporting mix. Old saved reports
remain unchanged; regenerate a report to use the experiment.

Controlled example: 1,000 identical cups/month, 60% at ₹30 and 40% at ₹20 net of
pack discounts, gives ASP ₹26. Annual revenue changes from ₹360,000 at the ₹30
reference price to ₹312,000 at ASP, a ₹48,000 (13.33%) reduction at the same volume.
These are illustrative inputs, not researched market prices or a recalculated
saved business report. This change does not fix the separate project-outlay issue.

A live synthetic ice-cream check on 24 October 2026 validated after one model
correction: 60% retail at ₹30 and 40% wholesale at ₹25 gave ASP ₹28 per 100 ml cup.
At the model's same 740 cups/month, the reference-price scenario was ₹266,400/year
and weighted revenue ₹248,640/year, a ₹17,760 (6.67%) reduction. These are provider
estimates for synthetic inputs, not observed prices or an update to saved reports.

Every operating LLM response now requires a `conversion` contract. It defines the
actual enterprise model, capacity basis (raw input, finished output, retail supply,
service hours/jobs or stored stock), one explicit sold unit and portion size,
capacity consumed per sold unit, working schedule, billing period, storage cycles
and annual-average seasonality factor. The model supplies the numeric conversion
and final monthly production, monthly sold quantity and monthly gross sales.
Generic fallback sector prices and 1:1 recipe seeds are no longer sent to the model.

The authoritative revenue quantity is `monthly_sales_units`, constrained by the
converted saleable capacity and reachable average demand. `monthly_gross_sales`
must equal this quantity times the price for the same defined sold unit, and
annual sales must equal monthly gross sales times twelve. Validation checks the
model's schedule, portions, recipe consistency, seasonal demand and arithmetic;
it does not restore the disabled parser or invent a replacement conversion. A
bounded repair asks the LLM to fix errors. When only operating arithmetic fails,
the fallback preserves the validated conversion and uses the same unit definition
and seasonal factor. Complete provider/schema failure retains the labelled
indicative fallback so report generation stays available.

The dashboard shows the sold-unit definition, monthly production capacity, monthly
gross sales and the conversion basis. This improves dimensional consistency; an
LLM-estimated recipe, serving size or price still needs business/supplier validation.
This change does not reconcile the separate equity-derived project outlay with
selected equipment cost or change the financing/moratorium conventions.

Machinery sizing: all 37 profiles now contain five explicit capacity variants
(starter, small, medium, reference and expanded), with the original reference
equipment records retained. `scripts/populate_machinery_variants.py` authors these
185 options offline from explicit numeric reference capacities; it does not
restore the runtime capacity parser. New prices are indicative estimates using
25% fixed cost plus 75% scaled by capacity ratio to the power 0.65, rounded to
₹100. Instruments retain their price, identical indivisible machines use whole
quantities, and multiple tanks/pasteurizers/RO units allow smaller vessel sizes.
Derived configurations do not claim the original motor power or specifications.

At the investment turn, the sizing LLM receives all relevant capacity options,
product-specific equipment, Census catchment and projected households, amenities,
district MSME data, CPI, promoter equity and derived/explicit total project outlay.
An indicative 30% of outlay is reserved for other project costs. The model estimates
product demand, yield, working schedule and headroom in the reference unit/period,
then chooses the smallest affordable option covering that requirement. Unnecessary
oversizing, unknown IDs, inconsistent demand/yield/schedule/headroom arithmetic
and unaffordable selections are rejected, with one bounded LLM correction.
Provider failure
uses a labelled starter estimate; a funding gap is shown when even that option
exceeds the equipment budget. This does not guarantee supplier availability.

Onboarding displays capacity, equipment cost, rationale, alternative sizes, pricing
basis and any funding gap. The selected ID and context persist in `machinery_plan`;
catalogue prices are reconstructed server-side when confirming owned equipment
and generating reports. Reports use the selected capacity rather than the original
plant size. Legacy/direct report requests get sizing after local evidence is loaded.
Investment/location changes before equipment confirmation trigger new sizing.
Reports also refresh sizing when the stored idea, location or gross budget changes.
Equipment cost is a component of project outlay, not a replacement for total outlay.

Actual investment no longer comes from an equity/margin multiple. That older
function remains only an affordability hint for choosing a machinery size.
Onboarding uses labelled preliminary startup allowances; the report then requests
an itemized LLM budget using selected equipment, local evidence and accepted
operations. Installation, premises, utility connections, launch costs, initial
working capital and contingency are added to equipment. Owned assets are credited
once at selected equipment prices (legacy aggregate credit is capped at equipment
value). Promoter cash affects funding, not the underlying cost of the project.

The budget separately estimates wages, rent, fixed utilities, maintenance,
distribution and administration with a basis for every amount, including zeros.
Per-unit expenses stay in the accepted operating model. Working capital is included
once as startup liquidity and never added again to recurring expenses. Budget
arithmetic gets one LLM repair. If structured cost estimates are usable but totals
still fail, retain those AI estimates and reconcile their totals with an explicit
source label. If cost estimates are unavailable, use explicit indicative
allowances so reports remain available. Output volume and average selling price
remain unchanged when expense/funding estimates change.

Base borrowing equals fresh outlay less available promoter cash. Potential scheme
subsidy remains a recommendation and is excluded from upfront funding until
confirmed; no missing cash contribution is silently invented. Any planning-margin
shortfall is disclosed. The budget and funding reconciliation are shared by the
dashboard and both DPR exports. Depreciation uses selected equipment, including
owned equipment, rather than 55% of net fresh outlay.

Year-one DSCR uses actual scheduled repayments. The first year with 12 repayments
is shown separately to expose moratorium effects; operating months are independent
of loan moratorium. An entire no-repayment year is labelled Moratorium, not a zero
coverage failure. Validate yearly interest/principal splits, expense and profit
arithmetic, DSCR verdicts and the average across serviced years. Negative coverage
is preserved; a valid calculation is not a promise of viability.

```text
python -m pytest tests/test_machinery_variants.py -q
python -m pytest tests/test_production_conversion.py -q
python -m pytest tests/test_average_selling_price.py -q
python -m pytest tests/test_business_demand.py -q
python -m pytest tests/test_project_budget.py -q
python -m pytest tests/test_enterprise_assumptions.py tests/test_enterprise_report_flow.py tests/test_llm_calculation_modes.py tests/test_planning_llm_transport.py tests/test_onboarding_sequence.py tests/test_odop_chat_flow.py -q
python scripts/smoke_enterprise_planning.py --live --details
python scripts/smoke_enterprise_planning.py --live --sizing-only
python scripts/smoke_enterprise_planning.py --live --operations-only --idea "Ice cream in 100 ml cups"
python scripts/smoke_business_demand.py --live
python scripts/recheck_feasibility.py REPORT_ID --live
cd frontend
node --test tests/financialsRender.test.js tests/planningAssumptionsRender.test.js tests/machineryCapacityRender.test.js
npm run build
```

The live smoke check uses synthetic business and village inputs and does not log
credentials. Provider failures are surfaced by that check while production report
generation continues through the labelled fallback.
