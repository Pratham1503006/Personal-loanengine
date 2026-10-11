from loan_engine import validation, schemas


def test_validate_basic_profile():
    profile = {
        "applicant_age_years": 30,
        "monthly_net_income_inr": 50000,
        "requested_loan_amount_inr": 500000,
        "requested_tenure_months": 36,
    }
    result = validation.validate_profile(schemas.ApplicantProfile(**profile))
    assert result.is_valid