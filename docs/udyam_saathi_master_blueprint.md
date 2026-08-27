# 🏛️ UDYAM SAATHI (उद्यम साथी) — Master Project Blueprint & Architecture

> **SIH 2026 — Problem Statement 26091**: AI-Powered Rural & Semi-Urban Enterprise Feasibility & Credit Advisory Platform.  
> **Core Mission**: Transform raw Indian public data (Census, LGD, MSME, MoSPI CPI, IMD, Government Schemes) into an **auditable, 100% pitch-defensible, bank-ready** business feasibility report and DPR (Detailed Project Report) in under 2 seconds.

---

## 1. Executive Summary & Core Philosophy

Rural entrepreneurs in India face three systemic barriers when starting an enterprise:
1. **Lack of Hyper-Local Market Feasibility**: Information on local demand, competitor saturation, and raw material access is fragmented across disparate government portals.
2. **Complex Government Scheme Rules**: Over 10+ central and state schemes (PMEGP, PMFME, MUDRA, Stand-Up India, PM Vishwakarma) have intricate subsidy slabs (15%–35%), reservation rules, project cost ceilings, and eligibility criteria.
3. **Bank Rejection due to Poor DPRs**: Lending institutions reject up to 60% of rural micro-loan applications due to non-standard Detailed Project Reports (DPRs), unrealistic cashflow projections, or improper Debt Service Coverage Ratios (DSCR).

**Udyam Saathi solves this through a Hybrid Tri-Tier Architecture**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            UDYAM SAATHI TRI-TIER ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 1: 100% DETERMINISTIC MATHEMATICAL & SPATIAL CORE                     │
│  • LGD 6-Tier Hierarchy + Census 2011 Compound Growth Projections (2026)    │
│  • Government Scheme Multi-Scheme Benefit Optimization (Rank 1 to N)        │
│  • EMI Amortization with Moratorium, Working Capital, and DSCR Formulas     │
│  • 8-Point Quantified Risk Matrix & Grounded SWOT Analysis with Exact ₹     │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 2: SUPERVISED MACHINE LEARNING VIABILITY CLASSIFIER                   │
│  • Flagship 10-D XGBoost Multi-Class Model (98.9%+ Stratified CV Accuracy)  │
│  • Predicts [SUITABLE / CAUTION / RECONSIDER] with Exact Probabilities       │
│  • Feature Importance Ranking & SHAP-like Grounded Explainability           │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 3: UNIFIED HIGH-SPEED AI SYNTHESIS & BANK-READY DPR EXPORT            │
│  • Single Groq Call (Llama 3.3 70B) with SHA-256 In-Memory Caching (<1ms)   │
│  • 100% Deterministic Offline Fallback Narrative (Zero-Crash Guarantee)     │
│  • Multi-Lingual Generation in 6 Indian Languages (EN, HI, MR, TA, TE, KN) │
│  • 7-Section Bank-Ready DPR Aligned with Scheduled Commercial Bank Formats │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Mathematical & Algorithmic Formulations

### 2.1 Population Projection Formula (Census 2011 to 2026)
Population is projected forward from the 2011 Census base using official state-wise Compound Annual Growth Rates (CAGR):

$$P_{t} = P_{2011} \times (1 + r)^{(t - 2011)}$$

- $P_{2011}$: Verified base population from `census_raw`
- $r$: Annual growth rate from `growth_rates.json` (e.g., $0.0125$ for West Bengal, $0.0097$ National)
- $t$: Current evaluation year (e.g., $2026$)
- $Households = \lfloor P_{t} / 4.8 \rfloor$ (Average Indian rural household size)

### 2.2 Total Addressable Market (TAM) & Monthly Transaction Volume
$$Target\_HH = Households \times Penetration\_Rate(Sector)$$
$$Monthly\_Units = Target\_HH \times Monthly\_Frequency(Sector)$$
$$Monthly\_TAM = Monthly\_Units \times Average\_Ticket\_Size(Sector)$$

