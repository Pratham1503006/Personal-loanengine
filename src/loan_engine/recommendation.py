"""Explainable multi-criteria comparison of feasible lenders.

The engine produces *estimated offers* only for lenders whose gate decision is
``GO``. ``REVIEW_REQUIRED`` lenders are reported separately and are never
presented as confirmed matches. Scores are transparent weighted sums over
named criteria — there is no opaque "approval probability".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import loan_calculator as lc
from . import affordability as aff
from .schemas import (
    ApplicantProfile,
    EvidenceStatus,
    GateDecision,
    Lender,
    LenderOutcome,
    Rule,
    RuleCategory,
    RuleType,
)

PREFERENCES = ["balanced", "lowest_estimated_cost", "lowest_emi", "highest_estimated_amount"]

#: Transparent ranking weights for the ``balanced`` preference.
BALANCED_WEIGHTS = {
    "feasibility": 0.45,
    "affordability": 0.30,
    "estimated_cost": 0.15,
    "evidence_quality": 0.10,
}

#: Scenario FOIR used to derive the affordability bound for estimates.
DEFAULT_ESTIMATE_FOIR = aff.DEFAULT_SCENARIO_FOIR


@dataclass
class EstimatedOffer:
    lender_id: str
    lender_name: str
    product_name: str
    feasible: bool
    requested_amount_inr: Optional[float]
    estimated_max_principal_inr: Optional[float]
    product_max_inr: Optional[float]
    affordability_max_inr: Optional[float]
    income_based_max_inr: Optional[float]
    feasible_tenure_months: Optional[int]
    published_tenure_min_months: Optional[int]
    published_tenure_max_months: Optional[int]
    rate_min_pct: Optional[float]
    rate_max_pct: Optional[float]
    emi_at_min_rate: Optional[float]
    emi_at_max_rate: Optional[float]
    total_repayment_min_rate: Optional[float]
    total_repayment_max_rate: Optional[float]
    processing_fee_text: Optional[str] = None
    applicant_specific_rate_status: str = "NOT_PUBLICLY_DETERMINABLE"
    evidence_note: str = ""
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    score: Optional[float] = None
    rank: Optional[int] = None
    rationale: str = ""


def _bounds(rule: Rule):
    """Return (lo, hi) numeric bounds implied by a rule, else (None, None)."""
    if not rule.has_known_value:
        return None, None
    if rule.range_min is not None or rule.range_max is not None:
        return rule.range_min, rule.range_max
    if rule.value_numeric is not None:
        if rule.operator.value == "<=":
            return None, rule.value_numeric
        if rule.operator.value == ">=":
            return rule.value_numeric, None
        return rule.value_numeric, rule.value_numeric
    return None, None


def _min_known(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return min(vals) if vals else None


def _max_known(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return max(vals) if vals else None


def extract_product_limits(rules: List[Rule]) -> dict:
    """Pull published amount/tenure/rate/fee bounds from a lender's rules."""
    amount_mins, amount_maxs = [], []
    tenure_mins, tenure_maxs = [], []
    rate_mins, rate_maxs = [], []
    fee_texts: List[str] = []
    income_based_max: List[float] = []

    for rule in rules:
        lo, hi = _bounds(rule)
        if rule.rule_category == RuleCategory.LOAN_AMOUNT:
            amount_mins.append(lo)
            amount_maxs.append(hi)
            if rule.parameter_name in {"income_based_max_loan", "max_loan_multiple_of_income"}:
                if hi is not None:
                    income_based_max.append(hi)
        elif rule.rule_category == RuleCategory.TENURE:
            tenure_mins.append(lo)
            tenure_maxs.append(hi)
        elif rule.rule_category == RuleCategory.PRICING:
            rate_mins.append(lo)
            rate_maxs.append(hi)
        elif rule.rule_category == RuleCategory.FEES:
            if rule.value_text:
                fee_texts.append(rule.value_text)
            elif rule.value_numeric is not None:
                fee_texts.append(f"{rule.value_numeric} {rule.unit or ''}".strip())

    return {
        "min_loan_inr": _min_known(amount_mins),
        "max_loan_inr": _max_known(amount_maxs),
        "min_tenure_months": _min_known(tenure_mins),
        "max_tenure_months": _max_known(tenure_maxs),
        "rate_min_pct": _min_known(rate_mins),
        "rate_max_pct": _max_known(rate_maxs),
        "fee_texts": fee_texts,
        "income_based_max_inr": _max_known(income_based_max),
    }


def _evidence_quality(lender_outcome: LenderOutcome) -> float:
    """0..1 evidence-quality proxy from evaluated mandatory rules."""
    total = lender_outcome.total_mandatory_count
    if total == 0:
        return 0.0
    official = sum(1 for r in lender_outcome.passed_gates if r.is_verified_official)
    return min(1.0, official / total)


