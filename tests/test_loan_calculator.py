from loan_engine import loan_calculator

def test_emi_calculator():
    e = loan_calculator.emi(100000, 10.0, 36)
    assert e > 0
