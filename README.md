# India Personal Loan Eligibility & Recommendation Engine

A transparent, **rule-based** (no machine learning) engine that evaluates a synthetic or
user-entered applicant profile against **publicly documented** lender rules for unsecured
personal loans in India, then ranks feasible lenders with a full, auditable explanation.

**Why this project exists.** Real lenders apply dozens of eligibility criteria — age,
CIBIL cut-offs, income floors, employer category, job tenure, business vintage, existing
obligations, product limits — but almost never publish how these combine. Existing
"eligibility checkers" hide their logic behind an opaque score. This project takes the
opposite approach: every single rule is a visible row in a CSV, every threshold carries
its source URL and the date it was checked, and any unknown is shown as unknown rather
than guessed. The output you see can be traced back, rule by rule, to a public web page.

> **Disclaimer:** This tool is educational/research-based. It is **not** a lender
> decision, an approval promise, or financial advice. Passing documented public criteria
> does not mean a lender will approve an application; lenders apply additional internal
> policies that are not public.

~1 minute read for rules · 3-minute read for how it works.

---

## Table of contents

1. [Scope and lender universe](#scope-and-lender-universe)
2. [How it works — two rule layers](#how-it-works--two-rule-layers)
3. [The recommendation layer](#the-recommendation-layer)
4. [Evidence taxonomy & research method](#evidence-taxonomy--research-method)
5. [Quick start](#quick-start)
6. [Using the Streamlit app](#using-the-streamlit-app)
7. [Command-line interface](#command-line-interface)
8. [Using the engine as a library](#using-the-engine-as-a-library)
9. [Repository layout](#repository-layout)
10. [Testing](#testing)
11. [Current research coverage](#current-research-coverage)
12. [Insights from the synthetic run](#insights-from-the-synthetic-run)
13. [Worked example](#worked-example)
14. [Assumptions in plain language](#assumptions-in-plain-language)
15. [Privacy & data handling](#privacy--data-handling)
16. [Limitations](#limitations)
17. [Future work](#future-work)

---

## Scope and lender universe

- **Personal loans in India only.** Home, auto, education, gold, and business loans are
  deliberately out of scope — the engine's rules are collected for personal-loan
  products only.

- **20 candidate lenders** (project-defined coverage set, **not** a definitive ranking):

  | Type | Lenders |
  |---|---|
  | Banks | HDFC Bank, ICICI Bank, State Bank of India, Axis Bank, Kotak Mahindra Bank, IDFC FIRST Bank, IndusInd Bank, YES BANK, Federal Bank, Bank of Baroda, Punjab National Bank, Canara Bank |
  | NBFCs | Bajaj Finance, Tata Capital, Aditya Birla Finance, L&T Finance, Poonawalla Fincorp, SMFG India Credit |
  | Digital platforms | Navi, Moneyview |

  **Selection method:** market relevance, category diversity (banks / NBFCs / digital
  platforms), and public-information availability. **Limitations of this method:**
  smaller banks, captive NBFCs and credit-card-fintech lenders are under-represented;
  no attempt was made to rank lenders by size or approval friendliness.

- **Regulated entities verified for digital platforms.** Digital platforms often broker
  rather than fund loans, so the regulated lender matters:
  - **Navi** → lends directly as **Navi Finserv Limited** (RBI-registered NBFC).
  - **Moneyview** → platform; loans are evaluated and disbursed by RBI-registered
    partners (e.g. **Whizdm Finance Pvt Ltd**, SMFG India Credit). Its published
    eligibility reflects partner-lender criteria.

---

## How it works — two rule layers

The engine deliberately splits its thinking into two layers so that hard facts and soft
estimates never blur together.

### Layer A — Go/No-Go gates
Mandatory, **verified** hard rules (e.g. minimum age, minimum CIBIL, maximum requested
amount). If one fails → the lender is `NO_GO`, with the failed gate, the required
threshold, and your actual value shown side by side, plus the source link.

### Layer B — Parameter-based evaluation
Everything that shapes an offer but shouldn't automatically reject: credit bureau
signals, income/ITR adequacy, employment stability, affordability (FOIR), loan amount
fit, pricing, tenure, fees, documentation.

### Decision semantics (per lender, per applicant)

| Decision | Meaning |
|---|---|
| 🟢 `GO` | All applicable, researched, mandatory gates are evaluable **and** pass. A coverage warning is always shown — public rule data is never complete. |
| 🔴 `NO_GO` | At least one **verified mandatory** hard gate failed. Known failures can trigger this even if other fields are missing (missing fields are still listed). |
| 🟡 `REVIEW_REQUIRED` | No gate failed, but the evaluation is blocked: applicant data missing, a rule is unpublished (`not_published`), or a rule hasn't been researched. |

Per applicant (aggregated over all lenders):
`ELIGIBLE_UNDER_DOCUMENTED_RULES` · `NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES` ·
`INSUFFICIENT_INFORMATION`.

**Safety rules built into the decision logic:**
- A missing value **never silently passes** a gate; it makes the gate unevaluable.
- Secondary, estimated, and unknown rules are **never treated** as verified hard gates.
- No fabricated thresholds: if a lender doesn't publish a minimum CIBIL, the value is
  stored as **null with status `not_published`** — not an invented 700, not zero.

### What you get for each lender

- Failed / unresolved / passed gates with required value, actual value, evidence status,
  source URL, and access date (expandable in the UI).
- Estimated maximum loan amount (product max ∩ income-based limit ∩ affordability limit,
  where each bound is known).
- Advertised annual interest-rate range and EMI scenarios **at the range endpoints**
  (never a fake applicant-specific rate — see assumptions).
- Feasible tenure ranges, processing fee structure where published, and what remains
  unknown — stated as unknown, not zero.

---

## The recommendation layer

For lenders with a clean GO, a transparent weighted comparison produces ranked
"estimated offers":

- `lowest_estimated_cost` — cheapest at the requested amount/tenure using range endpoints.
- `lowest_emi` — budget-friendly monthly outflow.
- `highest_estimated_amount` — maximum estimated affordability headroom.
- `balanced` — feasibility first, then estimated cost, then evidence quality.

You can switch preferences in the UI and watch rankings change. There is **no opaque
"approval probability"** and no implied "best lender for everyone". `NO_GO` lenders are
excluded from offers; `REVIEW_REQUIRED` lenders are shown in a separate
"needs more information / rules incomplete" group, never as confirmed matches. If no
lender reaches GO, the engine **refuses to manufacture a recommendation** and says so.

---

## Evidence taxonomy & research method

Every rule row carries one of these evidence statuses:

| Status | Meaning | Treated as a hard gate? |
|---|---|---|
| `verified_official` | Directly supported by a current official lender/regulatory source | Yes |
| `verified_secondary` | Credible comparison/knowledge source, not confirmed officially | No |
| `estimated` | Model assumption, flagged with `assumption_description` | No |
| `not_published` | Researched; lender genuinely doesn't publish it (value = null) | No (unevaluable) |
| `not_researched` | Research incomplete (value = null) | No (unevaluable) |
| `unverified` / `stale` | Source exists but couldn't be validated / may be outdated | No |

**Search order used** (details in `docs/research_methodology.md`):
1. Official lender pages — product page, eligibility, rates & fees, calculator, FAQs, terms.
2. Official PDFs and product documents linked from those pages.
3. RBI material — regulatory context only; a general RBI rule is **never** recorded as a
   lender-specific underwriting rule.
4. Reputable comparison sites — discovery/cross-check only, always labelled secondary.
5. Search snippets are never the sole evidence when the actual page can be opened.
   Paywalls, logins, and anti-bot controls are never bypassed.

Every source is registered in `data/source_registry.csv` with its URL, title, publisher,
source type, and the **actual access date** (2026-10-11 for all current sources).
Conflicts between sources are resolved in favour of the official page and noted.

---

## Quick start

Requires Python 3.11+.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash              (or .venv/bin/activate on Linux/macOS)

# 2. Install dependencies
pip install -r requirements.txt

# Optional but recommended: install the engine as a package
pip install -e .                   # thanks to setup.py; then `import loan_engine` works everywhere

# 3. Run the test suite (7 test modules — see Testing below)
PYTHONPATH=src python -m pytest -q

# 4. Generate all sample outputs from the 14 synthetic profiles
PYTHONPATH=src python -m loan_engine.cli \
  --profiles data/test_profiles.json --output data/test_results.json --write-outputs

# 5. Launch the Streamlit web UI
streamlit run app.py               # opens http://localhost:8501
```

All commands work from the repository root. If you installed with `pip install -e .`
you can drop the `PYTHONPATH=src` prefix (the commands below keep it for portability).

`--write-outputs` regenerates four files **from the current code and data** (never
hand-written predictions):

| File | Contents |
|---|---|
| `data/test_results.json` | Full per-profile engine results: profile, validation, derived features, affordability scenario, per-lender decisions, gate details, recommendation |
| `outputs/sample_predictions.csv` | One row per (profile × lender): decision, gate counts, EMI/rate/amount estimates where available |
| `outputs/rule_failure_analysis.csv` | Which rules failed most often across profiles, with numerator (`failures`) and denominator (`evaluations`) |
| `outputs/research_coverage.csv` | Per-lender rule counts by evidence status, source counts, last access dates |

---

## Using the Streamlit app

Five tabs, all built on the same engine the CLI uses (the UI is a thin layer):

| Tab | What it does |
|---|---|
| 🧾 **Applicant assessment** | Grouped form: basic/request, segment-aware employment & income (salaried fields vs ITR/business fields), optional bureau inputs where **leaving 0 means "unknown"**, existing obligations. Includes a synthetic-sample-profile dropdown (14 profiles) and a prominent disclaimer. |
| 📊 **Results** | Applicant outcome, affordability scenario summary, recommendation summary, ranked offer table (EMI range, rate range, est. max amount, rank rationale), and per-lender expanders showing every gate with required vs actual value, evidence status, source link **with access date**. JSON and CSV export buttons. |
| 🔍 **Lender explorer** | Browse/search the 20 lenders with filters by type, employment segment, and evidence status. Every rule rendered with its threshold, scope, mandatory flag, source link, and assumption notes; unknown/unpublished values shown explicitly as such. |
| 📈 **Research coverage** | Progress toward the 20-lender target, rule counts by evidence status, per-lender research status and last-verified dates, and most-failed gates from the synthetic run — each with its denominator. All synthetic-derived numbers labelled as such. |
| ℹ️ **About & methodology** | Two-layer rules explanation, decision semantics, evidence taxonomy, lender-selection limits, and links into `docs/`. |

---

## Command-line interface

```bash
# Batch of synthetic profiles → JSON, plus regenerate every outputs/ file
PYTHONPATH=src python -m loan_engine.cli \
  --profiles data/test_profiles.json --output data/test_results.json --write-outputs

# Single inline profile (any subset of fields; missing fields become unknowns)
PYTHONPATH=src python -m loan_engine.cli --profile '{
    "applicant_age_years": 30,
    "employment_type": "salaried",
    "monthly_net_income_inr": 90000,
    "requested_loan_amount_inr": 500000,
    "requested_tenure_months": 36,
    "cibil_score": 780,
    "existing_monthly_emi_inr": 5000,
    "current_job_tenure_months": 24
}'

# Change the recommendation preference
PYTHONPATH=src python -m loan_engine.cli --profiles data/test_profiles.json \
  --output data/test_results.json --write-outputs --preference lowest_emi

# Point at a different data directory (e.g. your own curated dataset)
PYTHONPATH=src python -m loan_engine.cli --profiles ... --output ... --data-dir /path/to/data
```

Invalid profiles exit with code 2 and a list of validation errors on stderr; a
successful run exits 0.

---

## Using the engine as a library

The engine is deliberately UI-independent; nothing in `src/loan_engine/` imports
Streamlit.

```python
from pathlib import Path
from loan_engine import data_loader as dl, reporting as rp
from loan_engine import schemas as sc

data = dl.load_all(Path("data"))
profile = sc.ApplicantProfile(
    applicant_age_years=30,
    employment_type="salaried",
    monthly_net_income_inr=90_000,
    requested_loan_amount_inr=500_000,
    requested_tenure_months=36,
    cibil_score=780,
)
result = rp.assess_profile(profile, data["lenders"], data["rules"], data["sources"])
print(result["applicant_outcome"])
for o in result["lender_outcomes"]:
    print(o["lender_name"], o["decision"])
print(result["recommendation"]["summary"])
```

Other useful entry points: `rule_engine.evaluate_all` (per-lender decisions),
`affordability.affordability_scenario` (FOIR/available-EMI maths),
`loan_calculator.emi` / `principal_from_emi` / `max_principal_from_available_emi`
(pure functions, zero-rate handled), `recommendation.recommend` (ranking),
`reporting.sample_predictions` / `rule_failure_analysis` / `research_coverage` (CSV
generation).

---

## Repository layout

```
personal-loan-eligibility-engine/
├── README.md                 ← you are here
├── PLAN.md                   ← original implementation plan (if present in your copy)
├── requirements.txt          ← runtime deps (streamlit, pandas, pydantic) + pytest
├── setup.py                  ← optional `pip install -e .` support
├── .gitignore
├── app.py                    ← Streamlit front-end (thin layer over loan_engine)
├── data/
│   ├── lenders.csv           ← 20 lender rows with regulated entity + research status
│   ├── lender_rules.csv      ← 206 individual rules (one row per rule, never wide tables)
│   ├── source_registry.csv   ← 83 sources with URL, type, publisher, access date
│   ├── input_variables.csv   ← full data dictionary for every applicant variable
│   ├── test_profiles.json    ← 14 synthetic profiles (synthetic=true)
│   └── test_results.json     ← engine output for those profiles (regenerated by CLI)
├── src/loan_engine/
│   ├── schemas.py            ← Pydantic models; evidence taxonomy; decision enums
│   ├── data_loader.py        ← CSV/JSON loading, indexing helpers
│   ├── validation.py         ← profile parsing & validation, helpful error lists
│   ├── feature_engineering.py← derived values (total obligations, income denominator)
│   ├── rule_engine.py        ← Layer A gates + Layer B parameter evaluation
│   ├── affordability.py      ← FOIR, available EMI, what-if scenarios
│   ├── loan_calculator.py    ← EMI, principal-from-EMI, totals (exact formulas)
│   ├── recommendation.py     ← transparent weighted-ranking of GO lenders
│   ├── reporting.py          ← JSON/CSV export; failure & coverage analysis
│   └── cli.py                ← batch runner, output generation, exit codes
├── tests/                    ← 7 test modules (see Testing)
├── outputs/                  ← generated artifacts (CSVs listed above)
├── docs/
│   ├── research_methodology.md
│   ├── data_dictionary.md
│   ├── assumptions.md
│   └── lender_research_notes.md
└── scripts/                  ← utility scripts (empty by default)
```

---

## Testing

14 synthetic profiles exercise the engine end-to-end, and 7 pytest modules cover the
internals:

| Test module | Covers |
|---|---|
| `test_validation.py` | Age bounds, CIBIL range, non-negative amounts, segment fields |
| `test_rule_engine.py` | Every gate operator, boundary values (exactly at min/max), segment scoping, hard-gate failure with other missing fields |
| `test_missing_data.py` | Missing values must not silently pass; unknown/unpublished lenders yield REVIEW_REQUIRED |
| `test_affordability.py` | FOIR computation, zero available EMI, scenario bounds |
| `test_loan_calculator.py` | Zero-interest and ordinary-interest EMI, invalid tenure/rate/income handling, principal-from-EMI round-tripping |
| `test_recommendation.py` | Ranking, tie handling, "no feasible lenders" case |
| `test_dataset_integrity.py` | Schema validity of all CSVs, source-date formats, rule↔source referential integrity, evidence-status vocabulary, 20-lender completeness |

Run: `PYTHONPATH=src python -m pytest -q`

---

## Current research coverage (as of 2026-10-11)

- **20/20 lenders** present in `lenders.csv` — 5 `complete`, 15 `researched`.
- **206 rule rows**; evidence mix: 178 `verified_official`, 14 `verified_secondary`,
  8 `estimated` (each with an explicit `assumption_description`), 6 `not_published`
  (null values, never fabricated cut-offs).
- **83 sources**, each with URL, title, type, publisher, and access date 2026-10-11.
- Notable confirmations: Navi's regulated entity (Navi Finserv Limited) and
  Moneyview's partner-funded model.
- **Known gaps:** applicant-specific pricing and income-based maximum-loan formulas are
  largely unpublished (`NOT_PUBLICLY_DETERMINABLE` / `not_published`); many
  self-employed criteria are not published verbatim. Per-lender detail:
  `docs/lender_research_notes.md`.

---

## Insights from the synthetic run

From the actual engine run over the 14 synthetic profiles (2026-10-11):

- Applicant outcomes: **14 `ELIGIBLE_UNDER_DOCUMENTED_RULES`**.
- Lender decisions: **94 GO · 143 REVIEW_REQUIRED · 43 NO_GO** (out of 280
  profile-lender evaluations).
- The large REVIEW_REQUIRED share is **by design**, not a bug: the engine refuses to
  label a lender GO when a mandatory condition can't be evaluated (data missing or rule
  unpublished). Fabricating passes would make the tool useless as a research artefact.
- Top failed/unresolved gates and full numerators/denominators:
  `outputs/rule_failure_analysis.csv` — e.g. requested-amount caps and minimum
  job-tenure are the most frequent blockers among evaluated gates.
- **These numbers come from synthetic profiles and do not estimate real-world approval
  or rejection rates.**

---

## Worked example

A salaried applicant (age 30, net ₹90k/month, CIBIL 780, job tenure 24 months, existing
EMI ₹5k, requests ₹5 lakh over 36 months):

1. Validation passes; derived fields computed (total obligations ₹5k, income
   denominator ₹90k).
2. Each of 20 lenders evaluated: gates checked against `lender_rules.csv` rows scoped to
   this applicant's segment.
3. Results: 7 GO, 13 REVIEW_REQUIRED (their remaining mandatory conditions are not all
   publicly defined, so the engine won't guess).
4. Recommendation (`balanced`): top offer estimated at ~₹9.9 lakh max, advertised rate
   range endpoints ("starting around 10.5%") with EMI shown as a range, not a single
   fake number. Full trace in `data/test_results.json`.

---

## Assumptions in plain language

All assumptions carry IDs and live in `docs/assumptions.md`; the key ones:

| ID | Assumption | Effect |
|---|---|---|
| `ASSUMPTION-FOIR-DENOMINATOR` | Income denominator = net monthly salary (salaried); documented monthly income (self-employed) | Only affects the *estimator*, never a pass/fail |
| `ASSUMPTION-SCENARIO-FOIR-CAP` | Scenario FOIR caps are model assumptions unless a rule is verified for that lender | Affordability bound labelled as estimate |
| `ASSUMPTION-MONTHLY-RATE` | Annual rate ÷ 12 = monthly rate, nominal reducing balance | Standard convention |
| `ASSUMPTION-RATE-PERSONALISATION` | No derived applicant-specific rates without a published formula | EMI shown as range at advertised endpoints |
| `ASSUMPTION-NO-SILENT-PASS` | Missing data never passes a gate | Causes higher REVIEW_REQUIRED, intentionally |
| `ASSUMPTION-SYNTHETIC-INSIGHTS` | Insights come from synthetic profiles only | Clearly labelled in outputs and UI |

---

## Privacy & data handling

- **No direct identifiers collected**: no PAN, no Aadhaar, no bank account numbers, no
  document uploads.
- Sample profiles are `synthetic=true`; nothing real is stored.
- No database, no persistence, no telemetry. Everything stays in CSV/JSON you control.
- If persistence is ever added, it will be opt-in and documented separately.

---

## Limitations

- **No internal rules**: lenders apply credit-policy overlays, risk-based pricing, and
  application-specific discretion that are not public. This engine models only what is
  published.
- **No approval dataset**: nothing here was trained on approved/rejected applications,
  and synthetic insights say nothing about real-world approval rates.
- **No guaranteed approval**: even a clean GO across all 20 lenders is an estimate under
  documented public rules, nothing more.
- **Rates are not personalised**: without a published deterministic pricing formula,
  applicant-specific rates are `NOT_PUBLICLY_DETERMINABLE`; EMIs use advertised
  range endpoints (see `ASSUMPTION-RATE-PERSONALISATION`).
- **Data ages**: lender pages change. Access dates are recorded per source; re-verify
  against the current official page before making a real decision.
- **Uneven coverage**: some lenders publish far more than others; coverage status and
  per-lender gaps are shown honestly (`docs/lender_research_notes.md`).

---

## Future work

- **Live re-verification**: scripted re-fetching of all 83 sources with new access dates
  and change detection.
- **Self-employed coverage**: most self-employed criteria are unpublished; more
  official-document research (ITR-based programs, GST-based programs) would improve
  segment coverage.
- **Optional persistence**: opt-in, documented storage if real applicant data is ever
  introduced (not the case today).
- **API surface**: an optional read-only FastAPI wrapper mirroring the CLI — only if a
  real integration need appears.
- **Data-quality dashboard**: automated weekly drift check between stored rule values
  and the live official pages.

---

## Documentation map

- `docs/research_methodology.md` — how sources were found, graded, dated, and conflicts resolved
- `docs/data_dictionary.md` — every applicant variable and every rule/source field
- `docs/assumptions.md` — every model assumption with ID, rationale, effect, status
- `docs/lender_research_notes.md` — per-lender coverage and explicit gap list
- `outputs/research_coverage.csv` — machine-readable per-lender coverage
- `outputs/rule_failure_analysis.csv` — most-failed gates with full denominators
- `outputs/sample_predictions.csv` — one row per (profile × lender)
