"""Streamlit UI for the India Personal Loan Eligibility & Recommendation Engine.

The UI is a thin front-end over the UI-free ``loan_engine`` package.

Run:  .venv/Scripts/streamlit run app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from loan_engine import data_loader as dl  # noqa: E402
from loan_engine import reporting  # noqa: E402
from loan_engine import schemas as sc  # noqa: E402
from loan_engine import validation as vd  # noqa: E402

ROOT = Path(__file__).parent

st.set_page_config(page_title="India Personal Loan Eligibility Engine", layout="wide", page_icon="🏦")


@st.cache_data(show_spinner=False)
def _load_all():
    return dl.load_all(ROOT / "data")


@st.cache_data(show_spinner=False)
def _load_profiles():
    return dl.load_test_profiles(ROOT / "data" / "test_profiles.json")


DATA = _load_all()
LENDERS = DATA["lenders"]
RULES = DATA["rules"]
SOURCES = DATA["sources"]
RULES_BY_LENDER = dl.rules_by_lender(RULES)
SOURCES_BY_ID = dl.sources_by_id(SOURCES)
PROFILES = _load_profiles()

DISCLAIMER = (
    "⚠️ **Educational / research tool — not a lender decision, approval promise, or "
    "financial advice.** Passing publicly documented criteria does not mean a lender "
    "will approve an application. No real personal data (PAN, Aadhaar, account "
    "numbers) is collected; sample profiles are synthetic."
)

PREFERENCE_LABELS = {
    "balanced": "Balanced",
    "lowest_estimated_cost": "Lowest estimated total cost",
    "lowest_emi": "Lowest EMI",
    "highest_estimated_amount": "Highest estimated loan amount",
}

EVIDENCE_EMOJI = {
    "verified_official": "🟢",
    "verified_secondary": "🟡",
    "estimated": "🟠",
    "not_published": "⛔",
    "not_researched": "⚪",
    "unverified": "❔",
    "stale": "🌫️",
}


def _rs(v):
    if v in (None, ""):
        return "unknown"
    try:
        return f"₹{float(v):,.0f}"
    except (TypeError, ValueError):
        return str(v)


def gate_rows(outcome: dict) -> list[dict]:
    rows = []
    for status, key in (("PASSED", "passed_gates"), ("FAILED", "failed_gates"), ("UNRESOLVED", "unresolved_gates")):
        for g in outcome.get(key) or []:
            rule = next((r for r in RULES if r.rule_id == g.get("rule_id")), None)
            src = SOURCES_BY_ID.get(rule.source_id) if rule else None
            rows.append(
                {
                    "Status": status,
                    "Rule": g.get("rule_id"),
                    "Parameter": g.get("parameter_name"),
                    "Explanation": g.get("description") or g.get("explanation", ""),
                    "Required": _rs(g.get("required")),
                    "Actual": _rs(g.get("actual")),
                    "Evidence": rule.evidence_status.value if rule else "",
                    "Mandatory": rule.mandatory if rule else "",
                    "Source": (src.source_url if src else rule.source_url if rule else "") or "",
                    "Accessed": (src.accessed_date if src else rule.accessed_date) or "",
                }
            )
    return rows


def find_result_field(result: dict, path: str):
    cur = result
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


# ----------------------------- Tabs -----------------------------
tab_assess, tab_results, tab_explorer, tab_coverage, tab_about = st.tabs(
    ["🧾 Applicant assessment", "📊 Results", "🔍 Lender explorer", "📈 Research coverage", "ℹ️ About & methodology"]
)

with tab_about:
    st.markdown(
        """
### Purpose & scope
A transparent **rule-based** engine (no machine learning) that evaluates applicant
profiles against **publicly documented** lender rules for unsecured **personal loans in
India only** (no home/auto/education/gold/business loans), then ranks feasible lenders
with a full explanation.

### Two rule layers
1. **Layer A — Go/No-Go gates**: verified mandatory hard rules → `GO` / `NO_GO`.
2. **Layer B — Parameter evaluation**: credit, income/ITR, employment, affordability,
   amount, pricing, tenure, fees, documentation → estimates and explanations.
3. **Recommendation layer**: explainable multi-criteria ranking with 4 preferences
   (transparent weighted sums; no opaque "approval probability").

### Decision semantics
- `NO_GO` — a **verified mandatory** hard gate fails (may still list missing fields).
- `REVIEW_REQUIRED` — no gate fails, but evaluation is blocked by missing applicant data,
  unknown/unpublished rules, or unresearched rules.
