# Year-one sales forecasting

Scope: estimate demand and selling prices with a structured LLM response, then
calculate machinery capacity, monthly sales and year-one revenue in Python.
Do not change loan rules, project outlay, operating margins or the DSCR formula.
Existing downstream financial calculations will consume the new sales input;
their existing 30% operating-income assumption remains pending a later change.

## Delivery steps

1. Restore the 37-profile machinery catalogue from Refactor-wizard-aryan. Keep
   reference and scaled prices explicitly indicative, not supplier quotations.
2. Add a bounded structured forecasting service: provenance-aware evidence,
   business-specific equations, three scenarios and twelve months; deterministic
   quantity, conversion, capacity selection and revenue validation; nonblocking
   fallback with explicit limitations. Test arithmetic, malformed responses,
   recipe/unit errors, shared capacity, zero sales and provider failure.
3. Integrate opt-in estimated sales into new-business onboarding and persist the
   complete forecast alongside the report and DPR. Keep manual/historical inputs
   backward compatible. Display the scenario range, equipment selection, monthly
   volumes, prices, sources and review warnings. Check the production build and
   report flow, then commit the completed change.

## Data contract and boundaries

- Evidence includes location, exact business idea, operating constraints, Census
  provenance, UDYAM retrieval coverage, amenities provenance, CPI period/source,
  ODOP and candidate catalogue variants. Never include a target DSCR or desired
  revenue/profit in the demand prompt. A fallback is not observed market data.
- LLM output consists of classification, product/channel units, an approved demand
  equation and its drivers, prices, process conversion and capacity assumptions,
  monthly scenarios, source references, confidence and limitations. No executable
  expressions, fabricated citations or unlisted machinery IDs.
- Annual sales = sum of all product/channel monthly quantities sold times their
  respective prices, across twelve months. Expected demand and effective capacity
  are separate. Shared equipment cannot be allocated in full to multiple products.
- A catalogue throughput must be converted to saleable units using an explicit
  output-per-input conversion; storage uses stock and occupancy, not throughput.
  Unknown infrastructure or process suitability requires review, never a guarantee.
- The machine budget reserves setup/working capital explicitly. Do not overwrite
  project cost or financing rules. Pick the smallest affordable sufficient variant,
  or cap the forecast at the affordable configuration and disclose the shortfall.
- Save accepted assumptions, evidence snapshot, version identifiers and calculated
  outputs. Reading a saved report does not rerun an LLM. Estimates remain
  provisional, especially when evidence is sparse. Fall back to a labelled manual
  estimate if providers/validation fail; never relabel it as validated demand.
- LLM observations are unverified unless their source matches evidence supplied by
  the application. Population, business registrations and CPI do not measure sales.

This document describes implementation scope, not verified market benchmarks.
