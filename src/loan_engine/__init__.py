"""India Personal Loan Eligibility & Recommendation Engine.

A transparent, rule-based (no machine learning) engine that evaluates a
synthetic or user-entered applicant profile against publicly documented
lender rules for unsecured personal loans in India, and recommends feasible
options with a full explanation.

The package is intentionally free of any UI dependency so the engine can be
driven from the command line, tests, or a Streamlit front-end.
"""

from .schemas import (
    ApplicantProfile,
    EvidenceStatus,
    GateDecision,
    Lender,
    LenderOutcome,
    Rule,
    RuleCategory,
    RuleType,
    Source,
)

__all__ = [
    "ApplicantProfile",
    "EvidenceStatus",
    "GateDecision",
    "Lender",
    "LenderOutcome",
    "Rule",
    "RuleCategory",
    "RuleType",
    "Source",
]

__version__ = "0.1.0"
