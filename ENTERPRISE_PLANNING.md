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

The model supplies product-specific price, input requirements, variable and fixed
costs, utilization, processing loss and achievable demand. It cannot overwrite a
normalized catalogue throughput. Stock capacity and batches need estimated
turnover/frequency. Unit changes are accepted with their related prices, costs,
yields and demand quantities together. Tonnes, kilograms, grams, litres and
millilitres are normalized consistently. Different materials require an explicit
input/output recipe; mass is never silently converted into volume.

Python calculates sales as saleable output constrained by local and supported
external demand. Population is used through households, purchase frequency,
quantity and market share. No debt-solvency floor increases sales. User-supplied
annual sales (including zero) are retained; onboarding auto-estimates are marked
`estimated` and recalculated with local evidence for the final report.

One operating model and monthly repayment schedule feed dashboard projections and
the DPR. Simple moratorium interest is capitalized before EMI repayment. Losses
are preserved. No-debt cases carry `NO DEBT`, with a numeric zero ratio for JSON
compatibility and `debt_service_required: false`. The assumptions, source of each
field, provider model, evidence snapshot and calculations are saved in the report.
Dashboard and exported documents describe economic estimates explicitly.

The pre-existing working-capital, break-even/payback estimates and ML classifier
remain separate appraisal heuristics; they are not newly trained on LLM estimates.

Validation:

```text
python -m pytest tests/test_enterprise_assumptions.py tests/test_enterprise_report_flow.py tests/test_onboarding_sequence.py tests/test_odop_chat_flow.py -q
python scripts/smoke_enterprise_planning.py --live
cd frontend
node --test tests/financialsRender.test.js tests/planningAssumptionsRender.test.js
npm run build
```

The live smoke check uses synthetic business and village inputs and does not log
credentials. Provider failures are surfaced by that check while production report
generation continues through the labelled fallback.
