# Documented Assumptions

Every model assumption is listed here. Assumptions are never treated by the engine as
verified official hard gates; scenario outputs using them are labelled as estimates.

## ASSUMPTION-FOIR-DENOMINATOR
- **Statement:** For a FOIR scenario, the income denominator is the salaried applicant's
  `monthly_net_income_inr`, or a correspondingly documented monthly income figure for
  self-employed applicants.
- **Rationale:** Lenders define FOIR and the income denominator differently and usually
  do not publish the exact method. Using net salary is the most conservative available
  estimator.
- **Effect:** Changes the available-EMI estimate; marked as an assumption in every
  scenario output.
- **Status:** Active, acknowledged by `affordability.py` output text.

## ASSUMPTION-SCENARIO-FOIR-CAP
- **Statement:** Scenario FOIR caps used for estimated maximum principal are model
  assumptions, not lender-published limits, unless a rule row's evidence status is
  `verified_official` for that lender.
- **Rationale:** Available EMI requires some cap; using an unlabelled generic 50% would
  imply false precision.
- **Effect:** `affordability_principal_inr` is an estimate bound, clearly labelled.
- **Status:** Active.

## ASSUMPTION-MONTHLY-RATE
- **Statement:** Annual advertised rates are converted to monthly rates as
  `annual_rate / 12` (nominal, reducing-balance EMI convention).
- **Rationale:** Standard Indian personal-loan EMI convention; lenders' advertised rates
  are nominal annual reducing-balance rates.
- **Effect:** EMIs are estimates at range endpoints; real offered rates may differ.
- **Status:** Active, documented in `loan_calculator.py`.

## ASSUMPTION-RATE-PERSONALISATION
- **Statement:** No applicant-specific rate can be derived from CIBIL or other variables
  without a published deterministic formula. Per-applicant rates are null with status
  `NOT_PUBLICLY_DETERMINABLE`; scenario EMIs use the advertised range endpoints.
- **Rationale:** Prohibiting invented risk-based pricing.
- **Effect:** EMI shown as a range, not a single offer.
- **Status:** Active.

## ASSUMPTION-NO-SILENT-PASS
- **Statement:** A missing or unknown value never silently passes a mandatory gate; the
  gate is unevaluable and the lender becomes `REVIEW_REQUIRED`.
- **Rationale:** Prevents fabricated approvals from incomplete data.
- **Effect:** High REVIEW_REQUIRED counts (intentional, honest).
- **Status:** Active rule-engine semantics.

## ASSUMPTION-SYNTHETIC-INSIGHTS
- **Statement:** Insights in `outputs/rule_failure_analysis.csv` come only from the 14
  synthetic test profiles and do not estimate real-world approval or rejection rates.
- **Status:** Active, labelled on outputs and the Streamlit coverage tab.