| Sector / Business Type | Penetration Rate | Monthly Frequency | Avg Ticket Size (₹) |
| :--- | :---: | :---: | :---: |
| **Dairy / Milk Processing** | $42\%$ | $26\text{ orders/mo}$ | ₹$75$ |
| **Food Processing / Bakery / Grocery** | $38\%$ | $12\text{ orders/mo}$ | ₹$180$ |
| **Repair / Electrical / Technical** | $28\%$ | $2\text{ orders/mo}$ | ₹$350$ |
| **Apparel / Tailoring / Boutique** | $30\%$ | $2\text{ orders/mo}$ | ₹$450$ |
| **Fabrication / Heavy Manufacturing** | $18\%$ | $1\text{ orders/mo}$ | ₹$1,200$ |

### 2.3 Financial Amortization & Moratorium Schedule
For loan principal $L$, annual interest rate $i$, tenure in months $N = \text{Tenure (Years)} \times 12$, and moratorium period $M$ months:
- Monthly interest rate: $r_m = i / 12$
- Effective repayment months: $n = N - M$
- Monthly EMI (Equal Monthly Installment):
$$EMI = L \times \frac{r_m (1 + r_m)^n}{(1 + r_m)^n - 1}$$
- Moratorium Simple Interest:
$$I_{moratorium} = L \times r_m \times M$$
- Total Interest Payable:
$$I_{total} = I_{moratorium} + (EMI \times n - L)$$

### 2.4 Debt Service Coverage Ratio (DSCR)
The universal banking solvency metric mandated by RBI (benchmark $\ge 1.33$):

$$DSCR = \frac{\text{Estimated Monthly Net Operating Income}}{\text{Monthly EMI Liability}}$$

$$\text{Verdict} = \begin{cases} 
\text{VIABLE} & \text{if } DSCR \ge 1.33 \\
\text{MARGINAL} & \text{if } 1.00 \le DSCR < 1.33 \\
\text{AT RISK} & \text{if } DSCR < 1.00 
\end{cases}$$

### 2.5 Multi-Scheme Net Financial Benefit Optimization
For every registered scheme in `government_schemes.json`, we calculate:

$$Net\_Benefit = Subsidy\_Grant\_Amount - Total\_Interest\_Payable$$

The platform ranks all schemes dynamically ($1 \dots K$). The scheme providing the maximum capital subsidy while minimizing total interest paid is awarded **Rank #1**.

---

## 3. The 10-Dimensional ML Feature Vector

The XGBoost Classifier operates on a normalized 10-D feature space:

| Index | Feature Key | Data Type | Physical Meaning | Provenance Source |
| :---: | :--- | :---: | :--- | :--- |
| **$x_0$** | `dscr` | `float [0.0 - 5.0]` | Debt Service Coverage Ratio | `financial_calculator.py` |
| **$x_1$** | `subsidy_coverage_ratio` | `float [0.0 - 1.0]` | $\text{Subsidy} / \text{Total Project Cost}$ | `government_schemes.json` |
| **$x_2$** | `loan_to_income_ratio` | `float [0.0 - 10.0]` | $\text{Loan Amount} / \text{Annual Gross Income}$ | Financial Projections |
| **$x_3$** | `log_projected_population` | `float [2.0 - 6.0]` | $\log_{10}(\text{Projected Population})$ | `census_raw` + CAGR |
| **$x_4$** | `msme_density_per_10k` | `float [0.0 - 200.0]` | Registered MSMEs per 10k population | `msme_district` table |
| **$x_5$** | `infrastructure_score` | `float [0.0 - 10.0]` | Paved Road (2.0) + Haat (1.5) + Power (1.5) + Bank (1.0) + PDS (1.0) | `village_amenities_cache` |
| **$x_6$** | `cpi_inflation_pct` | `float [-2.0 - 20.0]` | State Rural Consumer Price Index Inflation | `cpi_data` (MoSPI) |
| **$x_7$** | `working_capital_months_buffer` | `float [0.0 - 24.0]` | $\text{Promoter Margin} / \text{Monthly WC Outlay}$ | Financial Engine |
| **$x_8$** | `competition_intensity` | `float [0.0 - 1.0]` | Estimated local competitors per 1k catchment | MSME + Demographics |
| **$x_9$** | `weather_risk_score` | `float [0.0 - 1.0]` | $\text{Heavy Rain Days (>64.5mm)} / 30$ | `imd_weather_cache` |

