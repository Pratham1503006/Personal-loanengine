"""Typed schemas for the eligibility engine.

These pydantic models define the contract between the data files
(``data/*.csv``), the applicant input, and every downstream module. They are
deliberately explicit about optionality so that *unknown* values stay ``None``
rather than silently becoming zero.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceStatus(str, Enum):
    """Controlled vocabulary describing how well a rule is supported."""

    VERIFIED_OFFICIAL = "verified_official"
    VERIFIED_SECONDARY = "verified_secondary"
    ESTIMATED = "estimated"
    NOT_PUBLISHED = "not_published"
    NOT_RESEARCHED = "not_researched"
    UNVERIFIED = "unverified"
    STALE = "stale"


#: Evidence statuses that are considered *verified* evidence.
VERIFIED_STATUSES = {EvidenceStatus.VERIFIED_OFFICIAL, EvidenceStatus.VERIFIED_SECONDARY}
#: Evidence statuses that carry no usable numeric/rule value.
UNKNOWN_VALUE_STATUSES = {
    EvidenceStatus.NOT_PUBLISHED,
    EvidenceStatus.NOT_RESEARCHED,
    EvidenceStatus.UNVERIFIED,
}


class RuleCategory(str, Enum):
    GO_NO_GO = "GO_NO_GO"
    CREDIT_BUREAU = "CREDIT_BUREAU"
    INCOME_AND_EMPLOYMENT = "INCOME_AND_EMPLOYMENT"
    AFFORDABILITY = "AFFORDABILITY"
    LOAN_AMOUNT = "LOAN_AMOUNT"
    PRICING = "PRICING"
    TENURE = "TENURE"
    FEES = "FEES"
    DOCUMENTATION = "DOCUMENTATION"
    PRODUCT_AVAILABILITY = "PRODUCT_AVAILABILITY"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"


class RuleType(str, Enum):
    HARD_GATE = "hard_gate"
    SOFT_THRESHOLD = "soft_threshold"
    PRODUCT_CONSTRAINT = "product_constraint"
    PRICING_BAND = "pricing_band"
    DOCUMENTATION_REQUIREMENT = "documentation_requirement"
    DERIVED_ASSUMPTION = "derived_assumption"


class Operator(str, Enum):
    GE = ">="
    LE = "<="
    EQ = "=="
    IN = "in"
    RANGE = "range"
    REQUIRES = "requires"
    INFORMATIONAL = "informational"


class GateDecision(str, Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ApplicantOutcome(str, Enum):
    ELIGIBLE_UNDER_DOCUMENTED_RULES = "ELIGIBLE_UNDER_DOCUMENTED_RULES"
    NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES = "NOT_ELIGIBLE_UNDER_DOCUMENTED_RULES"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class EmploymentType(str, Enum):
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"
    OTHER = "other"


class CustomerSegment(str, Enum):
    NEW_CUSTOMER = "new_customer"
    EXISTING_CUSTOMER = "existing_customer"
    PREAPPROVED = "preapproved"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def _parse_date(value):
    """Parse an ISO date string, returning ``None`` for blanks/NaN."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "nat", "none", "null"}:
        return None
    return date.fromisoformat(text)


class Source(BaseModel):
    """A single research source (row in ``source_registry.csv``)."""

    model_config = ConfigDict(extra="ignore")

    source_id: str
    lender_id: Optional[str] = None
    source_title: str
    source_url: str
    source_type: str
    publisher: Optional[str] = None
    published_or_effective_date: Optional[date] = None
    accessed_date: date
    supports_rule_ids: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("published_or_effective_date", "accessed_date", mode="before")
    @classmethod
    def _coerce_dates(cls, v):
        return _parse_date(v)


class Lender(BaseModel):
    """A candidate lender / product (row in ``lenders.csv``)."""

    model_config = ConfigDict(extra="ignore")

    lender_id: str
    lender_name: str
    lender_type: Literal["bank", "nbfc", "digital_platform"]
    regulated_entity_name: str
    product_name: str
    official_product_url: Optional[str] = None
    product_status: Literal["verified_active", "unverified", "not_found"]
    selection_rationale: Optional[str] = None
    last_verified_date: Optional[date] = None
    research_status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("last_verified_date", mode="before")
    @classmethod
    def _coerce_date(cls, v):
        return _parse_date(v)


