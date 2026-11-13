import json
import pytest
from lab import *

def test_generation_and_checks():
    rows=benchmark()
    validate(rows)
    assert rows==benchmark() and len(rows)==300
    row=next(r for r in rows if r["task"]=="Extraction")
    assert grade(row,row["reference"])[0]==100
    assert grade(row,"not json")[0]==0
    assert grade(row,'{"invoice":"INV-1001","total":false}')[0]<100
    with pytest.raises(ValueError): validate(rows+rows[:1])

def test_snapshot_and_review_history():
    db=connect(":memory:")
    v=dataset(db,"example",benchmark(3))
    rid=run(db,v,RECIPES[0],100)
    old=db.execute("SELECT body FROM runs").fetchone()[0]
    review(db,rid,"1-001",60,"Ambiguous","Partial credit")
    review(db,rid,"1-001",80,"Clarity","Second opinion")
    assert db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]==2
    assert db.execute("SELECT body FROM runs").fetchone()[0]==old
    with pytest.raises(ValueError): review(db,rid,"absent",80,"Clarity","Invalid case")
    changed=benchmark(3); changed[0]["A"]="new answer"
    assert dataset(db,"changed",changed)!=v
