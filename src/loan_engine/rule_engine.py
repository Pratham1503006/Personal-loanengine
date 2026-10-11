"""The two-layer rule engine.

Layer A (go/no-go gates) and Layer B (parameter-based evaluation) are both
represented as rows in ``data/lender_rules.csv``. This module evaluates every
applicable rule for one applicant and aggregates the results into a
:class:`loan_engine.schemas.LenderOutcome`.

Safety properties enforced here:

* A rule only applies when its employment/customer segment matches.
* Unknown / unpublishable thresholds (``not_published``, ``not_researched``,
  ``unverified``, ``stale``) never *pass* a gate silently.
* Only ``verified_official`` mandatory blocking rules can cause ``NO_GO``.
* ``estimated`` rules can never be treated as verified hard gates.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from . import feature_engineering as fe
from .schemas import (
    ApplicantOutcome,
    ApplicantProfile,
    DerivedFeatures,
    EvidenceStatus,
    GateDecision,
    Lender,
    LenderOutcome,
    Operator,
    Rule,
    RuleCategory,
    RuleEvaluation,
    RuleType,
)

#: Rule types that can block an application when mandatory.
BLOCKING_RULE_TYPES = {RuleType.HARD_GATE, RuleType.PRODUCT_CONSTRAINT}
#: Evidence statuses that mean "we cannot evaluate this as a documented rule".
UNEVALUABLE_STATUSES = {
    EvidenceStatus.NOT_RESEARCHED,
    EvidenceStatus.UNVERIFIED,
    EvidenceStatus.STALE,
}
#: Evidence statuses that simply carry no published threshold/rule.
NO_RULE_STATUSES = {EvidenceStatus.NOT_PUBLISHED}


def _norm(value) -> Optional[str]:
    if value is None:
        return None
    text = getattr(value, "value", str(value)).strip().lower()
    return text or None


def rule_applies(rule: Rule, profile: ApplicantProfile) -> bool:
    """Whether a rule is in scope for this applicant's segment."""
    seg = _norm(rule.employment_segment)
    if seg and seg not in {"all", ""}:
        applicant_seg = _norm(profile.employment_type)
        if applicant_seg is None:
            # Segment-specific rule but applicant segment unknown: scope it in
            # but mark applicably unevaluable elsewhere via customer/param.
            return False
        if seg != applicant_seg:
            return False

    cust = _norm(rule.customer_segment)
    if cust and cust not in {"all", "unspecified", ""}:
        applicant_cust = _norm(profile.customer_segment)
        if applicant_cust is None:
            return False
        if cust != applicant_cust:
            return False
    return True


def _required_value(rule: Rule):
    if rule.value_numeric is not None:
        return rule.value_numeric
    if rule.range_min is not None or rule.range_max is not None:
        return (rule.range_min, rule.range_max)
    if rule.value_text is not None:
        return rule.value_text
    return None


def evaluate_operator(rule: Rule, actual) -> Optional[bool]:
    """Apply ``rule.operator`` to ``actual``; ``None`` means not evaluable."""
    op = rule.operator
    if op in (Operator.INFORMATIONAL, Operator.REQUIRES):
        return None  # handled as informational, not a pass/fail gate

    if actual is None:
        return None

    if op == Operator.GE:
        if rule.value_numeric is None:
            return None
        try:
            return float(actual) >= float(rule.value_numeric)
        except (TypeError, ValueError):
            return None
    if op == Operator.LE:
        if rule.value_numeric is None:
            return None
        try:
            return float(actual) <= float(rule.value_numeric)
        except (TypeError, ValueError):
            return None
    if op == Operator.EQ:
        target = rule.value_numeric if rule.value_numeric is not None else rule.value_text
        if target is None:
            return None
        if isinstance(target, (int, float)):
            try:
                return float(actual) == float(target)
            except (TypeError, ValueError):
                return None
        return _norm(actual) == _norm(target)
    if op == Operator.IN:
        if rule.value_text is None:
            return None
        allowed = {_norm(v) for v in str(rule.value_text).split(",") if _norm(v)}
        return _norm(actual) in allowed
    if op == Operator.RANGE:
        try:
            val = float(actual)
        except (TypeError, ValueError):
            return None
        if rule.range_min is not None and val < float(rule.range_min):
            return False
        if rule.range_max is not None and val > float(rule.range_max):
            return False
        return True
    return None


