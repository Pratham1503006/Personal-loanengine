from loan_engine import rule_engine, schemas, data_loader, feature_engineering


def test_missing_data_review_required():
    lenders = data_loader.load_lenders()
    rules = data_loader.load_rules()
    sources = data_loader.load_sources()
    profile = schemas.ApplicantProfile(monthly_net_income_inr=30000)
    derived = feature_engineering.compute_derived(profile)
    results = rule_engine.evaluate_all(profile, lenders, rules, derived)
    assert len(results) > 0
