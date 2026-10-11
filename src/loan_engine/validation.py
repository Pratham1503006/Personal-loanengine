"""Applicant input validation.

Validation is done through pydantic's field constraints where possible
(see :class:`loan_engine.schemas.ApplicantProfile`). This module adds the
*cross-field* and *business* rules that a field type cannot express, and
returns human-readable messages instead of raising, so the UI/CLI can show
them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import ValidationError

from .schemas import ApplicantProfile, EmploymentType

MAX_LOAN_AMOUNT_INR = 10_000_000
MAX_TENURE_MONTHS = 600
MIN_AGE = 18


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_profile(profile: ApplicantProfile) -> ValidationResult:
    """Validate an already-constructed profile for business-rule violations."""
    result = ValidationResult()

    # Requested product plausibility (prototype guard-rails, not lender rules).
    amt = profile.requested_loan_amount_inr
    if amt is not None:
        if amt <= 0:
            result.add_error("requested_loan_amount_inr must be greater than 0.")
        elif amt > MAX_LOAN_AMOUNT_INR:
            result.add_error(
                f"requested_loan_amount_inr ({amt:,.0f}) exceeds the prototype "
                f"guard-rail of {MAX_LOAN_AMOUNT_INR:,}."
            )

    tenure = profile.requested_tenure_months
    if tenure is not None and tenure > MAX_TENURE_MONTHS:
        result.add_error(
            f"requested_tenure_months ({tenure}) exceeds the prototype bound "
            f"of {MAX_TENURE_MONTHS} months."
        )

    # Age sanity.
    age = profile.applicant_age_years
    if age is not None and age < MIN_AGE:
        result.add_error(f"applicant_age_years must be at least {MIN_AGE}.")

    # Employment-specific income consistency.
    et = _employment_value(profile.employment_type)
    if et == "salaried":
        if profile.monthly_net_income_inr is None:
            result.add_warning(
                "Salaried applicant has no monthly_net_income_inr; income-based "
                "gates will be unevaluable (REVIEW_REQUIRED)."
            )
        if profile.monthly_gross_income_inr is not None and profile.monthly_net_income_inr is not None:
            if profile.monthly_gross_income_inr < profile.monthly_net_income_inr:
                result.add_warning(
                    "monthly_gross_income_inr is lower than monthly_net_income_inr; "
                    "please confirm the figures."
                )
    elif et == "self_employed":
        if profile.annual_itr_income_inr is None and profile.monthly_business_profit_inr is None:
            result.add_warning(
                "Self-employed applicant has neither annual_itr_income_inr nor "
                "monthly_business_profit_inr; income-based gates will be unevaluable."
            )
        if profile.monthly_business_revenue_inr is not None and profile.monthly_business_profit_inr is not None:
            if profile.monthly_business_profit_inr > profile.monthly_business_revenue_inr:
                result.add_warning(
                    "monthly_business_profit_inr exceeds monthly_business_revenue_inr; "
                    "revenue, profit and ITR income are distinct concepts."
                )

    # Obligations vs income sanity (only warning; never reject on estimate).
    if (
        profile.existing_monthly_emi_inr is not None
        and profile.monthly_net_income_inr is not None
        and profile.existing_monthly_emi_inr > profile.monthly_net_income_inr
    ):
        result.add_warning(
            "existing_monthly_emi_inr exceeds monthly_net_income_inr; FOIR will "
            "exceed 100% and no affordable EMI may remain."
        )

    # Bureau internal consistency.
    if (
        profile.days_past_due_max is not None
        and profile.days_past_due_max > 0
        and profile.cibil_score is not None
        and profile.cibil_score >= 800
    ):
        result.add_warning(
            "A very high CIBIL score alongside a recent days-past-due amount is "
            "unusual; please confirm bureau figures."
        )

    return result


def _employment_value(et) -> Optional[str]:
    if et is None:
        return None
    if isinstance(et, EmploymentType):
        return et.value
    return str(et).strip().lower()


def parse_and_validate(payload: dict) -> tuple[Optional[ApplicantProfile], ValidationResult]:
    """Build a profile from a dict, catching pydantic field errors."""
    try:
        profile = ApplicantProfile(**payload)
    except ValidationError as exc:
        result = ValidationResult()
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            result.add_error(f"{loc}: {err['msg']}")
        return None, result

    result = validate_profile(profile)
    return profile, result
