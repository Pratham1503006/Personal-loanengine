"""Assemble results, exports and research-coverage reporting.

This is the glue layer used by both the CLI and the Streamlit UI. It depends
only on the core engine modules (never on Streamlit).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from . import affordability as aff
from . import data_loader as dl
from . import feature_engineering as fe
from . import recommendation as rec
from . import rule_engine as re
from .schemas import (
    ApplicantOutcome,
    ApplicantProfile,
    EvidenceStatus,
    GateDecision,
    Lender,
    LenderOutcome,
    Rule,
    Source,
)
from .validation import validate_profile


def _outcome_to_dict(o: LenderOutcome) -> dict:
    def rule_list(items):
        return [
            {
                "rule_id": r.rule_id,
                "parameter_name": r.parameter_name,
                "rule_category": r.rule_category.value,
                "rule_type": r.rule_type.value,
                "mandatory": r.mandatory,
                "evidence_status": r.evidence_status.value,
                "operator": r.operator,
                "actual_value": r.actual_value,
                "required_value": r.required_value,
                "source_id": r.source_id,
                "source_url": r.source_url,
                "source_title": r.source_title,
                "source_type": r.source_type,
                "accessed_date": r.accessed_date.isoformat() if r.accessed_date else None,
                "message": r.message,
                "is_verified_official": r.is_verified_official,
                "blocks_approval": r.blocks_approval,
            }
            for r in items
        ]

    return {
        "lender_id": o.lender_id,
        "lender_name": o.lender_name,
        "product_name": o.product_name,
        "decision": o.decision.value,
        "coverage_warning": o.coverage_warning,
        "evaluated_mandatory_count": o.evaluated_mandatory_count,
        "total_mandatory_count": o.total_mandatory_count,
        "explanation": o.explanation,
        "failed_gates": rule_list(o.failed_gates),
        "unevaluable_mandatory": rule_list(o.unevaluable_mandatory),
        "soft_flags": rule_list(o.soft_flags),
    }


def _offer_to_dict(offer: rec.EstimatedOffer) -> dict:
    return {
        "rank": offer.rank,
        "lender_id": offer.lender_id,
        "lender_name": offer.lender_name,
        "product_name": offer.product_name,
        "feasible": offer.feasible,
        "requested_amount_inr": offer.requested_amount_inr,
        "estimated_max_principal_inr": offer.estimated_max_principal_inr,
        "product_max_inr": offer.product_max_inr,
        "affordability_max_inr": offer.affordability_max_inr,
        "feasible_tenure_months": offer.feasible_tenure_months,
        "published_tenure_min_months": offer.published_tenure_min_months,
        "published_tenure_max_months": offer.published_tenure_max_months,
        "rate_min_pct": offer.rate_min_pct,
        "rate_max_pct": offer.rate_max_pct,
        "emi_at_min_rate": offer.emi_at_min_rate,
        "emi_at_max_rate": offer.emi_at_max_rate,
        "total_repayment_min_rate": offer.total_repayment_min_rate,
        "total_repayment_max_rate": offer.total_repayment_max_rate,
        "processing_fee_text": offer.processing_fee_text,
        "applicant_specific_rate_status": offer.applicant_specific_rate_status,
        "evidence_note": offer.evidence_note,
        "assumptions": offer.assumptions,
        "unknowns": offer.unknowns,
        "score": offer.score,
        "rationale": offer.rationale,
    }


def assess_profile(
    profile: ApplicantProfile,
    lenders: List[Lender],
    rules: List[Rule],
    sources: List[Source],
    preference: str = "balanced",
    foir_fraction: Optional[float] = None,
) -> dict:
    """Run the full pipeline for one applicant and return a result dict."""
    validation = validate_profile(profile)
    derived = fe.compute_derived(profile, foir_fraction)
    rules_by_lender = dl.rules_by_lender(rules)
    outcomes = re.evaluate_all(profile, lenders, rules, derived)
    applicant_verdict = re.applicant_outcome(outcomes)
    recommendation = rec.recommend(profile, lenders, outcomes, rules_by_lender, preference)
    scenario = aff.affordability_scenario(profile, foir_fraction or aff.DEFAULT_SCENARIO_FOIR)

    return {
        "generated_at": date.today().isoformat(),
        "engine_version": __import__("loan_engine").__version__,
        "disclaimer": (
            "Educational/research tool. Passing documented public criteria is not "
            "a promise of approval and this is not financial advice."
        ),
        "profile": profile.model_dump(mode="json"),
        "validation": {
            "is_valid": validation.is_valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
        },
        "derived": derived.model_dump(mode="json"),
        "affordability_scenario": {
            k: v for k, v in scenario.items() if k != "assumptions"
        },
        "affordability_assumptions": scenario.get("assumptions", []),
        "applicant_outcome": applicant_verdict.value,
        "lender_outcomes": [_outcome_to_dict(o) for o in outcomes],
        "recommendation": {
            "preference": recommendation["preference"],
            "summary": recommendation["summary"],
            "winner_lender_id": recommendation["winner"].lender_id if recommendation["winner"] else None,
            "offers": [_offer_to_dict(o) for o in recommendation["offers"]],
            "review_lenders": recommendation["review_lenders"],
            "no_go_lenders": recommendation["no_go_lenders"],
        },
    }


def save_result_json(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)


def offer_rows(result: dict) -> List[dict]:
    """Flatten a result into one CSV-friendly row per lender outcome."""
    rows = []
    offers = {o["lender_id"]: o for o in result["recommendation"]["offers"]}
    for lo in result["lender_outcomes"]:
        offer = offers.get(lo["lender_id"], {})
        rows.append(
            {
                "applicant_id": result["profile"].get("applicant_id"),
                "lender_id": lo["lender_id"],
                "lender_name": lo["lender_name"],
                "product_name": lo["product_name"],
                "decision": lo["decision"],
                "applicant_outcome": result["applicant_outcome"],
                "evaluated_mandatory_count": lo["evaluated_mandatory_count"],
                "total_mandatory_count": lo["total_mandatory_count"],
                "n_failed_gates": len(lo["failed_gates"]),
                "n_unevaluable_mandatory": len(lo["unevaluable_mandatory"]),
                "est_max_principal_inr": offer.get("estimated_max_principal_inr"),
                "rate_min_pct": offer.get("rate_min_pct"),
                "rate_max_pct": offer.get("rate_max_pct"),
                "emi_min": offer.get("emi_at_min_rate"),
                "emi_max": offer.get("emi_at_max_rate"),
                "feasible": offer.get("feasible"),
                "rank": offer.get("rank"),
                "score": offer.get("score"),
            }
        )
    return rows


def sample_predictions(results: List[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.extend(offer_rows(result))
    return pd.DataFrame(rows)


def rule_failure_analysis(results: List[dict]) -> pd.DataFrame:
    """Count gate failures/flags across synthetic results.

    Reports numerator and denominator (denominator excludes profiles where the
    rule was not evaluable for the lender).
    """
    counters: Dict[tuple, dict] = {}
    for result in results:
        for lo in result["lender_outcomes"]:
            for gate in lo["failed_gates"]:
                key = (lo["lender_id"], gate["rule_id"], gate["parameter_name"])
                row = counters.setdefault(
                    key,
                    {
                        "lender_id": lo["lender_id"],
                        "rule_id": gate["rule_id"],
                        "parameter_name": gate["parameter_name"],
                        "rule_category": gate["rule_category"],
                        "evidence_status": gate["evidence_status"],
                        "failures": 0,
                        "evaluations": 0,
                    },
                )
                row["failures"] += 1
                row["evaluations"] += 1
            for gate in lo["unevaluable_mandatory"]:
                key = (lo["lender_id"], gate["rule_id"], gate["parameter_name"])
                row = counters.setdefault(
                    key,
                    {
                        "lender_id": lo["lender_id"],
                        "rule_id": gate["rule_id"],
                        "parameter_name": gate["parameter_name"],
                        "rule_category": gate["rule_category"],
                        "evidence_status": gate["evidence_status"],
                        "failures": 0,
                        "evaluations": 0,
                    },
                )
                row["evaluations"] += 1
    rows = list(counters.values())
    for row in rows:
        row["failure_rate_of_evaluated"] = (
            round(row["failures"] / row["evaluations"], 4) if row["evaluations"] else None
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["failures", "evaluations"], ascending=False)
    return df


def research_coverage(
    lenders: List[Lender],
    rules: List[Rule],
    sources: List[Source],
) -> pd.DataFrame:
    """Per-lender coverage/quality summary plus an overall tally."""
    by_status: Dict[tuple, int] = {}
    for rule in rules:
        key = (rule.lender_id, rule.evidence_status.value)
        by_status[key] = by_status.get(key, 0) + 1

    source_counts: Dict[str, int] = {}
    for src in sources:
        if src.lender_id:
            source_counts[src.lender_id] = source_counts.get(src.lender_id, 0) + 1

    last_access: Dict[str, date] = {}
    for src in sources:
        if src.lender_id:
            prev = last_access.get(src.lender_id)
            if prev is None or src.accessed_date > prev:
                last_access[src.lender_id] = src.accessed_date

    rows = []
    for lender in lenders:
        total = sum(v for (lid, _), v in by_status.items() if lid == lender.lender_id)
        row = {
            "lender_id": lender.lender_id,
            "lender_name": lender.lender_name,
            "lender_type": lender.lender_type,
            "regulated_entity_name": lender.regulated_entity_name,
            "product_status": lender.product_status,
            "research_status": lender.research_status,
            "total_rules": total,
            "sources": source_counts.get(lender.lender_id, 0),
            "last_source_accessed": (
                last_access[lender.lender_id].isoformat() if lender.lender_id in last_access else None
            ),
        }
        for status in EvidenceStatus:
            row[status.value] = by_status.get((lender.lender_id, status.value), 0)
        rows.append(row)
    return pd.DataFrame(rows)


def coverage_summary(coverage_df: pd.DataFrame) -> dict:
    if coverage_df.empty:
        return {}
    researched = int((coverage_df["total_rules"] > 0).sum())
    return {
        "lenders_total": int(len(coverage_df)),
        "lenders_with_rules": researched,
        "lenders_without_rules": int(len(coverage_df) - researched),
        "verified_official_rules": int(coverage_df.get("verified_official", pd.Series(dtype=int)).sum()),
        "verified_secondary_rules": int(coverage_df.get("verified_secondary", pd.Series(dtype=int)).sum()),
        "estimated_rules": int(coverage_df.get("estimated", pd.Series(dtype=int)).sum()),
        "not_published_rules": int(coverage_df.get("not_published", pd.Series(dtype=int)).sum()),
        "not_researched_rules": int(coverage_df.get("not_researched", pd.Series(dtype=int)).sum()),
        "unverified_rules": int(coverage_df.get("unverified", pd.Series(dtype=int)).sum()),
    }