def _is_blocking(rule: Rule) -> bool:
    return rule.mandatory and rule.rule_type in BLOCKING_RULE_TYPES


def evaluate_rule(
    rule: Rule,
    profile: ApplicantProfile,
    values: Dict[str, object],
) -> RuleEvaluation:
    """Evaluate a single rule and return a fully-annotated result."""
    base = dict(
        rule_id=rule.rule_id,
        lender_id=rule.lender_id,
        parameter_name=rule.parameter_name,
        rule_category=rule.rule_category,
        rule_type=rule.rule_type,
        mandatory=rule.mandatory,
        evidence_status=rule.evidence_status,
        applied=True,
        is_verified_official=rule.is_verified_official,
        source_id=rule.source_id,
        source_url=rule.source_url,
        source_title=rule.source_title,
        source_type=rule.source_type,
        accessed_date=rule.accessed_date,
        operator=rule.operator.value,
        required_value=_required_value(rule),
    )

    actual = values.get(rule.parameter_name)

    # Unknown / non-published rule values.
    if rule.evidence_status in NO_RULE_STATUSES:
        return RuleEvaluation(
            **base,
            evaluable=False,
            passed=None,
            actual_value=actual,
            message=(
                "Lender does not publish a threshold/value for this parameter; "
                "recorded as not_published, not treated as a gate."
            ),
        )
    if rule.evidence_status in UNEVALUABLE_STATUSES:
        return RuleEvaluation(
            **base,
            evaluable=False,
            passed=None,
            actual_value=actual,
            message=(
                f"Rule value is '{rule.evidence_status.value}'; it cannot be "
                "evaluated and does not silently pass."
            ),
        )

    # Informational / documentation rules never pass/fail a gate.
    if rule.operator in (Operator.INFORMATIONAL, Operator.REQUIRES):
        return RuleEvaluation(
            **base,
            evaluable=False,
            passed=None,
            actual_value=actual,
            message=(rule.value_text or rule.notes or "Informational rule."),
        )

    if actual is None:
        return RuleEvaluation(
            **base,
            evaluable=False,
            passed=None,
            actual_value=None,
            message=(
                f"Applicant value for '{rule.parameter_name}' is missing; the "
                "rule cannot be evaluated."
            ),
        )

    passed = evaluate_operator(rule, actual)
    if passed is None:
        return RuleEvaluation(
            **base,
            evaluable=False,
            passed=None,
            actual_value=actual,
            message="Rule could not be evaluated with the available values.",
        )

    return RuleEvaluation(
        **base,
        evaluable=True,
        passed=passed,
        actual_value=actual,
        message=_describe(rule, actual, passed),
    )


def _describe(rule: Rule, actual, passed: bool) -> str:
    req = _required_value(rule)
    verdict = "met" if passed else "not met"
    status = "" if rule.evidence_status == EvidenceStatus.VERIFIED_OFFICIAL else f" [{rule.evidence_status.value}]"
    return (
        f"{rule.parameter_name} {rule.operator.value} {req}: "
        f"actual={actual} -> {verdict}{status}"
    )


