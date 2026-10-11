"""Derived applicant features.

Nothing here is a lender rule: the functions compute applicant-side values
(obligations, an income denominator, FOIR) using explicitly documented
assumptions. Where a defensible input is missing the result is ``None`` —
never zero.
"""

from __future__ import annotations

from typing import Dict, Optional

from .schemas import ApplicantProfile, DerivedFeatures

#: Documented assumption id for the income denominator used in FOIR.
FOIR_DENOMINATOR_ASSUMPTION = "ASSUMPTION-FOIR-DENOMINATOR"


def total_monthly_obligations(profile: ApplicantProfile) -> Optional[float]:
    """Sum of existing EMIs and other monthly debt obligations.

    Returns ``None`` only when *both* components are unknown, so that a single
    known obligation still contributes rather than being discarded.
    """
    emi = profile.existing_monthly_emi_inr
    other = profile.other_monthly_debt_obligations_inr
    if emi is None and other is None:
        return None
    return float(emi or 0.0) + float(other or 0.0)


def monthly_income_for_foir(profile: ApplicantProfile) -> Optional[float]:
    """Choose a monthly income denominator for FOIR/affordability scenarios.

    Method (ASSUMPTION-FOIR-DENOMINATOR):
      * salaried  -> ``monthly_net_income_inr`` (take-home pay).
      * self_employed -> ``annual_itr_income_inr / 12`` if available, else
        ``monthly_business_profit_inr``.
      * other -> net income, then profit, then ITR/12, first non-null.

    Lenders define the denominator differently; this is a transparent,
    configurable model assumption, not a claim about any lender's formula.
    """
    et = _employment_value(profile.employment_type)
    net = profile.monthly_net_income_inr
    profit = profile.monthly_business_profit_inr
    itr = profile.annual_itr_income_inr
    itr_monthly = (itr / 12.0) if itr is not None else None

    if et == "salaried":
        return net
    if et == "self_employed":
        return itr_monthly if itr_monthly is not None else profit
    for candidate in (net, profit, itr_monthly):
        if candidate is not None:
            return candidate
    return None


def foir_pct(
    profile: ApplicantProfile,
    income_denominator: Optional[float] = None,
) -> Optional[float]:
    """FOIR% = total monthly obligations / income denominator * 100.

    ``None`` when obligations or denominator are unknown.
    """
    denom = income_denominator if income_denominator is not None else monthly_income_for_foir(profile)
    obligations = total_monthly_obligations(profile)
    if denom is None or denom <= 0 or obligations is None:
        return None
    return obligations / denom * 100.0


def compute_derived(
    profile: ApplicantProfile,
    foir_fraction: Optional[float] = None,
) -> DerivedFeatures:
    """Build the derived feature bundle for a profile.

    ``foir_fraction`` is an optional *scenario* FOIR cap (e.g. 0.5 for 50%)
    used only to illustrate available EMI; it is never applied as a lender
    rule unless a verified rule supplies it.
    """
    denom = monthly_income_for_foir(profile)
    obligations = total_monthly_obligations(profile)
    available = None
    if foir_fraction is not None and denom is not None:
        available = max(0.0, denom * foir_fraction - (obligations or 0.0))
    return DerivedFeatures(
        total_monthly_obligations_inr=obligations,
        monthly_income_for_foir_inr=denom,
        foir_pct=foir_pct(profile, denom),
        available_emi_inr=available,
    )


def feature_values(
    profile: ApplicantProfile,
    derived: Optional[DerivedFeatures] = None,
    foir_fraction: Optional[float] = None,
) -> Dict[str, object]:
    """Flat mapping of parameter name -> value for rule evaluation."""
    derived = derived or compute_derived(profile, foir_fraction)
    values: Dict[str, object] = dict(profile.model_dump())
    values.update(derived.model_dump())
    return values


def _employment_value(et) -> Optional[str]:
    if et is None:
        return None
    return getattr(et, "value", str(et)).strip().lower()
