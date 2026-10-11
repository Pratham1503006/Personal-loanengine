from loan_engine import data_loader

def test_datasets_load():
    l=data_loader.load_lenders()
    r=data_loader.load_rules()
    s=data_loader.load_sources()
    assert len(l)>0
    assert len(s)>0
