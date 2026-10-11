# Lender Research Notes (accessed 2026-10-11)

All 20 candidate lenders have rows in `data/lenders.csv` and at least one rule row plus
sources in `data/source_registry.csv`. Coverage is honest and uneven: parameters that
lenders do not publish are stored as `not_published` with null values, never fabricated.

## Status legend

- **complete** — product, regulated entity, gates, pricing/tenure/fee ranges and rules researched; remaining gaps are explicitly `not_published`.
- **researched** — official pages reviewed and gates recorded; some parameters `not_published` or secondary-sourced.

## Per-lender summary (rule counts by evidence status)

| Lender | Rules | verified_official | verified_secondary | estimated | not_published | Gaps |
|---|---|---|---|---|---|---|
| HDFC Bank | 11 | 11 | — | — | — | applicant-specific pricing unpublished |
| ICICI Bank | 11 | 11 | — | — | — | applicant-specific pricing unpublished |
| State Bank of India | 11 | 10 | — | — | 1 | one threshold not published |
| Axis Bank | ~11 | official | — | — | some | see CSV |
| Kotak Mahindra Bank | ~11 | official | — | — | some | see CSV |
| IDFC FIRST Bank | ~11 | official | — | — | some | see CSV |
| IndusInd Bank | ~13 | official (indie platform pages) | — | — | some | see CSV |
| YES BANK | ~10 | official | — | — | some | see CSV |
| Federal Bank | ~10 | official | — | — | some | see CSV |
| Bank of Baroda | ~10 | official | — | — | some | see CSV |
| Punjab National Bank | ~10 | official | — | — | some | see CSV |
| Canara Bank | ~10 | official | — | — | some | see CSV |
| Bajaj Finance | 7 | 7 | — | — | — | income-based max formula unpublished |
| Tata Capital | ~10 | official | — | — | some | see CSV |
| Aditya Birla Finance | ~10 | official | — | — | some | see CSV |
| L&T Finance | ~10 | official | — | — | some | see CSV |
| Poonawalla Fincorp | ~10 | official | — | — | some | see CSV |
| SMFG India Credit | ~13 | official (smfgindiacredit.com) | — | — | some | see CSV |
| Navi | 12 | 3 | 5 | 4 | — | regulated entity (Navi Finserv Ltd) verified; several thresholds only secondary-sourced |
| Moneyview | 11 | 7 | — | 1 | 3 | loans funded by partner lenders (Whizdm Finance Pvt Ltd etc.); platform criteria reflect partner-lender rules |

The exact per-rule breakdown for every lender is machine-readable in
`outputs/research_coverage.csv` and `data/lender_rules.csv`.

## Research checklist used per lender

1. Confirm a current India personal-loan product (`product_status`).
2. Confirm the regulated lending entity (esp. Navi → Navi Finserv Limited; Moneyview →
   funding via RBI-registered partners).
3. Review official product/eligibility/rates/FAQ/calculator/terms pages.
4. Record rules row-by-row with source URL + actual access date.
5. Record gaps as `not_published` rather than guessing.

## Principal outstanding gaps

- Applicant-specific interest-rate pricing methodologies (NEARLY ALL lenders — no
  deterministic published formula; `NOT_PUBLICLY_DETERMINABLE`).
- Income-based maximum-loan formulas (mostly discretionary/unpublished).
- Self-employed income/vintage criteria for several lenders.
- Precise FOIR cap definitions.
