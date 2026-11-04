# Automatic village area classification

`backend/app/core/area_classification.py` produces two explicit results after an exact LGD village/hierarchy match. Neither requires a Rural/Urban answer from the user.

1. **Official area category:** recognised local-government type, then an explicit LGD area flag, then a consistent exact-code Census record. Gram/Village Panchayat and municipal types are distinguished; Nagar/Town Panchayat is urban. The existing `is_rural` value used by financial calculations comes only from these official records. Missing status remains unknown and offers a data retry rather than a manual override.
2. **Development profile:** an application estimate of Rural, Semi-urban or Urban characteristics, calculated from measured population, density, employment and amenities. A developed revenue village can retain its official rural category while exhibiting a semi-urban development profile.

This distinction matters because [PMEGP's published guidelines](https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/PMEGP_Guidelines_Certified_2022_3.pdf) use revenue/local-government status for rural classification. The [Census definition](https://ies.gov.in/arthapedia/concept/urban) considers statutory status or population, density and male-main-worker occupation criteria. Amenities by themselves do not confer an official designation.

## Development policy `village_development_v1`

These are transparent application scoring choices, not an official Census or subsidy rule:

| Factor | 0 points | 1 point | 2 points |
|---|---|---|---|
| Population, exact Census village | Below 5,000 | 5,000–19,999 | At least 20,000 |
| Observed population density / km² | Below 400 | 400–1,499 | At least 1,500 |
| Non-agricultural share of all main workers | Below 50% | 50–74.99% | At least 75% |
| Available services, at least 3 observed | Fewer than 3 present | 3 present | At least 4 present |

Services are all-weather road, banking/ATM, internet, market/storage access and at least 18 power hours per day. Absent services are different from unavailable observations. Non-agricultural share uses total main workers minus main cultivators and main agricultural labourers; it is explicitly labelled as **all main workers**, and is not substituted for the official male-main-worker criterion.

Population and at least two other observed factor groups are required. Score 0–2 gives Rural characteristics, 3–5 Semi-urban and 6–8 Urban. Otherwise the development profile is `Insufficient data`. No projected or district-average population is used. Census population is labelled 2011; density uses a known density field or an explicit area in square kilometres. Total/Rural/Urban rows are never summed together.

## Amenities and missing data

The classifier has a separate strict Data.gov.in reader. It accepts a matching village code or complete state/district/block/village identity. It does not reuse the finance module's regional infrastructure baselines, unfiltered district fallback, or default `True` values. Only observed fields enter the score. Successful village observations are cached for 24 hours, at most 512 locations. Provider failures and ambiguous/mismatched records remain unavailable.

The dashboard and onboarding display a read-only automatic result and expandable evidence. The four dropdowns select the business location only. The legacy `verified_is_rural` request property remains parseable for compatibility but is ignored.

Verification includes factor boundaries, changed amenities, missing/invalid data, exact village identity, official-status precedence, conflicting Census records, strict provider/cache behaviour, and the existing onboarding/financial regressions. The live read-only public-village check returned automatic Rural classification, Census population 9,907 and non-agricultural main-worker share 24.43%; exact amenities and density were unavailable, so no development estimate was invented.