class Rule(BaseModel):
    """A single documented or assumed lender rule (row in ``lender_rules.csv``)."""

    model_config = ConfigDict(extra="ignore")

    rule_id: str
    lender_id: str
    product_name: Optional[str] = None
    parameter_name: str
    rule_category: RuleCategory
    rule_type: RuleType
    operator: Operator
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    unit: Optional[str] = None
    employment_segment: Optional[str] = None
    customer_segment: Optional[str] = None
    mandatory: bool = False
    evidence_status: EvidenceStatus
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    accessed_date: Optional[date] = None
    effective_date: Optional[date] = None
    confidence: Optional[Confidence] = None
    assumption_description: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("mandatory", mode="before")
    @classmethod
    def _coerce_bool(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        return str(v).strip().lower() in {"1", "true", "yes", "y", "t"}

    @field_validator("accessed_date", "effective_date", mode="before")
    @classmethod
    def _coerce_dates(cls, v):
        return _parse_date(v)

    @property
    def is_verified_official(self) -> bool:
        return self.evidence_status == EvidenceStatus.VERIFIED_OFFICIAL

    @property
    def is_verified(self) -> bool:
        return self.evidence_status in VERIFIED_STATUSES

    @property
    def has_known_value(self) -> bool:
        """True when the rule carries a usable threshold/value."""
        if self.evidence_status in UNKNOWN_VALUE_STATUSES:
            return False
        return any(
            v is not None
            for v in (self.value_numeric, self.value_text, self.range_min, self.range_max)
        )

    @property
    def applies_to_segment(self) -> Optional[str]:
        seg = (self.employment_segment or "").strip().lower()
        return seg or None


class ApplicantProfile(BaseModel):
    """Applicant input. Every field is optional so partial data is allowed.

    No direct personal identifiers (PAN, Aadhaar, account numbers) are part of
    this schema on purpose.
    """

    model_config = ConfigDict(extra="forbid")

    applicant_id: Optional[str] = None
    synthetic: bool = False

    # Identity / requested product
    applicant_age_years: Optional[int] = Field(default=None, ge=0, le=150)
    residence_country: Optional[str] = None
    city: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    customer_segment: Optional[CustomerSegment] = None
    requested_loan_amount_inr: Optional[float] = Field(default=None, ge=0)
    requested_tenure_months: Optional[int] = Field(default=None, ge=1, le=600)

    # Salaried
    monthly_net_income_inr: Optional[float] = Field(default=None, ge=0)
    monthly_gross_income_inr: Optional[float] = Field(default=None, ge=0)
    current_job_tenure_months: Optional[int] = Field(default=None, ge=0)
    total_work_experience_months: Optional[int] = Field(default=None, ge=0)
    employer_category: Optional[str] = None
    salary_credit_consistency: Optional[str] = None

    # Self-employed
    annual_itr_income_inr: Optional[float] = Field(default=None, ge=0)
    itr_years_available: Optional[int] = Field(default=None, ge=0)
    business_vintage_months: Optional[int] = Field(default=None, ge=0)
    monthly_business_revenue_inr: Optional[float] = Field(default=None, ge=0)
    monthly_business_profit_inr: Optional[float] = Field(default=None, ge=0)

    # Bureau / credit
    cibil_score: Optional[int] = Field(default=None, ge=300, le=900)
    credit_history_months: Optional[int] = Field(default=None, ge=0)
    active_loan_count: Optional[int] = Field(default=None, ge=0)
    credit_enquiries_6m: Optional[int] = Field(default=None, ge=0)
    overdue_amount_inr: Optional[float] = Field(default=None, ge=0)
    days_past_due_max: Optional[int] = Field(default=None, ge=0)
    written_off_accounts_count: Optional[int] = Field(default=None, ge=0)
    settled_accounts_count: Optional[int] = Field(default=None, ge=0)
    credit_card_utilisation_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # Affordability
    existing_monthly_emi_inr: Optional[float] = Field(default=None, ge=0)
    other_monthly_debt_obligations_inr: Optional[float] = Field(default=None, ge=0)

    def gated_value(self, parameter_name: str):
        """Return the applicant value a rule keyed on ``parameter_name`` uses.

        Derived parameters are computed lazily by
        :mod:`loan_engine.feature_engineering` and injected via
        :meth:`with_derived`.
        """
        return getattr(self, parameter_name, None)


class DerivedFeatures(BaseModel):
    """Values derived from an :class:`ApplicantProfile` (never raw input)."""

    model_config = ConfigDict(extra="allow")

    total_monthly_obligations_inr: Optional[float] = None
    monthly_income_for_foir_inr: Optional[float] = None
    foir_pct: Optional[float] = None
    available_emi_inr: Optional[float] = None


class RuleEvaluation(BaseModel):
    """Outcome of evaluating a single rule against an applicant."""

    rule_id: str
    lender_id: str
    parameter_name: str
    rule_category: RuleCategory
    rule_type: RuleType
    mandatory: bool
    evidence_status: EvidenceStatus
    applied: bool
    evaluable: bool
    passed: Optional[bool] = None
    actual_value: Optional[object] = None
    required_value: Optional[object] = None
    operator: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    accessed_date: Optional[date] = None
    message: str = ""
    is_verified_official: bool = False
    blocks_approval: bool = False


class LenderOutcome(BaseModel):
    """Aggregated evaluation outcome for one lender."""

    lender_id: str
    lender_name: str
    product_name: str
    decision: GateDecision
    failed_gates: List[RuleEvaluation] = Field(default_factory=list)
    unevaluable_mandatory: List[RuleEvaluation] = Field(default_factory=list)
    soft_flags: List[RuleEvaluation] = Field(default_factory=list)
    passed_gates: List[RuleEvaluation] = Field(default_factory=list)
    coverage_warning: Optional[str] = None
    evaluated_mandatory_count: int = 0
    total_mandatory_count: int = 0
    explanation: str = ""
