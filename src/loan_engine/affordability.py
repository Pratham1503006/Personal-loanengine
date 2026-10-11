"""Affordability helpers: FOIR and available-EMI scenarios.

These are applicant-side calculations gated by *configurable scenario
assumptions*. A FOIR fraction is only treated as a lender rule when a verified
rule supplies it; otherwise it is a clearly labelled scenario input.
"""

from __future__ import annotations

from typing import List, Optional

from . import loan_calculator as lc
from .schemas import ApplicantProfile
from .feature_engineering import (
    foir_pct as _foir_pct,
    monthly_income_for_foir,
    total_monthly_obligations,
)

#: Scenario FOIR caps used ONLY to illustrate affordability. These are NOT
#: presented as lender policy. See docs/assumptions.md.
DEFAULT_SCENARIO_FOIR = 0.50
SCENARIO_FOIR_LADDER: List[float] = [0.40, 0.50, 0.60]


def foir_fraction(
    obligations: Optional[float],
    income: Optional[float],
) -> Optional[float]:
    """FOIR as a *fraction* (0-1+). ``None`` when it cannot be computed."""
    if obligations is None or income is None or income <= 0:
        return None
    return obligations / income


def available_emi(
    income: Optional[float],
    existing_obligations: Optional[float],
    foir_cap_fraction: float,
) -> Optional[float]:
    """``available_emi = max(0, income * foir_cap - existing_obligations)``.

    ``None`` when income is unknown (we refuse to assume a denominator).
    If obligations are unknown they are treated as 0 for the *scenario*, but
    callers should surface that assumption.
    """
    if income is None or foir_cap_fraction is None:
        return None
    obligations = existing_obligations if existing_obligations is not None else 0.0
    return max(0.0, income * foir_cap_fraction - obligations)


def affordability_scenario(
    profile: ApplicantProfile,
    foir_cap_fraction: float = DEFAULT_SCENARIO_FOIR,
    annual_rate_pct: Optional[float] = None,
    tenure_months: Optional[int] = None,
) -> dict:
    """Compute a single affordability scenario for a profile.

    Returns income denominator, obligations, FOIR, available EMI and (if a
    rate/tenure are supplied) the principal that available EMI could support.
    """
    income = monthly_income_for_foir(profile)
    obligations = total_monthly_obligations(profile)
    available = available_emi(income, obligations, foir_cap_fraction)
    principal = None
    if available is not None and annual_rate_pct is not None and tenure_months is not None:
        principal = lc.max_principal_from_available_emi(available, annual_rate_pct, tenure_months)
    return {
        "income_denominator_inr": income,
        "obligations_inr": obligations,
        "foir_cap_fraction": foir_cap_fraction,
        "foir_fraction_actual": foir_fraction(obligations, income),
        "foir_pct_actual": _foir_pct(profile, income),
        "available_emi_inr": available,
        "affordability_principal_inr": principal,
        "assumptions": [
            "Scenario FOIR cap is a model assumption, not a lender-published rule "
            "unless flagged otherwise.",
            "Income denominator is an assumption (see ASSUMPTION-FOIR-DENOMINATOR).",
        ],
    }


def affordability_ladder(
    profile: ApplicantProfile,
    annual_rate_pct: Optional[float] = None,
    tenure_months: Optional[int] = None,
    caps: Optional[List[float]] = None,
) -> List[dict]:
    """Affordability under several scenario FOIR caps."""
    caps = caps or SCENARIO_FOIR_LADDER
    return [
        affordability_scenario(profile, cap, annual_rate_pct, tenure_months)
        for cap in caps
    ]
