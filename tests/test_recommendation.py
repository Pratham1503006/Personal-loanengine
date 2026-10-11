from loan_engine import recommendation, schemas, data_loader, feature_engineering, rule_engine

def test_recommend_runs():
    l=data_loader.load_lenders()
    r=data_loader.load_rules()
    p=schemas.ApplicantProfile(monthly_net_income_inr=50000, requested_loan_amount_inr=500000, requested_tenure_months=36, applicant_age_years=30, cibil_score=750)
    d=feature_engineering.compute_derived(p)
    out=rule_engine.evaluate_all(p,l,r,d)
    rec=recommendation.recommend(p,l,out,r)
    assert rec is not None