def build_offer(
    lender: Lender,
    outcome: LenderOutcome,
    rules: List[Rule],
    profile: ApplicantProfile,
) -> EstimatedOffer:
    limits = extract_product_limits(rules)
    requested = profile.requested_loan_amount_inr
    requested_tenure = profile.requested_tenure_months

    rate_min = limits["rate_min_pct"]
    rate_max = limits["rate_max_pct"]

    # Affordability bound using the scenario FOIR (assumption, documented).
    scen = aff.affordability_scenario(
        profile,
        DEFAULT_ESTIMATE_FOIR,
        annual_rate_pct=rate_max if rate_max is not None else rate_min,
        tenure_months=requested_tenure,
    )
    affordability_max = scen.get("affordability_principal_inr")

    candidates = [
        v
        for v in (
            limits["max_loan_inr"],
            limits["income_based_max_inr"],
            affordability_max,
        )
        if v is not None
    ]
    estimated_max = min(candidates) if candidates else None

    # Tenure feasibility.
    feasible_tenure = requested_tenure
    if requested_tenure is not None:
        if limits["min_tenure_months"] is not None and requested_tenure < limits["min_tenure_months"]:
            feasible_tenure = None
        if limits["max_tenure_months"] is not None and requested_tenure > limits["max_tenure_months"]:
            feasible_tenure = None
    elif limits["min_tenure_months"] is not None and limits["max_tenure_months"] is not None:
        feasible_tenure = limits["max_tenure_months"]

    unknowns: List[str] = []
    if limits["max_loan_inr"] is None:
        unknowns.append("Published maximum loan amount not found in dataset.")
    if rate_min is None or rate_max is None:
        unknowns.append("Published interest-rate range incomplete.")
    if limits["min_tenure_months"] is None or limits["max_tenure_months"] is None:
        unknowns.append("Published tenure range incomplete.")

    amount_for_emi = requested if requested is not None else estimated_max
    emi_min = emi_max = tr_min = tr_max = None
    if amount_for_emi is not None and feasible_tenure:
        rng = lc.emi_range(amount_for_emi, rate_min, rate_max, feasible_tenure)
        emi_min, emi_max = rng["emi_low"], rng["emi_high"]
        if rate_min is not None:
            tr_min = lc.total_repayment(amount_for_emi, rate_min, feasible_tenure)
        if rate_max is not None:
            tr_max = lc.total_repayment(amount_for_emi, rate_max, feasible_tenure)

    feasible = outcome.decision == GateDecision.GO
    if requested is not None and estimated_max is not None and requested > estimated_max:
        feasible = False
    if feasible_tenure is None:
        feasible = False

    return EstimatedOffer(
        lender_id=lender.lender_id,
        lender_name=lender.lender_name,
        product_name=lender.product_name,
        feasible=feasible,
        requested_amount_inr=requested,
        estimated_max_principal_inr=estimated_max,
        product_max_inr=limits["max_loan_inr"],
        affordability_max_inr=affordability_max,
        income_based_max_inr=limits["income_based_max_inr"],
        feasible_tenure_months=feasible_tenure,
        published_tenure_min_months=limits["min_tenure_months"],
        published_tenure_max_months=limits["max_tenure_months"],
        rate_min_pct=rate_min,
        rate_max_pct=rate_max,
        emi_at_min_rate=emi_min,
        emi_at_max_rate=emi_max,
        total_repayment_min_rate=tr_min,
        total_repayment_max_rate=tr_max,
        processing_fee_text="; ".join(limits["fee_texts"]) or None,
        evidence_note=(
            f"{outcome.evaluated_mandatory_count}/{outcome.total_mandatory_count} "
            "mandatory rules evaluated."
        ),
        assumptions=[
            "EMI uses advertised rate endpoints; applicant-specific pricing is "
            "NOT_PUBLICLY_DETERMINABLE.",
            f"Affordability bound uses scenario FOIR {DEFAULT_ESTIMATE_FOIR:.0%} (assumption).",
            "Fees, taxes and insurance are excluded from EMI/total repayment.",
        ],
        unknowns=unknowns,
    )


def _group_rules(rules):
    grouped: Dict[str, list] = {}
    for rule in rules:
        grouped.setdefault(rule.lender_id, []).append(rule)
    return grouped