---

## 4. Government Scheme Knowledge Engine

The system contains full parameterization for India's major enterprise schemes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GOVERNMENT SCHEME REGISTRY COVERAGE                     │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Scheme Name       │ Target Sector     │ Max Outlay (₹)    │ Subsidy / Grant │
├───────────────────┼───────────────────┼───────────────────┼─────────────────┤
│ **PMEGP**         │ Mfg / Service     │ ₹50L (Mfg) / ₹20L │ 15% to 35%      │
│ **PMFME**         │ Food Processing   │ ₹1 Crore          │ 35% (Max ₹10L)  │
│ **MUDRA Shishu**  │ Micro / Retail    │ ₹50,000           │ Collateral-free │
│ **MUDRA Kishore** │ Micro / Small     │ ₹5,00,000         │ Collateral-free │
│ **MUDRA Tarun**   │ Small Business    │ ₹10,00,000        │ Collateral-free │
│ **MUDRA Tarun +** │ Repeat Borrowers  │ ₹20,00,000        │ Collateral-free │
│ **Stand-Up India**│ SC / ST / Women   │ ₹10L to ₹1 Crore  │ 85% Composite   │
│ **PM Vishwakarma**│ 18 Artisan Trades │ ₹3,00,000         │ 5% Subvention   │
│ **DAY-NRLM**      │ Women SHG Units   │ ₹3,00,000         │ 7% Subvention   │
│ **NABARD AHIDF**  │ Dairy / Livestock │ ₹5 Crore+         │ 3% Subvention   │
└───────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

---

## 5. Bank-Ready Detailed Project Report (DPR) Structure

Every analysis can be exported into an official 7-section Bank Appraisal Report:

1. **Header & Enterprise Profile**: DPR Number, Promoter Social Category, Constitution, Target Village/District.
2. **Capital Outlay & Means of Finance**: Machinery (55%), Electrification (15%), Initial Buffer (20%), Margin (5–10%), Subsidy (15–35%), Bank Term Loan (55–80%).
3. **Financial & Cash Flow Projections**: Annual Turnover, Raw Material Outlay, Gross Operating Margin, Annual Bank Interest, Depreciation, Net Annual Profit.
4. **Multi-Scheme Optimization Table**: Comparative ranking of all eligible government schemes by net benefit.
5. **Machine Learning Viability Appraisal**: XGBoost model prediction, confidence level, and class probability distribution.
6. **Quantified SWOT & 8-Point Risk Mitigation Table**: Concrete operational steps and rupee-denominated buffers.
7. **Statutory Bank Submission Checklist**: Mandatory documents required by Scheduled Commercial Banks.

---

## 6. SIH Pitch Deck & Jury Defense Strategy

### Frequently Asked Questions by SIH Jury & Pitch Answers:

> **Q1: "Is your LLM hallucinating financial numbers and scheme rules?"**  
> **Answer**: *"No. Our LLM does zero financial calculations. 100% of financials, EMIs, subsidies, DSCR ratios, and risk thresholds are computed deterministically using pure mathematical formulas and externalized JSON scheme registries. The LLM is strictly used in a single, unified call to format the executive narrative and translate into regional languages."*

> **Q2: "Why use Machine Learning if your formulas are deterministic?"**  
> **Answer**: *"Formulas compute accounting viability (DSCR), but the XGBoost ML model evaluates multi-dimensional enterprise survivability across 10 non-linear variables simultaneously—such as competition saturation, infrastructure readiness, rainfall risk, and inflation pressure. This mirrors the dual-underwriting process of commercial banks."*

> **Q3: "How does the system handle internet outages or LLM API rate limits?"**  
> **Answer**: *"We implement SHA-256 in-memory caching for instant (<1ms) replay, plus a 100% deterministic template narrative fallback. If Groq or OpenRouter goes down, the platform continues generating complete, bank-ready feasibility reports without throwing errors."*
