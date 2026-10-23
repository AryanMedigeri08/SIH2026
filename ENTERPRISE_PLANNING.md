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


Validation:

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

```text
python -m pytest tests/test_machinery_variants.py -q
python -m pytest tests/test_enterprise_assumptions.py tests/test_enterprise_report_flow.py tests/test_llm_calculation_modes.py tests/test_planning_llm_transport.py tests/test_onboarding_sequence.py tests/test_odop_chat_flow.py -q
python scripts/smoke_enterprise_planning.py --live --details
python scripts/smoke_enterprise_planning.py --live --sizing-only
cd frontend
node --test tests/financialsRender.test.js tests/planningAssumptionsRender.test.js tests/machineryCapacityRender.test.js
npm run build
```

The live smoke check uses synthetic business and village inputs and does not log
credentials. Provider failures are surfaced by that check while production report
generation continues through the labelled fallback.
