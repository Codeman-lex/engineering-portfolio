"""Versioned synthetic benchmarks, deterministic scoring and experiment snapshots."""
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone

TASKS = ["Factual QA", "Extraction", "Instructions", "Business analysis", "Uncertainty"]
VERSION = "1.0"
RECIPES = ["Direct answer", "Evidence first"]


def benchmark(n=60):
    cases=[]
    for i in range(1,n+1):
        ref=f"INV-{1000+i}"
        total=117+i*13
        city=["Luma","Tern","Fenn"][i%3]
        inputs=[
            (f"Which depot handles {ref}?",f"Dispatch register: {ref} is assigned to {city}.",city,"Orin"),
            ("Return invoice and total as a JSON object.",f"Invoice {ref}; total USD {total}.",
             json.dumps({"invoice":ref,"total":total}),json.dumps({"invoice":ref,"total":total+10})),
            ("Return only the routing code in uppercase.",f"Routing code: rt-{i:03}.",f"RT-{i:03}",f"Code: RT-{i:03}"),
            ("Report the change in units as one signed integer.",f"Opening units {total}; closing units {total+i}.",f"+{i}",f"-{i}"),
            ("Which reviewer authorized this order? Reply UNKNOWN if unspecified.",f"Order {ref} is recorded. Reviewer field is blank.","UNKNOWN","Reviewer K")]
        for j,(task,(prompt,doc,answer,wrong)) in enumerate(zip(TASKS,inputs)):
            cases.append(dict(id=f"{j+1}-{i:03}",task=task,prompt=prompt,evidence=doc,reference=answer,
                              A=wrong if (i+j)%3==0 else answer,B=wrong if (i+2*j)%7==0 else answer))
    return cases


def validate(cases):
    if not isinstance(cases,list) or not 1<=len(cases)<=2000:
        raise ValueError("Provide 1–2,000 test cases.")
    ids=set()
    for row in cases:
        if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not 0<len(row[k])<=8000 for k in ("id","task","prompt","evidence","reference","A","B")):
            raise ValueError("Each case needs an ID, task, prompt, evidence, reference and two text fixtures.")
        if row["id"] in ids or row["task"] not in TASKS:
            raise ValueError("Duplicate ID or unknown task.")
        ids.add(row["id"])
        if row["task"]=="Extraction":
            try: obj=json.loads(row["reference"])
            except ValueError: raise ValueError("Extraction reference must be JSON.") from None
            if not isinstance(obj,dict) or not obj: raise ValueError("Expected a nonempty reference object.")
        if row["task"]=="Business analysis":
            try: int(row["reference"])
            except ValueError: raise ValueError("Expected an integer reference.") from None


def grade(row,answer):
    ref=row["reference"]
    answer=answer.strip()
    if row["task"]=="Extraction":
        expected=json.loads(ref)
        try: obj=json.loads(answer)
        except ValueError: obj=None
        obj=obj if isinstance(obj,dict) else {}
        checks={"Exact schema":set(obj)==set(expected)}
        for key,value in expected.items():
            checks["Supported field: "+key]=type(obj.get(key)) is type(value) and obj.get(key)==value
    elif row["task"]=="Business analysis":
        try: correct=int(answer)==int(ref)
        except ValueError: correct=False
        checks={"Correct change":correct,"Signed integer only":answer[:1] in ("+","-") and answer[1:].isdecimal()}
    elif row["task"]=="Instructions":
        checks={"Exact routing code":answer==ref,"Uppercase only":answer==answer.upper(),"Single token":len(answer.split())==1}
    else:
        checks={"Supported answer" if row["task"]=="Factual QA" else "Recognizes missing evidence":answer.casefold()==ref.strip().casefold()}
    return round(100*sum(checks.values())/len(checks),2), checks


def connect(path):
    db=sqlite3.connect(path,timeout=15)
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS datasets(version TEXT PRIMARY KEY,name TEXT NOT NULL,body TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY,version TEXT,grader TEXT,recipe TEXT,cutoff INT,stamp TEXT,body TEXT);
    CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,run INT,item TEXT,score INT,tag TEXT,reason TEXT,stamp TEXT);
    """)
    return db


def dataset(db,name,cases):
    validate(cases)
    body=json.dumps(cases,sort_keys=True)
    version=hashlib.sha256(body.encode()).hexdigest()[:16]
    with db: db.execute("INSERT OR IGNORE INTO datasets VALUES(?,?,?)",(version,name.strip()[:100] or "Custom",body))
    return version


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(db,version,recipe,cutoff):
    if recipe not in RECIPES or not 0<=cutoff<=100: raise ValueError("Invalid experiment settings.")
    cases=json.loads(db.execute("SELECT body FROM datasets WHERE version=?",(version,)).fetchone()[0])
    results=[]
    for row in cases:
        answer=row["A" if recipe==RECIPES[0] else "B"]
        score,checks=grade(row,answer)
        results.append(dict(id=row["id"],task=row["task"],score=score,passed=score>=cutoff,checks=checks,answer=answer))
    with db:
        cur=db.execute("INSERT INTO runs(version,grader,recipe,cutoff,stamp,body) VALUES(?,?,?,?,?,?)",
                       (version,VERSION,recipe,cutoff,now(),json.dumps(results)))
    logging.info("experiment_saved id=%s cases=%d",cur.lastrowid,len(results))
    return cur.lastrowid


def review(db,run_id,item,score,tag,reason):
    if not reason.strip() or not 0<=score<=100: raise ValueError("Supply a reason and a score between 0 and 100.")
    snapshot=db.execute("SELECT body FROM runs WHERE id=?",(run_id,)).fetchone()
    if not snapshot or not any(x["id"]==item for x in json.loads(snapshot[0])): raise ValueError("Unknown case in run.")
    with db: db.execute("INSERT INTO reviews(run,item,score,tag,reason,stamp) VALUES(?,?,?,?,?,?)",
                        (run_id,item,score,tag,reason.strip()[:3000],now()))


if __name__=="__main__": print(json.dumps(benchmark(),indent=2))
