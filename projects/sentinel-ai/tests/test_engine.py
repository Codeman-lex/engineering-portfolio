from datetime import timedelta
import numpy as np
import pandas as pd
import pytest

from sentinel.analytics import filter_rows, summary
from sentinel.data import generate, validate
from sentinel.detection import classify, contributions, features, metrics, train
from sentinel.storage import case, database, initialize, load, save


@pytest.fixture(scope="module")
def events():
    return generate(2400)


def test_repeatable_and_prior():
    d = generate(150)
    pd.testing.assert_frame_equal(d,generate(150))
    assert d.timestamp.is_monotonic_increasing
    assert d.previous_timestamp.equals(d.groupby("customer_id").timestamp.shift())
    for _, g in d.groupby("customer_id"):
        for i,row in enumerate(g.itertuples()):
            assert row.recent_count == (g.timestamp.iloc[:i]>=row.timestamp.to_pydatetime()-timedelta(hours=1)).sum()


@pytest.mark.parametrize("error",["missing","duplicate","negative","date"])
def test_validation(events,error):
    d = events.head(5).copy()
    if error=="missing":
        d.loc[0,"customer_id"]=None
    if error=="duplicate":
        d.loc[0,"transaction_id"]=d.loc[1,"transaction_id"]
    if error=="negative":
        d.loc[0,"amount"]=-1
    if error=="date":
        d["timestamp"]="invalid"
    with pytest.raises(ValueError):
        validate(d)


def test_thresholds_and_rules(events):
    assert list(classify([0,24,25,50,75,100]))==["Low Risk","Low Risk","Medium Risk","High Risk","Critical Risk","Critical Risk"]
    with pytest.raises(ValueError):
        classify([1],(5,4,3))
    d=events.head(1).assign(amount=300,historical_average=100,recent_count=2,new_device=1,
                            ip_country="ZZZ",new_beneficiary=1,international=1,account_age=1)
    assert contributions(d).sum(axis=1).item()==113
    assert contributions(d,[0]*7).sum(axis=1).item()==0


def test_model(events):
    m=train(events)
    test=events[events.timestamp>=m.cutoff].copy()
    test["ip_country"]="UNSEEN"
    a,p=m.predict(test)
    assert np.all((0<=a)&(a<=100)) and np.all((0<=p)&(p<=1))
    changed=test.assign(fraud_label=0,risk_score=100,status="Example")
    pd.testing.assert_frame_equal(features(test),features(changed))
    assert metrics([0,1],[1,1])["FP"]==1


def test_database_and_filters(tmp_path):
    engine=database(tmp_path/"demo.db")
    initialize(engine,500)
    initialize(engine,500)
    d=load(engine)
    assert len(d)==500
    tx=d.iloc[0].transaction_id
    found=filter_rows(d, dates=[d.timestamp.min().date()]*2, amounts=(0,100000),search=tx.lower())
    assert list(found.transaction_id)==[tx]
    assert summary(filter_rows(d,selections={"origin":["unknown"]}))["total"]==0
    save(engine,tx,"Escalated","Review device",0)
    assert case(database(tmp_path/"demo.db"),tx)["notes"]=="Review device"
    with pytest.raises(ValueError):
        save(engine,tx,"Resolved","stale",0)
    with pytest.raises(ValueError):
        save(engine,"absent","Resolved","",0)
