"""Pure annuity math for EMI and principal estimates.

All functions are side-effect free and validate their inputs. Rates are
*annual nominal* percentages unless a function name says otherwise; they are
converted with ``annual_rate / 12 / 100``. Rounding is left to the caller /
display layer — intermediate results are never rounded.
"""

from __future__ import annotations

import math
from typing import Optional


class InvalidLoanInput(ValueError):
    """Raised when loan math is requested with impossible inputs."""


def _monthly_rate(annual_rate_pct: float) -> float:
    return annual_rate_pct / 12.0 / 100.0


def emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Equated Monthly Instalment.

    ``emi = P*r*(1+r)^n / ((1+r)^n - 1)`` and ``emi = P/n`` when ``r == 0``.
    """
    if principal is None or annual_rate_pct is None or tenure_months is None:
        raise InvalidLoanInput("principal, annual_rate_pct and tenure_months are required.")
    if principal < 0:
        raise InvalidLoanInput("principal must be >= 0.")
    if annual_rate_pct < 0:
        raise InvalidLoanInput("annual_rate_pct must be >= 0.")
    if tenure_months <= 0:
        raise InvalidLoanInput("tenure_months must be > 0.")

    r = _monthly_rate(annual_rate_pct)
    if r == 0:
        return principal / tenure_months
    factor = (1 + r) ** tenure_months
    return principal * r * factor / (factor - 1)


def principal_from_emi(emi_amount: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Maximum principal supported by ``emi_amount`` over ``tenure_months``.

    Inverse of :func:`emi`: ``P = M*(1-(1+r)^-n)/r`` and ``P = M*n`` if ``r == 0``.
    """
    if emi_amount is None or annual_rate_pct is None or tenure_months is None:
        raise InvalidLoanInput("emi_amount, annual_rate_pct and tenure_months are required.")
    if emi_amount < 0:
        raise InvalidLoanInput("emi_amount must be >= 0.")
    if annual_rate_pct < 0:
        raise InvalidLoanInput("annual_rate_pct must be >= 0.")
    if tenure_months <= 0:
        raise InvalidLoanInput("tenure_months must be > 0.")

    r = _monthly_rate(annual_rate_pct)
    if r == 0:
        return emi_amount * tenure_months
    return emi_amount * (1 - (1 + r) ** (-tenure_months)) / r


def total_repayment(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """Sum of all EMIs over the life of the loan (nominal, no fees)."""
    return emi(principal, annual_rate_pct, tenure_months) * tenure_months


def total_interest(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    return total_repayment(principal, annual_rate_pct, tenure_months) - principal


def emi_range(
    principal: float,
    min_rate_pct: Optional[float],
    max_rate_pct: Optional[float],
    tenure_months: int,
) -> dict:
    """EMI at the published rate endpoints.

    Any endpoint that is unknown yields ``None`` for that side rather than a
    guess. Returns a dict with ``min_rate_emi``, ``max_rate_emi`` and the
    corresponding rates.
    """
    low = emi(principal, min_rate_pct, tenure_months) if min_rate_pct is not None else None
    high = emi(principal, max_rate_pct, tenure_months) if max_rate_pct is not None else None
    lo, hi = None, None
    emis = [e for e in (low, high) if e is not None]
    if emis:
        lo, hi = min(emis), max(emis)
    return {
        "principal": principal,
        "tenure_months": tenure_months,
        "min_rate_pct": min_rate_pct,
        "max_rate_pct": max_rate_pct,
        "min_rate_emi": low,
        "max_rate_emi": high,
        "emi_low": lo,
        "emi_high": hi,
    }


def max_principal_from_available_emi(
    available_emi: float,
    annual_rate_pct: Optional[float],
    tenure_months: int,
) -> Optional[float]:
    """Principal supported by an available EMI; ``None`` if rate/tenure unknown."""
    if available_emi is None or annual_rate_pct is None or tenure_months is None:
        return None
    if available_emi <= 0:
        return 0.0
    return principal_from_emi(available_emi, annual_rate_pct, tenure_months)


def present_value_of_emi_stream(
    emi_amount: float,
    annual_rate_pct: float,
    tenure_months: int,
) -> float:
    """Alias used in docs for the principal-from-EMI discounting formula."""
    return principal_from_emi(emi_amount, annual_rate_pct, tenure_months)


def safe_emi(principal: float, annual_rate_pct: Optional[float], tenure_months: Optional[int]):
    """Return EMI or ``None`` instead of raising (used by the reporting layer)."""
    try:
        if annual_rate_pct is None or tenure_months is None:
            return None
        return emi(principal, annual_rate_pct, tenure_months)
    except (InvalidLoanInput, TypeError):
        return None
