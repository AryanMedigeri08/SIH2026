# Udyam Saath v2 audit implementation tracker

Source: `C:\Users\aryan\Downloads\COMPREHENSIVE PLATFORM AUDIT.docx` (external audit; examples and policy claims require independent validation).

## Implemented in the first tranche

- The selected scheme's beneficiary-contribution rate now comes from the existing scheme catalog instead of an unconditional 5%/10% rule. The PMEGP and PMFME rates were cross-checked against KVIC and MoFPI guidance.
- Undeclared promoter cash is no longer represented as a contribution. The report/DPR disclose the contribution shortfall separately and show cash applied in the reconciled financing table.
- Working-capital risk features use only cash left after the promoter contribution, preventing the same cash from being counted twice.
- Report pages no longer invent ODOP designations for three hardcoded districts when the backend registry has no mapped record. An unmapped district gets an explicit verification notice.
- The marketing page no longer hardcodes Bankura-specific packaging claims for the non-ODOP branch.

## Remaining, in suggested order

1. Rebuild the pricing simulator around user-entered, sourced offers for direct haat, kirana wholesale, and mandi/buyback channels; derive the safety floor from evidenced costs and constrain volume by actual machine/working-hour capacity. Remove invented distress/town prices and guarantee language.
2. Replace fixed 55/15/20/10 DPR capital-outlay allocation with an itemized fresh-purchase plan. Carry required machines, already-owned machines, verified cost/quotes, and additional working capital from onboarding through persistence into the report. Reconcile gross value, owned in-kind value, fresh outlay, promoter cash, subsidy timing, and bank debt without double counting. Review the arbitrary onboarding outlay/margin tiers.
3. Correct back-ended subsidy cash-flow treatment, EMI/DSCR sensitivity, working-capital estimation, and borrower-income assumptions. Scheme eligibility and borrower-contribution sufficiency must be distinct from arithmetic reconciliation.
4. Review remaining static ODOP, subsidy, GeM, approval, price-premium, and bank-policy claims throughout marketing, schemes, overview, and DPR text against current primary sources. Prefer conditional language when eligibility has not been verified.
5. Implement the audit's banker CAM and deficiency workflow, government budget/utilization and saturation views, A4 DPR print improvements, ecosystem data provenance, and plain-language beneficiary labels.

## Verification so far

- `venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_financial_buffer.py`: 2 passed.
- `venv\Scripts\python.exe tests/test_phase5.py`: 38 passed, 0 failed.
- `node --test tests/*.js` in `frontend`: 16 passed.
- `node node_modules/vite/bin/vite.js build` in `frontend`: passed with an existing large-chunk warning.
- Full live feasibility pipeline test: attempted but did not complete; external-data path stalled. It remains unverified, not passed.
