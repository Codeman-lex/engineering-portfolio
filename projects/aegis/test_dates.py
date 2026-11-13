from workflow import example,assess,POLICY

def test_unparsed_date_cannot_pass():
    row=example(2)
    row["documents"]["identity"]["expires"]="current"
    checks=assess(row,POLICY,"2026-01-01")
    assert not next(x for x in checks if x["rule"]=="Identity validity")["passed"]
