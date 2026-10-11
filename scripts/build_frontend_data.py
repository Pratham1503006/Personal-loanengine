"""Generate scripts/frontend_data.js — the datasets embedded into index.html.

Run from the repository root:

    python scripts/build_frontend_data.py

This regenerates the JS data blob consumed by index.html from the same
CSV/JSON sources the Python engine uses, so the client-side evaluator stays in
sync with the documented rule base. Nothing here changes engine semantics —
the JS in index.html mirrors rule_engine.py, it does not re-research anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from loan_engine import data_loader as dl  # noqa: E402
from loan_engine import feature_engineering as fe, rule_engine as re_  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "scripts" / "frontend_data.js"


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)


def _summary(profile: sc.ApplicantProfile) -> str:
    bits = []
    for key, label in (
        ("applicant_age_years", "age"),
        ("employment_type", "emp"),
        ("monthly_net_income_inr", "net"),
        ("annual_itr_income_inr", "itr"),
        ("cibil_score", "cibil"),
        ("existing_monthly_emi_inr", "emi"),
        ("requested_loan_amount_inr", "req"),
        ("requested_tenure_months", "ten"),
    ):
        v = getattr(profile, key, None)
        if v is None:
            continue
        if hasattr(v, "value"):  # enums -> plain string value
            v = v.value
        bits.append(f"{label}={v}")
    return " ".join(bits)


def main() -> None:
    lenders = dl.load_lenders()
    rules = dl.load_rules()
    sources = dl.load_sources()

    # Pre-compute sample profiles with the real Python engine so index.html
    # shows verified outcomes (the JS evaluator mirrors the same semantics).
    samples = []
    try:
        profiles = dl.load_test_profiles()
        rules_by_lender = dl.rules_by_lender(rules)
        for profile in profiles:
            derived = fe.compute_derived(profile, 0.5)
            decisions = [
                o.decision.value  # "GO" / "NO_GO" / "REVIEW_REQUIRED"
                for o in re_.evaluate_all(profile, lenders, rules, derived)
            ]
            counts = {
                "GO": decisions.count("GO"),
                "REVIEW_REQUIRED": decisions.count("REVIEW_REQUIRED"),
                "NO_GO": decisions.count("NO_GO"),
            }
            samples.append(
                {
                    "profile_id": profile.applicant_id,
                    "inputs": profile.model_dump(),
                    "short": _summary(profile),
                    "outcome": (
                        "ELIGIBLE_UNDER_DOCUMENTED_RULES"
                        if counts["GO"] > 0
                        else (
                            "NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES"
                    if counts["NO_GO"] == len(decisions) and decisions
                    else "INSUFFICIENT_INFORMATION"
                )
            ),
                    "counts": counts,
                }
            )
    except FileNotFoundError:
        samples = []

    payload = {
        "generatedOn": "2026-10-11",
        "samples": samples,
        "lenders": [
            {
                "lender_id": l.lender_id,
                "lender_name": l.lender_name,
                "lender_type": l.lender_type,
                "regulated_entity_name": l.regulated_entity_name,
                "product_name": l.product_name,
                "official_product_url": l.official_product_url,
                "product_status": l.product_status,
                "research_status": l.research_status,
                "notes": l.notes,
            }
            for l in lenders
        ],
        "rules": [
            {
                "rule_id": r.rule_id,
                "lender_id": r.lender_id,
                "product_name": r.product_name,
                "parameter_name": r.parameter_name,
                "rule_category": r.rule_category.value,
                "rule_type": r.rule_type.value,
                "operator": r.operator.value,
                "value_numeric": r.value_numeric,
                "value_text": r.value_text,
                "range_min": r.range_min,
                "range_max": r.range_max,
                "unit": r.unit,
                "employment_segment": r.employment_segment,
                "customer_segment": r.customer_segment,
                "mandatory": r.mandatory,
                "evidence_status": r.evidence_status.value,
                "source_id": r.source_id,
                "source_url": r.source_url,
                "source_title": r.source_title,
                "source_type": r.source_type,
                "accessed_date": str(r.accessed_date) if r.accessed_date else None,
                "assumption_description": r.assumption_description,
                "notes": r.notes,
            }
            for r in rules
        ],
        "sources": [
            {
                "source_id": s.source_id,
                "lender_id": s.lender_id,
                "source_title": s.source_title,
                "source_url": s.source_url,
                "source_type": s.source_type,
                "publisher": s.publisher,
                "accessed_date": str(s.accessed_date) if s.accessed_date else None,
            }
            for s in sources
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "// AUTO-GENERATED by scripts/build_frontend_data.py — do not edit by hand.\n"
        "// Source of truth: data/lenders.csv, data/lender_rules.csv, data/source_registry.csv\n"
        f"window.__ENGINE_DATA__ = {_dump(payload)};\n"
        f"window.__SAMPLE_PROFILES__ = {_dump(samples)};\n"
    )
    OUT.write_text(header, encoding="utf-8")
    _inject_into_html(header)  # keep index.html's embedded copy in sync
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT} ({size_kb:.1f} KB, {len(rules)} rules, {len(lenders)} lenders, {len(sources)} sources)")


def _inject_into_html(js_blob: str) -> None:
    """Keep the data script inside index.html in sync with the datasets.

    Either fills the ``<!--DATA_BLOB-->`` placeholder (first run) or replaces
    the whole previously generated ``<script> // AUTO-GENERATED ...`` block.
    """
    import re

    html_path = REPO / "index.html"
    if not html_path.exists():
        print("(index.html not found; skipping embedded-data sync)")
        return
    html = html_path.read_text(encoding="utf-8")
    inline = f"<script>\n{js_blob}</script>"
    pattern = re.compile(r"<script>\s*// AUTO-GENERATED[\s\S]*?</script>")
    marker = "<!--DATA_BLOB-->"
    if marker in html:
        html = html.replace(marker, inline)
    elif pattern.search(html):
        html = pattern.sub(lambda _: inline, html, count=1)  # noqa: B023 fine—single shot
    else:
        print("(no DATA_BLOB marker and no generated block found in index.html; skipped)")
        return
    html_path.write_text(html, encoding="utf-8")
    print("Embedded data block in index.html updated.")


if __name__ == "__main__":
    main()