def _score_offers(
    offers: List[EstimatedOffer],
    preference: str,
) -> None:
    """Assign transparent scores in-place (higher is better)."""
    if not offers:
        return
    emis = [o.emi_at_min_rate for o in offers if o.emi_at_min_rate is not None]
    costs = [o.total_repayment_min_rate for o in offers if o.total_repayment_min_rate is not None]
    amounts = [o.estimated_max_principal_inr for o in offers if o.estimated_max_principal_inr is not None]
    emi_best, emi_worst = (min(emis), max(emis)) if emis else (None, None)
    cost_best, cost_worst = (min(costs), max(costs)) if costs else (None, None)
    amt_best, amt_worst = (max(amounts), min(amounts)) if amounts else (None, None)

    for offer in offers:
        def norm_low(value, best, worst):
            if value is None or best is None or worst is None or best == worst:
                return 0.5
            return 1.0 - (value - best) / (worst - best)

        def norm_high(value, best, worst):
            if value is None or best is None or worst is None or best == worst:
                return 0.5
            return 1.0 - (worst - value) / (worst - best)

        affordability = norm_low(offer.emi_at_min_rate, emi_best, emi_worst)
        cost = norm_low(offer.total_repayment_min_rate, cost_best, cost_worst)
        amount = norm_high(offer.estimated_max_principal_inr, amt_best, amt_worst)
        feasibility = 1.0 if offer.feasible else 0.0
        evidence = 1.0  # GO lenders have evaluated their mandatory rules

        if preference == "lowest_estimated_cost":
            score = 0.75 * cost + 0.25 * feasibility
        elif preference == "lowest_emi":
            score = 0.75 * affordability + 0.25 * feasibility
        elif preference == "highest_estimated_amount":
            score = 0.75 * amount + 0.25 * feasibility
        else:  # balanced
            score = (
                BALANCED_WEIGHTS["feasibility"] * feasibility
                + BALANCED_WEIGHTS["affordability"] * affordability
                + BALANCED_WEIGHTS["estimated_cost"] * cost
                + BALANCED_WEIGHTS["evidence_quality"] * evidence
            )
        offer.score = round(score, 4)


def recommend(
    profile: ApplicantProfile,
    lenders: List[Lender],
    outcomes: List[LenderOutcome],
    rules_by_lender: Dict[str, List[Rule]],
    preference: str = "balanced",
) -> dict:
    """Produce offers, rankings and a plain-language recommendation."""
    if preference not in PREFERENCES:
        raise ValueError(f"preference must be one of {PREFERENCES}")

    if not isinstance(rules_by_lender, dict):
        rules_by_lender = _group_rules(rules_by_lender)

    lender_by_id = {l.lender_id: l for l in lenders}
    go_outcomes = [o for o in outcomes if o.decision == GateDecision.GO]

    offers = [
        build_offer(
            lender_by_id[o.lender_id],
            o,
            rules_by_lender.get(o.lender_id, []),
            profile,
        )
        for o in go_outcomes
        if o.lender_id in lender_by_id
    ]

    _score_offers(offers, preference)
    offers.sort(key=lambda o: (o.feasible, o.score or 0.0), reverse=True)
    for i, offer in enumerate(offers, start=1):
        offer.rank = i
        offer.rationale = _rationale(offer, preference)

    review = [o for o in outcomes if o.decision == GateDecision.REVIEW_REQUIRED]
    no_go = [o for o in outcomes if o.decision == GateDecision.NO_GO]

    winner = offers[0] if offers else None
    if winner is None:
        summary = (
            "No lender has a defensible GO result under the documented rules, so "
            "no recommendation is produced. Review the REVIEW_REQUIRED lenders "
            "(incomplete rules or missing applicant data) or the NO_GO gates."
        )
    else:
        summary = (
            f"Under the '{preference}' preference and the documented rules, the "
            f"top estimate is {winner.lender_name} ({winner.product_name}) — "
            f"{winner.rationale} This is an estimate, not an approval promise."
        )

    return {
        "preference": preference,
        "offers": offers,
        "winner": winner,
        "review_lenders": [o.lender_id for o in review],
        "no_go_lenders": [o.lender_id for o in no_go],
        "summary": summary,
    }


def _rationale(offer: EstimatedOffer, preference: str) -> str:
    bits = []
    if offer.feasible:
        bits.append("the requested amount and tenure fit the documented product limits")
    else:
        bits.append("the request exceeds a documented bound or is otherwise infeasible")
    if offer.emi_at_min_rate is not None:
        bits.append(
            f"estimated EMI {offer.emi_at_min_rate:,.0f}–"
            f"{offer.emi_at_max_rate:,.0f} INR over {offer.feasible_tenure_months} months"
        )
    if offer.estimated_max_principal_inr is not None:
        bits.append(f"estimated maximum about {offer.estimated_max_principal_inr:,.0f} INR")
    bits.append(f"ranked under '{preference}'")
    if offer.unknowns:
        bits.append("unknowns: " + "; ".join(offer.unknowns))
    return "; ".join(bits) + "."
