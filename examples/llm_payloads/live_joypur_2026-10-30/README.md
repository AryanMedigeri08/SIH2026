# Real-source Jaypur sales comparison snapshot — 30 October 2026

This is a frozen evidence payload, not a generated sales forecast. No LLM was
called. No saved beneficiary reports or private user tables were queried.

## Files to use

- `messages.json`: the exact system/user messages, response schema and generation
  settings for comparison. Add the desired provider's model name and credentials
  separately. Use the identical file for each model; do not let individual models
  fetch additional evidence if comparing their reasoning on this input.
- `payload.json`: complete structured user-message payload, including output
  schema and machinery candidates.
- `data.json`: readable business and evidence portion without schema helpers.
- `raw_village_amenities.json`: exact public village record selected by Census
  code, preserving original labels and NA values.
- `manifest.json`: snapshot time, source endpoints and SHA-256 checksums.
- `verified_cpi_publication.json`: independent cross-check transcribed from the
  official PDF opened through the web tool. The final collector also successfully
  fetched and parsed the official HTML release directly.

## What was actually fetched

- Read-only database query identified Jaypur village: Census code 328046, state
  19, district Census code 339, subdistrict 02368. The LGD district code is 305
  and development block code 2782. Joypur is a common alternate spelling.
- Census 2011: population 3,136, households 741. These are not the Joypur block's
  population or a measured 5/10-km catchment.
- OGD UDYAM API: all 948 records reported for PIN 722138 were retrieved across
  two pages. Eighteen names/activity descriptions explicitly matched milk/dairy
  keywords. This is a broad registration sample, not 18 confirmed operating direct
  competitors. General grocers and informal milk sellers can be missing.
- OGD amenities: three villages share the Jaypur name. The correct code is
  exported by OGD as `'328046` with an Excel-style leading apostrophe. Exact-code
  matching selected the appropriate record rather than the first name match.
  Dataset title says 2011 and its record reference-year field says 2009; both are
  preserved. It reports 10/12 commercial power hours in summer/winter and paved
  road/banking availability. These are historical observations, not current
  infrastructure guarantees. Unavailable cold-storage/internet data stay null.
- Official MoSPI/PIB release dated 12 October 2026: West Bengal September 2026
  rural CPI inflation 4.44%, rural index 109.31, base 2024=100, provisional.
  The configured database's newest chronological CPI record was July 2026;
  the newer official publication is supplied separately.
- Banglar Dairy's public product API: six active milk products. Milk price fields
  were 0.00; the producer's website interprets these as no price displayed, so
  they are exported as null, never as free milk. No village-specific selling or
  raw-milk procurement quote could be verified.
- The existing ODOP registry and machinery catalogue are labelled local reference
  data. Machinery variants and prices are indicative estimates, not newly fetched
  supplier quotations. The dairy candidate and its five variants are explicitly
  selected from the full catalogue for this controlled comparison, independently
  of the application's generic keyword ranking.

## Proposed inputs, not fetched facts

The milk-pasteurisation business, INR 20 lakh project budget, two staff,
26 days/month, eight hours/day and November 2026 startup are proposed comparison
inputs. They do not describe a verified operating enterprise. The 2026 population
projection applies a documented approximate historical growth assumption; it is
not a current Census observation or a count of customers.

Actual orders, customer acquisition, repeat purchases, achievable local prices,
raw-milk supply and current operating constraints remain unknown. Each model
must identify its assumptions and uncertainty and must not tune sales to a DSCR.

For comparison, record the provider/model/version, parameters and raw response,
then check its demand equations, purchase frequency, price basis, units,
equipment fit and twelve-month arithmetic. Different unsupported assumptions
can produce different sales even when both calculations are arithmetically valid.

To recollect the public sources, run `scripts/collect_joypur_sales_snapshot.py`
from the repository root with the project Python environment. It deliberately
uses read-only SQL. Recollection changes the snapshot and its hash; freeze one
copy before sending it to multiple models.
