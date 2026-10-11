# Data Dictionary

Full field-level dictionary for every applicant variable also lives in
`data/input_variables.csv` (name, label, definition, type, unit, allowed values/range,
source category, segment, required/conditional status, validation rules).

## 1. Applicant variables

### Identity and requested product
| Variable | Type | Unit | Validation |
|---|---|---|---|
| `applicant_age_years` | integer | years | ≥ 18 for any GO; validated ≥ 0 |
| `residence_country` | string | — | default India |
| `city` | string | — | free text |
| `employment_type` | enum | — | `salaried` / `self_employed` / `other` |
| `customer_segment` | enum | — | `new_customer` / `existing_customer` / `preapproved` / `unknown` |
| `requested_loan_amount_inr` | decimal | INR | ≥ 0 |
| `requested_tenure_months` | integer | months | > 0 |

### Salaried segment
`monthly_net_income_inr` (required for salaried), `monthly_gross_income_inr`,
`current_job_tenure_months`, `total_work_experience_months`, `employer_category`,
`salary_credit_consistency` — nullable unless stated required.

### Self-employed segment
`annual_itr_income_inr`, `itr_years_available`, `business_vintage_months`,
`monthly_business_revenue_inr`, `monthly_business_profit_inr`.

Revenue, profit and ITR income are **never substituted** for one another without a
documented method.

### Bureau / credit
`cibil_score` (300–900 or null), `credit_history_months`, `active_loan_count`,
`credit_enquiries_6m`, `overdue_amount_inr`, `days_past_due_max`,
`written_off_accounts_count`, `settled_accounts_count`, `credit_card_utilisation_pct`.

### Affordability
`existing_monthly_emi_inr`, `other_monthly_debt_obligations_inr`; derived
`total_monthly_obligations_inr`, `foir_pct`, `available_emi_inr`.

**Privacy:** PAN, Aadhaar, bank account numbers, uploaded documents and other direct
identifiers are not collected. Sample data is synthetic; no persistence by default.

## 2. Rule fields (`data/lender_rules.csv`, one row per rule)

| Field | Meaning |
|---|---|
| `rule_id`, `lender_id`, `product_name` | identity |
| `parameter_name` | applicant variable the rule tests |
| `rule_category` | `GO_NO_GO`, `CREDIT_BUREAU`, `INCOME_AND_EMPLOYMENT`, `AFFORDABILITY`, `LOAN_AMOUNT`, `PRICING`, `TENURE`, `FEES`, `DOCUMENTATION`, `PRODUCT_AVAILABILITY`, `CUSTOMER_SEGMENT` |
| `rule_type` | `hard_gate`, `soft_threshold`, `product_constraint`, `pricing_band`, `documentation_requirement`, `derived_assumption` |
| `operator` | `>=`, `<=`, `==`, `in`, `range`, `requires`, `informational` |
| `value_numeric`, `value_text`, `range_min`, `range_max`, `unit` | threshold values (null = unknown) |
| `employment_segment`, `customer_segment` | rule scope |
| `mandatory` | hard gate if true and verified |
| `evidence_status`, `confidence` | see research_methodology.md |
| `source_id`, `source_url`, `source_title`, `source_type`, `accessed_date`, `effective_date` | provenance |
| `assumption_description`, `notes` | context for estimated/unknown rules |

## 3. Lender fields (`data/lenders.csv`)

`lender_id`, `lender_name`, `lender_type` (`bank`/`nbfc`/`digital_platform`),
`regulated_entity_name`, `product_name`, `official_product_url`, `product_status`
(`verified_active`/`unverified`/`not_found`), `selection_rationale`, `last_verified_date`,
`research_status`, `notes`.

## 4. Source fields (`data/source_registry.csv`)

`source_id`, `lender_id` (nullable for RBI/general), `source_title`, `source_url`,
`source_type`, `publisher`, `published_or_effective_date`, `accessed_date` (ISO),
`supports_rule_ids`, `notes`.
