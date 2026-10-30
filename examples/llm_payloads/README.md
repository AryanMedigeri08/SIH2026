# Filled dairy sales-forecast example

These files contain a complete, fictional input for a milk-pasteurisation and
delivery forecast. They contain no saved beneficiary data or credentials. They
have not been sent to an LLM as part of creating this example.

- `dairy_sales_payload.json`: readable user-message payload, including the full
  Pydantic output schema, permitted equations, exact unit labels, allowed machine
  profile IDs and response-nesting example.
- `dairy_sales_request.json`: complete Sarvam-compatible chat-completions request
  with the current forecasting system prompt and that payload as the user
  message. Supply provider authentication separately through application config.

## Business and evidence

- Proposed activity: pasteurise purchased raw milk and sell milk by the litre.
- Channels: recurring home delivery and occasional direct retail; these customer
  cohorts must not be double-counted. Offered pack sizes are not measured demand.
- Location: fictional village/block/district in Karnataka.
- Project budget: INR 2,000,000; two staff; 26 operating days/month, eight hours/day.
- Forecast: November 2026 through October 2027.
- Population 5,000, households 1,000, 18 hours of power and road access are explicit
  demonstration assumptions, not database/API observations.
- Competitors, actual customer uptake, local prices, orders and supply agreements
  are unavailable. CPI 4.85% is the application fallback, not current local data.
- Machinery capacities/prices are copied from the restored catalogue. Smaller
  variant prices are derived estimates, not verified supplier quotations.

The example deliberately filters machinery candidates to the milk-processing
profile and updates the allowed-ID schema accordingly. The current keyword
retriever can also match irrelevant terms in long descriptions, including
negations; this manually curated example is not a claim that retrieval is fixed.

## Response and use

The LLM must return business classification, driver and price assumptions,
twelve monthly values for each of three scenarios, production conversion,
independent operational capacity, setup/working-capital reserve and limitations.
The embedded `output_shape_example` demonstrates syntax only; its artificial
numbers must not be reused as market benchmarks.

Backend arithmetic then selects affordable machinery, converts input throughput
to saleable units, respects shared/independent capacity, and sums monthly sales
quantity times the corresponding price across twelve months. There is no target
DSCR, required profit or annual-sales target in this input. Loan/DSCR calculations
are outside this payload. Forecast results remain provisional, with assumptions
and evidence retained for audit.
