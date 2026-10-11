from loan_engine import affordability, schemas

def test_foir_basic():
    p = schemas.ApplicantProfile(monthly_net_income_inr=50000, existing_monthly_emi_inr=10000)
    sc = affordability.affordability_scenario(p)
    assert sc is not None
