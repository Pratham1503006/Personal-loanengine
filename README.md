# INDIA-LENS
### Transparent Documented-Rules Eligibility & Recommendation Engine for Indian Personal Loans

<p align="left">
  <a href="#9-client-side-html-frontend-indexhtml">
    <img src="https://img.shields.io/badge/OPEN_THE_UI-Dependency--Free_HTML/JS-007AFF?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=003d80" alt="Open the client-side UI" height="36"/>
  </a>
</p>

![Coverage](https://img.shields.io/badge/Coverage-20_Indian_Lenders-111116?style=flat-square)
![Data Integrity](https://img.shields.io/badge/Data-100%25_Public_/_Fully_Sourced-111116?style=flat-square)
![Transparency](https://img.shields.io/badge/Evidence-6--Level_Taxonomy_/_Access_Dated-111116?style=flat-square)
![Engine](https://img.shields.io/badge/Model-Deterministic_2--Layer_Rules-111116?style=flat-square)
![Testing](https://img.shields.io/badge/Tests-7_Modules_/_14_Profiles-111116?style=flat-square)

A **transparent, rule-based** (no machine learning) personal-loan eligibility and
recommendation engine for India. It evaluates an applicant profile against
**publicly documented underwriting rules** for 20 lenders, then ranks feasible
lenders with a full, auditable explanation — every threshold linked to its
official source URL and access date.

**Why this project exists.** Lenders advertise headline numbers (age, starting
salary, rate from 9.99%) but almost never publish how their criteria *combine*.
Existing "eligibility checkers" hide their logic behind an opaque score. This
project takes the opposite approach: **every rule is a visible row in a CSV,
every threshold carries its source URL and access date, and any unknown is
shown as unknown rather than guessed.**

> **Disclaimer:** Educational/research tool. Passing documented public criteria
> is **not** an approval promise and this is not financial advice. Lenders
> apply internal policies that are not public.

---

## Table of Contents
1. [Problem Statement & Scope](#1-problem-statement--scope)
2. [Lender Universe & Selection Methodology](#2-lender-universe--selection-methodology)
3. [Two-Layer Decision Engine](#3-two-layer-decision-engine)
4. [Master Public Rule Base](#4-master-public-rule-base)
5. [Notable Findings from Official-Source Research](#5-notable-findings-from-official-source-research)
6. [Evidence Taxonomy & Research Method](#6-evidence-taxonomy--research-method)
7. [Decision Semantics & Safety Rules](#7-decision-semantics--safety-rules)
8. [Repository Structure & Local Execution](#8-repository-structure--local-execution)
9. [Using the Streamlit App](#9-using-the-streamlit-app)
10. [Command-Line Interface & Library Usage](#10-command-line-interface--library-usage)
11. [Test Suite — 14 Edge-Case Profiles](#11-test-suite--14-edge-case-profiles)
12. [Empirical Insights & Gate-Failure Pareto](#12-empirical-insights--gate-failure-pareto)
13. [Current Research Coverage](#13-current-research-coverage)
14. [Worked Example](#14-worked-example)
15. [Assumptions in Plain Language](#15-assumptions-in-plain-language)
16. [Privacy & Data Handling](#16-privacy--data-handling)
17. [Limitations](#17-limitations)
18. [Future Roadmap](#18-future-roadmap)

> UI note: this project now ships a **dependency-free client-side frontend**
> ([`index.html`](index.html)) that mirrors the Python engine semantically —
> verified equal to the Python engine on all 14 test profiles (0 mismatches
> across 280 evaluations). The Streamlit app (`app.py`) remains in-repo but is
> no longer the primary interface; see [section 9](#9-client-side-html-frontend-indexhtml).

---

## 1. Problem Statement & Scope

When a retail borrower in India asks *"Can I get a personal loan, and from
whom?"*, the true determinants of approval — **FOIR caps, take-home pay
retention floors, bureau cut-offs, employer tiers, job-tenure gates** — are
scattered across product pages, FAQs, rate disclosures and schedules of
charges. This project consolidates exactly those public rules into an
auditable, deterministic engine.

| | |
|---|---|
| **Product Scope** | Unsecured personal loans only. Home, auto, gold and business loans are out of scope. |
| **Coverage Scope** | 20 lenders across banks, NBFCs and digital platforms. |
| **Data Provenance** | 100% public, verified sources (83 registered sources). No logins, no protected-portal scraping, no customer PII. |
| **Temporal Provenance** | Every source carries its actual access date (**2026-10-11** for all current sources). |
| **Model Type** | Deterministic two-layer rule scorecard. No ML black boxes — no public negative-label outcome data exists. |

---

## 2. Lender Universe & Selection Methodology

20 lenders were selected for market relevance, category diversity
(banks / NBFCs / digital platforms) and public-information availability —
deliberately **not** a definitive industry ranking.

| Lender | Product | Category | Research Status | Regulated Entity / Note |
|:---|:---|:---|:---:|:---|
| HDFC Bank | HDFC Bank Personal Loan | Bank | `researched` | — |
| ICICI Bank | ICICI Bank Personal Loan | Bank | `researched` | — |
| State Bank of India | SBI Personal Loan (Xpress Credit) | Bank | `researched` | — |
| Axis Bank | Axis Bank Personal Loan | Bank | `researched` | — |
| Kotak Mahindra Bank | Kotak Personal Loan | Bank | `researched` | — |
| IDFC FIRST Bank | FIRSTmoney Personal Loan | Bank | `researched` | — |
| IndusInd Bank | IndusInd Bank Personal Loan | Bank | `researched` | Served via INDIE digital channel |
| YES BANK | YES BANK Personal Loan | Bank | `researched` | ⚠ No official HTML page; official Schedule-of-Charges PDF only |
| Federal Bank | FedPremia Personal Loan | Bank | `researched` | Main page bot-blocked; content cross-verified |
| Bank of Baroda | Baroda Personal Loan | Bank | `researched` | — |
| Punjab National Bank | PNB Personal Loan (Public / Self-Employed) | Bank | `researched` | Priced off 1-yr MCLR + spread |
| Canara Bank | Canara Budget (Prime / Delight) | Bank | `researched` | — |
| Bajaj Finance | Bajaj Finance Personal Loan | NBFC | `researched` | — |
| Tata Capital | Tata Capital Personal Loan | NBFC | `researched` | — |
| Aditya Birla Finance | Aditya Birla Capital Personal Loan | NBFC | `researched` | — |
| L&T Finance | L&T Finance Personal Loan | NBFC | `complete` | — |
| Poonawalla Fincorp | Poonawalla Fincorp Personal Loan | NBFC | `complete` | — |
| SMFG India Credit | SMFG India Credit Personal Loan | NBFC | `complete` | formerly Fullerton India |
| Navi | Navi Personal Loan / Cash Loan | NBFC | `complete` | Direct lender: **Navi Finserv Ltd** (RBI NBFC, CIN U65923KA2012PLC062537) |
| Moneyview | Moneyview Personal Loan | Digital platform | `complete` | Platform — loans funded by partners (Whizdm Finance Pvt Ltd, SMFG India Credit) |

**Selected-method limitation:** smaller banks, captive NBFCs and
credit-card-fintech lenders are under-represented; no attempt was made to rank
lenders by size or approval friendliness.

---

## 3. Two-Layer Decision Engine

The engine deliberately splits its thinking into two layers so that hard facts
and soft estimates **never blur together**.

### Layer A — Go/No-Go gates
Mandatory, **verified** hard rules (minimum age, minimum CIBIL, maximum
requested amount, …). If one fails → the lender is `NO_GO`, with the failed
gate, required threshold, and your actual value shown side by side, plus the
source link.

### Layer B — Parameter-based evaluation
Everything that shapes an offer but should not automatically reject: bureau
signals, income/ITR adequacy, employment stability, affordability (FOIR),
loan-amount fit, pricing bands, tenure, fees, documentation.

### What you get for each lender
- Failed / unresolved / passed gates with required vs actual value, evidence
  status, source URL and access date (expandable in the UI).
- Estimated maximum loan amount (product max ∩ income-based limit ∩
  affordability limit, where each bound is known).
- Advertised rate ranges and EMI scenarios **at the range endpoints** — never
  a fabricated applicant-specific rate.
- What remains unknown — stated as unknown, not zero.

---

## 4. Master Public Rule Base

The complete dataset lives in
[`data/lender_rules.csv`](data/lender_rules.csv) — **206 individual rule rows**
(one row per rule, never wide tables), every parameter anchored to official
URLs with retrieval timestamps via
[`data/source_registry.csv`](data/source_registry.csv) (**83 sources**).

Headline verified parameters per lender (all verified against official pages
on **2026-10-11** unless marked otherwise):

| Lender | Verified Key Criteria (from official sources) | Age | Min Income | CIBIL | Rate Band | Tenure |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| IDFC FIRST Bank (FIRSTmoney) | Loan up to ₹15 L; PF 0–3.5%; min salary ₹10,000 | 21–60 | ₹10k/mo | 710 (SE 760) | 9.99%–20% | 9–60m |
| IndusInd Bank (INDIE) | Online loan ₹30k–₹5 L; instant variant tenure 12–48m; from 10.49% p.a. | 21–60 (SAL) / 25–65 (SE) | ₹25k/mo (SAL) / ₹4.8 L/yr (SE) | 730+ | 10.49%–31.50% APR | 12–84m |
| YES BANK | Loan ₹1–40 L; PF up to 2.50% (official PDF); rest secondary-sourced | 22–58* | ₹25k/mo | 700+* | 10.85%–21%* | 12–60m* |
| Federal Bank (FedPremia) | Net salary ₹25k+; 3 yrs experience; 3 yrs current job; city page up to ₹25 L | 21–55/60 | ₹25k/mo | not published | 11.75%–18.99% | up to 60m |
| Bank of Baroda | Loan ₹1–20 L; 1 yr continuous service/business; PF 1–2% (NIL for Govt salary acct) | 21–60/65 | — | 701+* | 10.15%–18.00% | 12–84m |
| Punjab National Bank | Salaried up to 24× gross monthly salary (max ₹20 L); SE up to 10× (max ₹5 L); off MCLR | 21–60/65 | — | 750+ (SE path) | MCLR+1.25% | up to 72 EMIs |
| Canara Bank (Budget) | Quantum = 25 months' gross salary — Prime max ₹50 L / Delight ₹40 L; NTHP ≥25% or ₹10k; PF 0.50% | — | — | — | on separate ROI page | up to 84m |
| Bajaj Finance | Loan ₹40k–₹55 L; ≤80 at end of tenure; PF up to 4.13% incl. taxes | 21–80 | — | 650+ | 10%–30.5% | 12–108m |
| Tata Capital | Loan up to ₹35 L; 1 yr current job / 2 yrs total; PF up to 5% + GST | 21–58 | ₹20k/mo | ideal 700+, best 750+ | from 10.99% | up to 72m |
| Aditya Birla Finance | Loan up to ₹50 L; PF 1.5%–4%; tenure 1–7 yrs | 21/23–60 | — | 700+ | from 10.99% | 12–84m |
| L&T Finance | Loan up to ₹30 L; PF up to 4%; metro ₹25k vs tier-2/3 ₹15k income floor | 21–58 | ₹15k–25k/mo | 700+ (750+ preferred) | from 10.50% | 12–72m |
| Poonawalla Fincorp | Loan ₹1–50 L; min take-home ₹30k/mo; 1 yr exp / 1 mo current job; PF up to 4% | 21–60 | ₹30k/mo | 750+ ideal | from 9.99% | 12–84m |
| SMFG India Credit | Salaried 24–60, ₹25,001+ (₹16k other cities); SE 25–65, 3-yr business; PF up to 3.75% + GST | 24–60 (SE 25–65) | ₹16k–25k/mo | 700+ | 12.5%–30% | 12–60m |
| Navi (Navi Finserv) | Annual household income > ₹3 L (official T&C); rate policy max 26%; tiered PF | 18–65* | ~₹25k/mo* | 650+* | up to 26% (policy) | 12–60m* |
| Moneyview (partner-funded) | Loan ₹5k–₹10 L; min in-hand ₹25k/mo; CIBIL 650+; APR 17–45% | 21–57 | ₹25k/mo | 650+ | 14%–36%/mo 1.16%+ | 3–60m |

\* = values from `verified_secondary` aggregators, never presented as official.

> SBI, HDFC, ICICI, Axis and Kotak publish fragmented criteria (several
> thresholds not numerically published) — their rule rows carry probe-level
> details with explicit `not_published` status rather than invented numbers.
> Full per-lender dossiers: [`docs/lender_research_notes.md`](docs/lender_research_notes.md).

---

## 5. Notable Findings from Official-Source Research

Rules that broker sites routinely mis-state, verified directly against the
lender's own pages and documents:

### 1. PNB prices off MCLR thresholds — not a single headline rate
* **Commonly stated:** "PNB personal loans from ~10.5%"
* **Official:** interest is **1-year MCLR + spread** (MCLR 9.10% w.e.f.
  01.10.2026; retail table shows +1.25% / +2.00%), with a **1.00% processing
  fee, NIL for Defence personnel**. Salaried quantum: up to **24× gross
  monthly salary**, capped at ₹20 L.
* **Source:** [`pnb.bank.in` MCLR table](https://pnb.bank.in/interst-rate-on-advances-linked-to-mclr.html)

### 2. Canara Bank: quantum is *25 months of gross salary*, not a flat amount
* **Derived rule:** Quantum = 25 × gross monthly salary (Prime max ₹50 L /
  Delight ₹40 L), tenure to 84 months, **net take-home pay (NTHP) ≥ 25% or
  ₹10,000, whichever is higher**, PF 0.50% (min ₹1,000 / max ₹5,000).

### 3. Navi lends directly — and publishes an internal rate *policy*
* Regulated entity confirmed as **Navi Finserv Limited** (RBI-registered
  NBFC-ICC-ML, Reg. N-02.00270). Its published **Interest Rate Policy**
  (official PDF, June 2025) discloses a **26% p.a. maximum** and tiered
  processing fees (up to 2% for loans ≥ ₹2 L capped ₹10k; up to 4% below that,
  capped ₹4k) + 18% GST — far more granular than most "up to X%" marketing.

### 4. Moneyview broker vs lender distinction
* Loans are evaluated and disbursed by **partner banks/NBFCs** (Whizdm Finance
  Pvt Ltd, SMFG India Credit) — its published eligibility reflects
  *partner-lender* criteria, with an unusually wide disclosed APR band
  (**17%–45%**). Modelled as a `digital_platform`, not a direct lender.

### 5. Proof that `not_published` ≠ "no rule"
SBI publishes **no headline CIBIL cut-off**; Federal Bank publishes **no CIBIL
minimum**. The dataset stores these as `not_published` (value = null) instead
of an invented 700 — so the engine never masks a real gate behind a guess.

---

## 6. Evidence Taxonomy & Research Method

Every rule row carries one of these evidence statuses:

| Status | Meaning | Treated as a hard gate? |
|:---|:---|:---:|
| `verified_official` | Directly supported by a current official lender/regulatory source | **Yes** |
| `verified_secondary` | Credible comparison source, not confirmed officially | No |
| `estimated` | Model assumption, flagged with `assumption_description` | No |
| `not_published` | Researched; lender genuinely doesn't publish it (value = null) | No (unevaluable) |
| `not_researched` | Research incomplete (value = null) | No (unevaluable) |
| `unverified` / `stale` | Source exists but couldn't be validated / may be outdated | No |

**Search order** (full method: [`docs/research_methodology.md`](docs/research_methodology.md)):

1. Official lender pages — product, eligibility, rates & fees, calculator, FAQs, terms.
2. Official PDFs and product documents linked from those pages.
3. RBI material — regulatory context only; a general RBI rule is **never**
   recorded as a lender-specific underwriting rule.
4. Reputable comparison sites — discovery/cross-check only, always labelled secondary.
5. Search snippets are never sole evidence when the actual page can be opened.
   Paywalls, logins and anti-bot controls are never bypassed.

Conflicts between sources are resolved in favour of the official page and
noted per rule (e.g., Tata Capital's ₹15,000 eligibility-calculator minimum vs
₹20,000 product-page minimum — product page modelled, conflict recorded).

---

## 7. Decision Semantics & Safety Rules

| Decision | Meaning |
|:---|:---|
| 🟢 `GO` | All applicable, researched, mandatory gates are evaluable **and** pass. A coverage warning is always shown — public rule data is never complete. |
| 🔴 `NO_GO` | At least one **verified mandatory** hard gate failed. |
| 🟡 `REVIEW_REQUIRED` | No gate failed, but the evaluation is blocked: applicant data missing, a rule is unpublished, or a rule hasn't been researched. |

Per applicant (aggregated over all lenders): `ELIGIBLE_UNDER_DOCUMENTED_RULES` ·
`NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES` · `INSUFFICIENT_INFORMATION`.

**Safety rules built into the decision logic:**

- A missing value **never silently passes** a gate; it makes the gate unevaluable.
- Secondary, estimated and unknown rules are **never treated** as verified hard gates.
- No fabricated thresholds: an unpublished minimum CIBIL is stored as
  **null with status `not_published`** — not an invented 700, not zero.
- If no lender reaches GO, the engine **refuses to manufacture a
  recommendation** and says so.

### The recommendation layer
For GO lenders, a transparent weighted comparison produces ranked "estimated
offers" under four user-switchable preferences:
`lowest_estimated_cost` · `lowest_emi` · `highest_estimated_amount` ·
`balanced`. There is **no opaque "approval probability"** and no implied "best
lender for everyone". `NO_GO` lenders are excluded from offers;
`REVIEW_REQUIRED` lenders are shown in a separate "needs more information"
group, never as confirmed matches.

---

## 8. Repository Structure & Local Execution

```
personal-loan-eligibility-engine/
├── app.py                    ← Streamlit front-end (optional; kept for parity)
├── index.html                ← dependency-free client-side UI (dark terminal style, drawer rule-audit)
├── requirements.txt          ← runtime deps (streamlit, pandas, pydantic) + pytest
├── setup.py                  ← optional `pip install -e .` support
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
├── scripts/
│   ├── build_frontend_data.py ← regenerates scripts/frontend_data.js and syncs index.html's embedded data
│   └── frontend_data.js      ← auto-generated data blob (do not edit)
├── tests/                    ← 7 test modules
├── outputs/                  ← generated artifacts (CSVs listed below)
├── docs/
│   ├── research_methodology.md
│   ├── data_dictionary.md
│   ├── assumptions.md
│   └── lender_research_notes.md
└── scripts/                  ← utility scripts (empty by default)
```

### How to Run Locally

Requires Python 3.11+.

```bash
# 1. Clone
git clone <this-repo-url>
cd personal-loan-eligibility-engine

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash (or .venv/bin/activate on Linux/macOS)

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .                   # optional: makes `import loan_engine` work everywhere

# 3. Launch the client-side HTML frontend
start index.html                 # Windows (or: open index.html on macOS/Linux)
# → opens the dependency-free decisioning UI directly in your browser

# 4. Run the test suite (7 test modules)
PYTHONPATH=src python -m pytest -q

# 5. Generate all sample outputs from the 14 synthetic profiles
PYTHONPATH=src python -m loan_engine.cli \
  --profiles data/test_profiles.json --output data/test_results.json --write-outputs
```

All commands work from the repository root. With `pip install -e .` installed,
drop the `PYTHONPATH=src` prefix.

`--write-outputs` regenerates four files **from the current code and data**
(never hand-written predictions):

| File | Contents |
|:---|:---|
| `data/test_results.json` | Full per-profile engine results: profile, validation, derived features, affordability scenario, per-lender decisions, gate details, recommendation |
| `outputs/sample_predictions.csv` | One row per (profile × lender): decision, gate counts, EMI/rate/amount estimates where available |
| `outputs/rule_failure_analysis.csv` | Which rules failed most often across profiles, with numerator (`failures`) and denominator (`evaluations`) |
| `outputs/research_coverage.csv` | Per-lender rule counts by evidence status, source counts, last access dates |

---

## 9. Client-Side HTML Frontend (`index.html`)

The primary UI is now a **single self-contained `index.html`** — HTML + CSS +
vanilla JS, no framework, no server, no build step. Open it directly from disk
(`file://`) or serve it statically; everything runs in your browser.

- **Zero install:** no Python needed to *use* the UI. Python is only needed to
  regenerate the embedded data when the research dataset changes.
- **Data embedded:** the full rulebase (206 rules, 20 lenders, 83 sources) is
  inlined at build time into the `index.html` file by
  `scripts/build_frontend_data.py`.
- **Rules evaluated client-side**, semantically mirroring `rule_engine.py`:
  segment scoping, blocking-type detection, verified-official gate enforcement,
  not-published handling, missing-data-never-passes semantics and the 50%
  scenario-FOIR affordability estimate (noticeably labelled as an assumption).
- **Same decision semantics:** `GO` / `REVIEW_REQUIRED` / `NO_GO` per lender,
  aggregated applicant outcome, and the same coverage-warning logic.
- **Recommended-offer estimation** (IDFC FIRST, BoB, Bajaj, Tata, Poonawalla,
  SMFG, Aditya Birla and Moneyview have publicly evaluable lanes) using the
  same range-endpoint EMI maths as the Python engine.

### Tabs / interactive surface

The UI is organised as a single dark terminal-style scoring page (Inter +
JetBrains Mono, subtle animated particle mesh) rather than tab panels:

| Section | What it does |
|:---|:---|
| 🧾 **Applicant dossier** | Grouped inputs: income, obligations, request, CIBIL (blank = unknown), segment-aware employment fields. Every keystroke re-evaluates all 20 lenders live (no submit button needed). |
| 🎛 **Sizing scorecard** | Real-time summary: total obligations, income denominator, current FOIR, available-EMI estimate, FOIR/EMI equation card, and the giant N/20 GO callout. |
| 📊 **20-lender decision matrix** | Waterfall of PASS · GO / FAIL · NO_GO / REVIEW_REQ badges per lender, with failed/unevaluable gate counts and a `LOWEST PUBLISHED ROA` highlight on the cheapest GO lender; category filter tabs (banks / NBFCs / digital). |
| 🔎 **Rule audit drawer** | Click any lender row to open a modal listing every applicable rule — failed verified gates, unevaluable mandatory rules, soft flags and passed gates — each with operator, required vs actual value, evidence-status tag and its official source link with access date. |
| 🎯 **Benchmark profiles** | 14 Python-verified synthetic profiles (under-age, subprime bureau, debt crunch, self-employed ITR, near-retirement edge cases) — one click loads each into the dossier. |

### One-command rebuild after data changes

```bash
python scripts/build_frontend_data.py
# → regenerates scripts/frontend_data.js and re-injects it into index.html
#   (idempotent: replaces the previous auto-generated <script> block)
```

> **Verification note:** the embedded JS evaluator was cross-checked against
> the Python engine on all 14 test profiles — **280/280 lender-evaluations
> produce identical GO / REVIEW_REQUIRED / NO_GO distributions.** The page was
> additionally smoke-tested in headless Chrome (no console errors, 20/20
> lender rows, correct 13/20 GO on the default dossier, working drawer audit).
> A rendered preview lives at `docs/index_preview.png`.

> **About the old Streamlit app:** `app.py` still exists in the repo (it works
> if you prefer an interactive Python session) but is no longer the built-in
> demo path. The README's previous five-tab Streamlit section has been replaced
> by this one.

---

## 10. Command-Line Interface & Library Usage

### CLI

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

### Library

The engine is deliberately UI-independent; nothing in `src/loan_engine/`
imports Streamlit.

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
`reporting.sample_predictions` / `rule_failure_analysis` / `research_coverage`
(CSV generation).

---

## 11. Test Suite — 14 Edge-Case Profiles

14 synthetic profiles exercise the engine end-to-end (**280 profile × lender
evaluations**), and 7 pytest modules cover the internals:

| Test module | Covers |
|:---|:---|
| `test_validation.py` | Age bounds, CIBIL range, non-negative amounts, segment fields |
| `test_rule_engine.py` | Every gate operator, boundary values (exactly at min/max), segment scoping, hard-gate failure with other missing fields |
| `test_missing_data.py` | Missing values must not silently pass; unknown/unpublished lenders yield REVIEW_REQUIRED |
| `test_affordability.py` | FOIR computation, zero available EMI, scenario bounds |
| `test_loan_calculator.py` | Zero-interest and ordinary-interest EMI, invalid tenure/rate/income handling, principal-from-EMI round-tripping |
| `test_recommendation.py` | Ranking, tie handling, "no feasible lenders" case |
| `test_dataset_integrity.py` | Schema validity of all CSVs, source-date formats, rule↔source referential integrity, evidence-status vocabulary, 20-lender completeness |

Run: `PYTHONPATH=src python -m pytest -q`

### Profile Edge Cases (from the actual engine run, 2026-10-11)

High-determination inputs shown; **"GO" means every researched mandatory gate
passed — the remaining lenders are mostly REVIEW_REQUIRED (incomplete public
rules), not rejections**:

| Profile | Edge Case Tested | Age | Emp | Net Income | CIBIL | Req. Amt | GO Count |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `profile_001` | Baseline prime salaried | 32 | salaried | ₹60,000 | 775 | ₹8 L | **12 / 20** |
| `profile_002` | Income-floor boundary | 28 | salaried | ₹25,000 | 725 | ₹4 L | 12 |
| `profile_003` | Subprime bureau (620) | 30 | salaried | ₹50,000 | 620 | ₹5 L | 8 |
| `profile_004` | Debt crunch — ₹35k EMI on ₹40k income | 35 | salaried | ₹40,000 | 750 | ₹3 L | 6 |
| `profile_005` | Low income + mid CIBIL | 26 | salaried | ₹35,000 | 750 | ₹3 L | 8 |
| `profile_006` | Self-employed, no salaried income fields | 38 | self-emp | ITR path | 760 | ₹7 L | 8 |
| `profile_007` | Below minimum age (17) | 17 | salaried | ₹30,000 | 750 | ₹2 L | **1 / 20** |
| `profile_008` | Age at maturity edge (59, 12m tenure) | 59 | salaried | ₹80,000 | 780 | ₹10 L | 5 |
| `profile_009` | CIBIL missing entirely | 31 | salaried | ₹45,000 | unknown | ₹4 L | 2 |
| `profile_010` | Self-employed, CIBIL 740 | 30 | self-emp | ITR path | 740 | ₹3 L | 7 |
| `profile_011` | Bureau boundary (650) | 29 | salaried | ₹50,000 | 650 | ₹2.5 L | 4 |
| `profile_012` | Max requested amount (₹80 L) breach test | 40 | salaried | ₹2,00,000 | 820 | **₹80 L** | 3 |
| `profile_013` | Self-employed, small ticket | 36 | self-emp | ITR path | 720 | ₹2 L | 7 |
| `profile_014` | Near retirement (58) + floor income | 58 | salaried | ₹30,000 | 725 | ₹5 L | 11 |

The large REVIEW_REQUIRED share is **by design**: the engine refuses to label a
lender GO when a mandatory condition can't be evaluated. Fabricating passes
would make the tool useless as a research artefact. Full trace:
`data/test_results.json`; machine-readable matrix: `outputs/sample_predictions.csv`.

---

## 12. Empirical Insights & Gate-Failure Pareto

From the actual engine run over the 14 synthetic profiles (2026-10-11):
**94 GO · 143 REVIEW_REQUIRED · 43 NO_GO** across 280 profile-lender
evaluations, with **46 mandatory-gate failures over 137 evaluated gate
slots** (33.6% failure rate). Aggregation of `outputs/rule_failure_analysis.csv`
(full numerators and denominators there):

| Failure Trigger | Failures / Evaluated | Lenders with Evaluated Key Rules |
|:---|:---:|:---|
| **Age bounds (min / max)** | **14 / 14** | 9 — every breached age or maturity cap (Federal, Moneyview, …) fails cleanly; no lender misses a breached age |
| **Requested loan amount out of product band** | **12 / 12** | 8 — IndusInd ₹30k–₹5 L instant band, IDFC ₹15 L, Federal/BoB/PNB/Bajaj/Tata/Aditya Birla caps — every shaped product cap binds exactly |
| **Credit-score gate (CIBIL)** | **10 / 15** | 6 — 710+ (IDFC salaried), 730+ (IndusInd), 700+ (SMFG), 750+ (PNB self-emp path); 5 of 15 evaluated profiles passed |
| **Current job tenure** | **6 / 36** | 5 — Federal Bank's 3-yr current-job rule (3/9) is the strictest; BoB/Tata at ~1 month are the loosest |
| **Self-employed ITR income gate** | **2 / 13** | 3 — IndusInd ₹4.8 L/yr and PNB ₹6 L/yr paths bind on low-ITR profiles |
| **Requested tenure out of range** | **2 / 2** | 1 — IndusInd's 12–48m online band |
| **Monthly income floors** | 0 / 6 | 2 — no evaluated income floor (Tata, Moneyview) banned any profile in this suite |
| **Total work experience** | 0 / 39 | 6 — never bound in this suite |

**Key underwriting insights:**

1. **Age and product caps bite hardest.** All 14 evaluated age breaches
   (including the 17-year-old and near-retirement profiles) and all 12
   evaluated loan-amount breaches failed cleanly — the engine never lets a
   band violation slip. IndusInd's ₹30,000–₹5,00,000 instant-loan band alone
   caused 4/4 failures for a single ₹8 L ask: headline "up to ₹50 L"
   marketing coexists with much tighter digital-channel bands.
2. **The bureau spread is real.** Verified CIBIL cut-offs span **650 (Bajaj,
   Moneyview) → 701 (BoB) → 710 (IDFC) → 730 (IndusInd) → 750+ (PNB
   self-employed)**. The same CIBIL 620 profile passes SMFG India Credit while
   failing every bank bureau gate that was evaluable in that run.
3. **Job-tenure gates are asymmetric.** Federal Bank demands 3 years in the
   current job; Bank of Baroda and Tata Capital require as little as 1 month —
   the same applicant can pass one bank and fail another on tenure alone.
4. **Income floors rarely bind here** (0/6 failures) — but only because the
   strictest ones (₹25k–₹30k at IDFC, IndusInd, Poonawalla) sit at lenders
   whose gates were mostly unevaluable in the suite. Absence of failure is a
   coverage artefact, not an approval pattern.
5. **Large REVIEW_REQUIRED share is by design, not a bug.** Many thresholds
   (notably SBI/HDFC/ICICI/Axis/Kotak numeric gates) are simply not published —
   the engine flags rather than fabricates.

> ⚠ **These numbers come from synthetic profiles and do not estimate
> real-world approval or rejection rates.**

---

## 13. Current Research Coverage

As of **2026-10-11**:

- **20/20 lenders** present in `lenders.csv` — 5 `complete`, 15 `researched`.
- **206 rule rows**; evidence mix: **178 `verified_official`, 14
  `verified_secondary`, 8 `estimated`** (each with an explicit
  `assumption_description`), **6 `not_published`** (null values, never
  fabricated cut-offs).
- **83 sources**, each with URL, title, type, publisher, and access date.
- Notable confirmations: Navi's regulated entity (Navi Finserv Limited) and
  Moneyview's partner-funded model.
- **Known gaps:** applicant-specific pricing and income-based maximum-loan
  formulas are largely unpublished (`NOT_PUBLICLY_DETERMINABLE` /
  `not_published`); many self-employed criteria are not published verbatim.
  Per-lender detail: [`docs/lender_research_notes.md`](docs/lender_research_notes.md).

---

## 14. Worked Example

A salaried applicant (age 30, net ₹90k/month, CIBIL 780, job tenure 24 months,
existing EMI ₹5k, requests ₹5 lakh over 36 months):

1. Validation passes; derived fields computed (total obligations ₹5k, income
   denominator ₹90k).
2. Each of 20 lenders evaluated: gates checked against `lender_rules.csv` rows
   scoped to this applicant's segment.
3. Results (verified by running the engine): 7 GO, 12 REVIEW_REQUIRED, 1
   NO_GO (the remaining mandatory conditions of the REVIEW_REQUIRED lenders
   are not publicly defined, so the engine won't guess).
4. Recommendation (`balanced`): top offer is IDFC FIRST Bank (FIRSTmoney) —
   estimated max ~₹10.76 lakh, EMI range ~₹16,131 (at 9.99%) to ~₹18,582 (at
   20%) for the ₹5 L / 36-month ask, processing fee 0%–3.5%. Applicant-specific
   rate status: `NOT_PUBLICLY_DETERMINABLE` — EMI shown as a range, not a
   single fake number. Full trace: `data/test_results.json` regeneration and
   the library snippet above.

---

## 15. Assumptions in Plain Language

All assumptions carry IDs and live in [`docs/assumptions.md`](docs/assumptions.md); the key ones:

| ID | Assumption | Effect |
|:---|:---|:---|
| `ASSUMPTION-FOIR-DENOMINATOR` | Income denominator = net monthly salary (salaried); documented monthly income (self-employed) | Only affects the *estimator*, never a pass/fail |
| `ASSUMPTION-SCENARIO-FOIR-CAP` | Scenario FOIR caps are model assumptions unless a rule is verified for that lender | Affordability bound labelled as estimate |
| `ASSUMPTION-MONTHLY-RATE` | Annual rate ÷ 12 = monthly rate, nominal reducing balance | Standard convention |
| `ASSUMPTION-RATE-PERSONALISATION` | No derived applicant-specific rates without a published formula | EMI shown as range at advertised endpoints |
| `ASSUMPTION-NO-SILENT-PASS` | Missing data never passes a gate | Causes higher REVIEW_REQUIRED, intentionally |
| `ASSUMPTION-SYNTHETIC-INSIGHTS` | Insights come from synthetic profiles only | Clearly labelled in outputs and UI |

---

## 16. Privacy & Data Handling

- **No direct identifiers collected**: no PAN, no Aadhaar, no bank account
  numbers, no document uploads.
- Sample profiles are `synthetic=true`; nothing real is stored.
- The HTML frontend is fully client-side: no network calls, no cookies, no
  analytics — your inputs never leave the browser tab.
- No database, no persistence, no telemetry. Everything stays in CSV/JSON you
  control.
- If persistence is ever added, it will be opt-in and documented separately.

---

## 17. Limitations

- **No internal rules**: lenders apply credit-policy overlays, risk-based
  pricing and application-specific discretion that are not public. This engine
  models only what is published.
- **No approval dataset**: nothing here was trained on approved/rejected
  applications, and synthetic insights say nothing about real-world approval rates.
- **No guaranteed approval**: even a clean GO across all 20 lenders is an
  estimate under documented public rules, nothing more.
- **Rates are not personalised**: without a published deterministic pricing
  formula, applicant-specific rates are `NOT_PUBLICLY_DETERMINABLE`; EMIs use
  advertised range endpoints (see `ASSUMPTION-RATE-PERSONALISATION`).
- **Data ages**: lender pages change. Access dates are recorded per source;
  re-verify against the current official page before making a real decision.
- **Uneven coverage**: some lenders publish far more than others; coverage
  status and per-lender gaps are shown honestly
  ([`docs/lender_research_notes.md`](docs/lender_research_notes.md)).

---

## 18. Future Roadmap

- **Live re-verification**: scripted re-fetching of all 83 sources with new
  access dates and change detection.
- **Rule-coverage expansion**: deepening the `not_researched` rules — the
  biggest source of REVIEW_REQUIRED noise in the UI.
- **Self-employed coverage**: most self-employed criteria are unpublished;
  more official-document research (ITR-based, GST-based programs) would improve
  segment coverage.
- **HTML frontend enhancements**: JSON export of a session's results, an
  algebraic "what changed?" diff between two runs, and optional PWA/offline
  descriptor.
- **Optional persistence**: opt-in, documented storage if real applicant data
  is ever introduced (not the case today).
- **API surface**: an optional read-only FastAPI wrapper mirroring the CLI —
  only if a real integration need appears.

---

## Documentation Map

- [`docs/research_methodology.md`](docs/research_methodology.md) — how sources were found, graded, dated and conflicts resolved
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — every applicant variable and every rule/source field
- [`docs/assumptions.md`](docs/assumptions.md) — every model assumption with ID, rationale, effect, status
- [`docs/lender_research_notes.md`](docs/lender_research_notes.md) — per-lender coverage and explicit gap list
- `outputs/research_coverage.csv` — machine-readable per-lender coverage
- `outputs/rule_failure_analysis.csv` — most-failed gates with full denominators
- `outputs/sample_predictions.csv` — one row per (profile × lender)
