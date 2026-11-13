import json
import pytest
from workflow import *

def test_packet_limits_and_missing_data():
    for raw,name in [(b"x"*65537,"packet.json"),(b"{}","packet.exe"),(b"[]","packet.json"),(b'{"unknown":{}}',"packet.json")]:
        with pytest.raises(ValueError): parse(raw,name)
    rec=example(2); rec["documents"]={}
    assert risk(assess(rec,POLICY,"2026-01-01"))=="Requires Manual Review"

def test_correction_decision_and_history():
    db=connect(":memory:"); rec=example(4)
    cid=submit(db,rec,POLICY,REVIEWERS[0])
    docs=rec["documents"]; docs["address"]["address"]=rec["declared"]["address"]
    change(db,cid,1,"Replace documents",REVIEWERS[0],"Corrected address",docs)
    change(db,cid,2,"Approve",REVIEWERS[1],"Evidence checked")
    with pytest.raises(ValueError): change(db,cid,3,"Reject",REVIEWERS[1],"Invalid transition")
    with pytest.raises(ValueError): change(db,cid,2,"Reopen",REVIEWERS[1],"Stale")
    with pytest.raises(ValueError): change(db,cid,3,"Reopen",REVIEWERS[1]," ")
    trail=db.execute("SELECT * FROM audit ORDER BY id").fetchall()
    assert [r["status"] for r in trail]==["Requires review","Pending","Approved"]
    assert json.loads(trail[0]["snapshot"])["record"]["documents"]["address"]!=docs["address"]
    change(db,cid,3,"Reopen",REVIEWERS[0],"New evidence")

def test_seed_and_policy():
    db=connect(":memory:"); seed(db); seed(db)
    assert db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]==40
    assert risk(assess(example(4),dict(POLICY,address=False),"2026-01-01"))=="Low"