def evaluate_lender(
    lender: Lender,
    rules: List[Rule],
    profile: ApplicantProfile,
    derived: Optional[DerivedFeatures] = None,
) -> LenderOutcome:
    """Evaluate all rules for one lender and aggregate a decision."""
    values = fe.feature_values(profile, derived)

    failed: List[RuleEvaluation] = []
    unevaluable: List[RuleEvaluation] = []
    soft: List[RuleEvaluation] = []
    passed: List[RuleEvaluation] = []

    blocking_total = 0
    blocking_evaluated = 0
    has_official_failure = False
    has_review_trigger = False

    for rule in rules:
        if rule.lender_id != lender.lender_id:
            continue
        if not rule_applies(rule, profile):
            continue

        result = evaluate_rule(rule, profile, values)
        blocking = _is_blocking(rule)

        if blocking:
            blocking_total += 1

        if result.passed is True:
            passed.append(result)
            if blocking:
                blocking_evaluated += 1
        elif result.passed is False:
            if blocking and rule.is_verified_official:
                result.blocks_approval = True
                failed.append(result)
                blocking_evaluated += 1
                has_official_failure = True
            elif blocking:
                # Non-official (secondary/estimated) failure: never NO_GO alone.
                result.blocks_approval = False
                soft.append(result)
                has_review_trigger = True
            else:
                soft.append(result)
        else:
            # Not evaluable.
            if blocking:
                unevaluable.append(result)
                if rule.evidence_status in UNEVALUABLE_STATUSES:
                    has_review_trigger = True
                else:
                    # Missing applicant data for an otherwise documented gate.
                    has_review_trigger = True
            else:
                soft.append(result)

    if has_official_failure:
        decision = GateDecision.NO_GO
    elif has_review_trigger:
        decision = GateDecision.REVIEW_REQUIRED
    else:
        decision = GateDecision.GO

    coverage_warning = None
    if blocking_total == 0:
        coverage_warning = (
            "No mandatory blocking rules are recorded for this lender, so the "
            "decision cannot be treated as complete."
        )
        if decision == GateDecision.GO:
            decision = GateDecision.REVIEW_REQUIRED
    elif blocking_evaluated < blocking_total:
        coverage_warning = (
            f"Only {blocking_evaluated} of {blocking_total} mandatory rules were "
            "evaluated; the dataset is incomplete for this lender."
        )

    return LenderOutcome(
        lender_id=lender.lender_id,
        lender_name=lender.lender_name,
        product_name=lender.product_name,
        decision=decision,
        failed_gates=failed,
        unevaluable_mandatory=unevaluable,
        soft_flags=soft,
        passed_gates=passed,
        coverage_warning=coverage_warning,
        evaluated_mandatory_count=blocking_evaluated,
        total_mandatory_count=blocking_total,
        explanation=_explain(decision, failed, unevaluable, soft),
    )


def _explain(
    decision: GateDecision,
    failed: List[RuleEvaluation],
    unevaluable: List[RuleEvaluation],
    soft: List[RuleEvaluation],
) -> str:
    if decision == GateDecision.NO_GO:
        reasons = "; ".join(r.message for r in failed)
        return f"NO_GO: failed verified mandatory gate(s): {reasons}"
    if decision == GateDecision.REVIEW_REQUIRED:
        reasons = []
        if failed:
            reasons.append("non-official gate(s) flagged: " + "; ".join(r.message for r in failed))
        if unevaluable:
            reasons.append("unevaluable mandatory rule(s): " + "; ".join(r.message for r in unevaluable))
        if not reasons:
            reasons.append("incomplete rule coverage")
        return "REVIEW_REQUIRED: " + " | ".join(reasons)
    return (
        "GO: all applicable, researched, mandatory gates passed "
        f"({len(soft)} soft/informational note(s))."
    )


def evaluate_all(
    profile: ApplicantProfile,
    lenders: List[Lender],
    rules: List[Rule],
    derived: Optional[DerivedFeatures] = None,
) -> List[LenderOutcome]:
    rules_by_lender: Dict[str, List[Rule]] = {}
    for rule in rules:
        lid = getattr(rule, "lender_id")
        rules_by_lender.setdefault(lid, []).append(rule)
    return [
        evaluate_lender(lender, rules_by_lender.get(getattr(lender, "lender_id"), []), profile, derived)
        for lender in lenders
    ]


def applicant_outcome(outcomes: List[LenderOutcome]) -> ApplicantOutcome:
    """Aggregate lender decisions into a single applicant-level verdict."""
    if not outcomes:
        return ApplicantOutcome.INSUFFICIENT_INFORMATION
    if any(o.decision == GateDecision.GO for o in outcomes):
        return ApplicantOutcome.ELIGIBLE_UNDER_DOCUMENTED_RULES
    if all(o.decision == GateDecision.NO_GO for o in outcomes):
        return ApplicantOutcome.NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES
    return ApplicantOutcome.INSUFFICIENT_INFORMATION