- `GO` — all applicable, researched, mandatory gates evaluable **and** pass; a coverage
  warning is always shown beside a GO because public rule data is never complete.
- Applicant level: `ELIGIBLE_UNDER_DOCUMENTED_RULES`,
  `NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES`, `INSUFFICIENT_INFORMATION`.
- Unknown values are **never** silently passed; secondary/estimated rules are never
  treated as verified hard gates.

### Lender selection & limitations
The 20-lender universe is a **project-defined coverage set** — chosen for market
relevance, category diversity (banks / NBFCs / digital platforms) and public-information
availability — **not** a definitive top-20 ranking. Limitations: no lender internal
rules, no approval dataset, no guaranteed approval; applicant-specific rates are
`NOT_PUBLICLY_DETERMINABLE` without a published pricing formula; public thresholds
change (access dates recorded per source).

### Evidence taxonomy
`verified_official` · `verified_secondary` · `estimated` · `not_published` ·
`not_researched` · `unverified` · `stale` — see `docs/research_methodology.md`,
`docs/assumptions.md`, `docs/data_dictionary.md`.
"""
    )

with tab_explorer:
    st.subheader("Lender explorer")
    st.markdown(DISCLAIMER)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        ltypes = st.multiselect(
            "Lender type", ["bank", "nbfc", "digital_platform"], default=["bank", "nbfc", "digital_platform"]
        )
    with c2:
        segfilter = st.selectbox("Employment segment", ["all", "salaried", "self_employed"])
    with c3:
        evfilter = st.multiselect("Evidence status (empty = all)", list(EVIDENCE_EMOJI))
    search = st.text_input("Search lender name").strip().lower()

    for lender in LENDERS:
        if str(lender.lender_type) not in ltypes:
            continue
        if search and search not in lender.lender_name.lower():
            continue
        lrules = RULES_BY_LENDER.get(lender.lender_id, [])
        if segfilter != "all":
            lrules = [r for r in lrules if (r.employment_segment or "all") in (segfilter, "all")]
        if evfilter:
            lrules = [r for r in lrules if r.evidence_status.value in evfilter]
        with st.expander(
            f"{lender.lender_name} — {lender.product_name}  ({len(lrules)} rules shown, research: {lender.research_status})"
        ):
            st.markdown(f"**Regulated entity:** {lender.regulated_entity_name or 'unknown'}")
            st.markdown(f"**Product page:** {lender.official_product_url or 'unknown'}")
            st.markdown(f"**Selection rationale:** {lender.selection_rationale or '—'}")
            if lender.notes:
                st.markdown(f"**Notes:** {lender.notes}")
            st.markdown(f"**Research status:** `{lender.research_status}` | **Last verified:** {lender.last_verified_date}")
            if not lrules:
                st.info("No rules recorded (or none match the current filters).")
            for r in lrules:
                val = r.value_numeric if r.value_numeric is not None else r.value_text
                rng = ""
                if r.range_min is not None or r.range_max is not None:
                    rng = f" (range {r.range_min if r.range_min is not None else '?'}–{r.range_max if r.range_max is not None else '?'})"
                src = SOURCES_BY_ID.get(r.source_id)
                url = (src.source_url if src else r.source_url) or ""
                date = (src.accessed_date if src else r.accessed_date) or ""
                color = EVIDENCE_EMOJI.get(r.evidence_status.value, "❔")
                conf = f", {r.confidence.value} confidence" if r.confidence else ""
                line = (
                    f"- {color} **{r.parameter_name}** (`{r.rule_id}`, {r.rule_category.value}): "
                    f"{r.operator or ''} {_rs(val) if r.value_numeric is not None else (val or 'unknown / not published')}{rng} — "
                    f"`{r.evidence_status.value}`{conf} | segment: {r.employment_segment or 'all'} | mandatory: {r.mandatory}"
                )
                if url:
                    line += f" — [source]({url}) (accessed {date})"
                else:
                    line += " — no source (unknown)"
                st.markdown(line)
                if r.assumption_description:
                    st.markdown(f"  - **Assumption:** {r.assumption_description}")

with tab_assess:
    st.subheader("Applicant assessment")
    st.markdown(DISCLAIMER)

    sample = st.selectbox(
        "Load a synthetic sample profile (synthetic=true, not real data)",
        ["— none —"] + [f"{p.applicant_id} — {p.city or p.employment_type or p.applicant_id}" for p in PROFILES],
    )
    profile = sc.ApplicantProfile()
    if sample != "— none —":
        profile = PROFILES[[f"{p.applicant_id} — {p.city or p.employment_type or p.applicant_id}" for p in PROFILES].index(sample)]

    st.markdown("#### Basic & request")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        age = st.number_input("Age (years)", 0, 100, int(profile.applicant_age_years or 30))
    with c2:
        emp = st.selectbox(
            "Employment type",
            ["salaried", "self_employed", "other"],
            index=["salaried", "self_employed", "other"].index(
                profile.employment_type.value if profile.employment_type else "salaried"
            ),
        )
    with c3:
        cust = st.selectbox(
            "Customer segment", ["unknown", "new_customer", "existing_customer", "preapproved"]
        )
    with c4:
        city = st.text_input("City", profile.city or "")

    c1, c2 = st.columns(2)
    with c1:
        amount = st.number_input(
            "Requested loan amount (₹)", 0, 5_000_000, int(profile.requested_loan_amount_inr or 500000), step=10_000
        )
    with c2:
        tenure = st.number_input("Requested tenure (months)", 1, 120, int(profile.requested_tenure_months or 36))

    if emp == "salaried":
        st.markdown("#### Employment & income (salaried)")
        c1, c2, c3 = st.columns(3)
        with c1:
            net = st.number_input("Monthly net income (₹)", 0, 10_000_000, int(profile.monthly_net_income_inr or 50_000), step=1_000)
        with c2:
            gross = st.number_input("Monthly gross income (₹, optional)", 0, 10_000_000, int(profile.monthly_gross_income_inr or 0), step=1_000)
        with c3:
            jobten = st.number_input("Current job tenure (months)", 0, 600, int(profile.current_job_tenure_months or 12))
        c1, c2 = st.columns(2)
        with c1:
            employer_category = st.text_input("Employer category (optional)", profile.employer_category or "")
        with c2:
            exp = st.number_input("Total work experience (months, optional)", 0, 700, int(profile.total_work_experience_months or 0))
        itr = itryears = vintage = brev = bprof = 0
    else:
        st.markdown("#### Employment & income (self-employed / other)")
        c1, c2, c3 = st.columns(3)
        with c1:
            itr = st.number_input("Annual ITR income (₹)", 0, 100_000_000, int(profile.annual_itr_income_inr or 600_000), step=10_000)
        with c2:
            itryears = st.number_input("ITR years available", 0, 20, int(profile.itr_years_available or 2))
        with c3:
            vintage = st.number_input("Business vintage (months)", 0, 600, int(profile.business_vintage_months or 36))
        c1, c2 = st.columns(2)
        with c1:
            brev = st.number_input("Monthly business revenue (₹, optional)", 0, 100_000_000, int(profile.monthly_business_revenue_inr or 0), step=10_000)
        with c2:
            bprof = st.number_input("Monthly business profit (₹, optional)", 0, 100_000_000, int(profile.monthly_business_profit_inr or 0), step=10_000)
        net = gross = jobten = 0

    st.markdown("#### Credit bureau (leave 0/blank = unknown, not zero-pass)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cibil = st.number_input("CIBIL score (300–900; 0 = unknown)", 0, 900, int(profile.cibil_score or 0))
    with c2:
        active = st.number_input("Active loans", 0, 50, int(profile.active_loan_count or 0))
    with c3:
        enq = st.number_input("Credit enquiries (6m)", 0, 50, int(profile.credit_enquiries_6m or 0))
    with c4:
        overdue = st.number_input("Overdue amount (₹)", 0, 10_000_000, int(profile.overdue_amount_inr or 0), step=1_000)
    c1, c2, c3 = st.columns(3)
    with c1:
        dpd = st.number_input("Max days past due", 0, 3_000, int(profile.days_past_due_max or 0))
    with c2:
        wo = st.number_input("Written-off accounts", 0, 50, int(profile.written_off_accounts_count or 0))
    with c3:
        settled = st.number_input("Settled accounts", 0, 50, int(profile.settled_accounts_count or 0))

    st.markdown("#### Existing obligations")
    c1, c2 = st.columns(2)
    with c1:
        emi = st.number_input("Existing monthly EMI (₹)", 0, 5_000_000, int(profile.existing_monthly_emi_inr or 0), step=1_000)
    with c2:
        other = st.number_input("Other monthly obligations (₹)", 0, 5_000_000, int(profile.other_monthly_debt_obligations_inr or 0), step=1_000)

    preference = st.selectbox(
        "Recommendation preference", list(PREFERENCE_LABELS.values()), index=0
    )
    preference = next(k for k, v in PREFERENCE_LABELS.items() if v == preference)

    st.markdown(DISCLAIMER)

    def build_profile() -> sc.ApplicantProfile:
        data = dict(
            applicant_age_years=int(age) or None,
            employment_type=emp,
            customer_segment=cust,
            city=city or None,
            requested_loan_amount_inr=float(amount),
            requested_tenure_months=int(tenure),
            existing_monthly_emi_inr=float(emi),
            other_monthly_debt_obligations_inr=float(other),
            cibil_score=int(cibil) or None,
            active_loan_count=int(active),
            credit_enquiries_6m=int(enq),
            overdue_amount_inr=float(overdue),
            days_past_due_max=int(dpd),
            written_off_accounts_count=int(wo),
            settled_accounts_count=int(settled),
        )
        if emp == "salaried":
            data.update(
                monthly_net_income_inr=float(net),
                monthly_gross_income_inr=float(gross) or None,
                current_job_tenure_months=int(jobten),
                employer_category=employer_category or None,
                total_work_experience_months=int(exp),
            )
        else:
            data.update(
                annual_itr_income_inr=float(itr),
                itr_years_available=int(itryears),
                business_vintage_months=int(vintage),
                monthly_business_revenue_inr=float(brev) or None,
                monthly_business_profit_inr=float(bprof) or None,
            )
        return sc.ApplicantProfile(**data)

    if st.button("🚀 Run assessment", type="primary"):
        try:
            st.session_state["result"] = reporting.assess_profile(
                build_profile(), LENDERS, RULES, SOURCES, preference=preference
            )
        except Exception as e:  # validation surface
            st.error(f"Could not run assessment: {e}")

with tab_results:
    st.subheader("Results")
    st.markdown(DISCLAIMER)
    result = st.session_state.get("result")
    if not result:
        st.info("Run an assessment in the **Applicant assessment** tab first.")
    else:
        st.markdown(f"**Applicant outcome:** `{result['applicant_outcome']}`")
        ao = result.get("affordability_scenario") or {}
        if ao:
            c1, c2, c3 = st.columns(3)
            c1.metric("Income denominator", _rs(ao.get("income_denominator_inr")))
            c2.metric("Total obligations", _rs(ao.get("obligations_inr")))
            c3.metric("Available EMI (scenario)", _rs(ao.get("available_emi_inr")))
            if ao.get("assumptions"):
                st.caption("Scenario assumptions: " + " | ".join(ao["assumptions"]))

        rrec = result.get("recommendation") or {}
        if rrec.get("summary"):
            st.success(f"**Recommendation ({rrec.get('preference', 'balanced')})** — {rrec['summary']}")
        offers = rrec.get("offers") or []
        if offers:
            off_df = pd.DataFrame(
                [
                    {
                        "Rank": o.get("rank"),
                        "Lender": o.get("lender_name"),
                        "Product": o.get("product_name"),
                        "Feasible": o.get("feasible"),
                        "Est. max amount": _rs(o.get("estimated_max_principal_inr")),
                        "Rate min %": o.get("rate_min_pct"),
                        "Rate max %": o.get("rate_max_pct"),
                        "EMI @min": _rs(o.get("emi_at_min_rate")),
                        "EMI @max": _rs(o.get("emi_at_max_rate")),
                        "Score": o.get("score"),
                        "Why": o.get("rationale"),
                    }
                    for o in offers
                ]
            )
            st.dataframe(off_df, use_container_width=True)

        st.markdown("#### Lender-by-lender decisions")
        for key, label, icon in (("go", "🟢 GO lenders", "GO"), ("review_required", "🟡 REVIEW_REQUIRED lenders", "REVIEW_REQUIRED"), ("no_go", "🔴 NO_GO lenders", "NO_GO")):
            outs = result.get(key) or result.get("lender_outcomes") or []
        all_outs = result.get("lender_outcomes") or []
        for outcome in all_outs:
            decision = outcome.get("decision")
            icon = {"GO": "🟢", "NO_GO": "🔴", "REVIEW_REQUIRED": "🟡"}.get(decision, "❔")
            with st.expander(
                f"{icon} {outcome.get('lender_name')} — {outcome.get('product_name')} → {decision}"
            ):
                if outcome.get("coverage_warning"):
                    st.warning(outcome["coverage_warning"])
                rows = gate_rows(outcome)
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)
                else:
                    st.info("No gate details recorded for this lender.")

        offer_payload = [
            {
                "applicant_id": result.get("profile", {}).get("applicant_id"),
                **{k: v for k, v in (o or {}).items()},
            }
            for o in offers
        ]
        download = {
            "profile": result.get("profile"),
            "applicant_outcome": result.get("applicant_outcome"),
            "affordability_scenario": ao,
            "recommendation": rrec,
            "lender_outcomes": all_outs,
        }
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download results (JSON)", json.dumps(download, indent=2, default=str), "results.json", "application/json")
        c2.download_button(
            "⬇️ Download lender rows (CSV)",
            pd.DataFrame(offer_payload).to_csv(index=False) if offer_payload else "",
            "lender_rows.csv",
            "text/csv",
        )

with tab_coverage:
    st.subheader("Research coverage & insights")
    st.markdown(DISCLAIMER)
    import csv as _csv
    from collections import Counter

    rules_rows = list(_csv.DictReader(open(ROOT / "data" / "lender_rules.csv", encoding="utf-8")))
    lenders_rows = list(_csv.DictReader(open(ROOT / "data" / "lenders.csv", encoding="utf-8")))
    sources_rows = list(_csv.DictReader(open(ROOT / "data" / "source_registry.csv", encoding="utf-8")))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lenders", f"{len(lenders_rows)}/20")
    c2.metric("Rule rows", len(rules_rows))
    c3.metric("Sources", len(sources_rows))
    c4.metric("Last access date", max((s.get("accessed_date") or "") for s in sources_rows) or "—")

    st.markdown("#### Rule records by evidence status")
    ev_counts = Counter(r.get("evidence_status") or "MISSING" for r in rules_rows)
    ev_df = pd.DataFrame(
        {"Evidence status": list(ev_counts), "Rules": list(ev_counts.values())}
    )
    ev_df["Share %"] = (ev_df["Rules"] / ev_df["Rules"].sum() * 100).round(1)
    st.bar_chart(ev_df.set_index("Evidence status")["Rules"])
    st.dataframe(ev_df, use_container_width=True)

    st.markdown("#### Research status by lender")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Lender": l.get("lender_name"),
                    "Type": l.get("lender_type"),
                    "Research status": l.get("research_status"),
                    "Product status": l.get("product_status"),
                    "Last verified": l.get("last_verified_date"),
                    "Rules": sum(1 for r in rules_rows if r.get("lender_id") == l.get("lender_id")),
                }
                for l in lenders_rows
            ],
        ),
        use_container_width=True,
    )

    results_path = ROOT / "data" / "test_results.json"
    if results_path.exists():
        st.markdown("#### Synthetic test-profile outcomes (synthetic data — not real-world rates)")
        res = json.load(open(results_path, encoding="utf-8"))
        dec = Counter()
        ao = Counter()
        for r in (res if isinstance(res, list) else []):
            ao[r.get("applicant_outcome")] += 1
            for lo in r.get("lender_outcomes", []):
                dec[lo.get("decision")] += 1
        c1, c2 = st.columns(2)
        c1.metric("Lender decisions — GO", dec.get("GO", 0))
        c2.metric("Lender decisions — REVIEW_REQUIRED / NO_GO", f"{dec.get('REVIEW_REQUIRED', 0)} / {dec.get('NO_GO', 0)}")
        st.caption("Applicant outcomes: " + ", ".join(f"{k}: {v}" for k, v in ao.items()))

        fail_path = ROOT / "outputs" / "rule_failure_analysis.csv"
        if fail_path.exists():
            st.markdown("##### Most commonly failed / unresolved gates (with denominator)")
            fdf = pd.read_csv(fail_path)
            if not fdf.empty and {"rule_id", "failures", "evaluations"}.issubset(fdf.columns):
                fdf = fdf.sort_values("failures", ascending=False).head(15)
                fdf["Failure rate %"] = (fdf["failures"] / fdf["evaluations"].replace(0, pd.NA) * 100).round(1)
                st.dataframe(fdf, use_container_width=True)
            else:
                st.info("rule_failure_analysis.csv is present but lacks expected columns.")
    else:
        st.info(
            "No synthetic run output found. Generate it with: "
            "`python -m loan_engine.cli --profiles data/test_profiles.json --output data/test_results.json --write-outputs`"
        )
