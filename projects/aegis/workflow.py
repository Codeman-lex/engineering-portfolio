"""Synthetic onboarding documents, validation and atomic case transitions."""
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

REVIEWERS=["Demo analyst Rowan","Demo reviewer Quinn"]
ACTIONS={"Request information":"Awaiting information","Escalate":"Escalated","Approve":"Approved","Reject":"Rejected","Reopen":"Pending"}
ALLOWED={"Pending":["Request information","Escalate","Approve","Reject"],"Requires review":["Request information","Escalate","Approve","Reject"],
         "Awaiting information":["Reopen","Escalate"],"Escalated":["Approve","Reject","Request information"],"Approved":["Reopen"],"Rejected":["Reopen"]}
KINDS=["identity","address","registration","ownership"]
POLICY={"expiry":True,"address":True,"registration":True,"ownership":True}


def example(i):
    business=i%2==0
    name=f"Fenn Works {i:03}" if business else f"Tern Applicant {i:03}"
    declared=dict(name=name,address=f"Unit {i}, Demo Quay",registration=f"REG-{i:05}",activity="Equipment leasing" if business else "Personal account",country="Example jurisdiction")
    docs={"identity":{"name":name,"expires":"2030-01-01"},"address":{"address":declared["address"]}}
    if business:
        docs.update(registration={"name":name,"registration":declared["registration"]},ownership={"owner":f"Demo member {i}"})
    if i%4==0: docs["address"]["address"]="Unit 0, Demo Quay"
    if i%5==0: docs["identity"]["expires"]="2025-01-01"
    if i%7==0: del docs["address"]
    return dict(customer_id=f"DEMO-{i:04}",kind="Business" if business else "Individual",declared=declared,documents=docs)


def parse(raw,filename):
    if not filename.lower().endswith(".json") or len(raw)>65536:
        raise ValueError("Upload a JSON document packet of at most 64 KiB.")
    try: packet=json.loads(raw)
    except (ValueError,UnicodeError,RecursionError): raise ValueError("Unreadable JSON packet.") from None
    if not isinstance(packet,dict) or set(packet)-set(KINDS): raise ValueError("Unknown document type.")
    for fields in packet.values():
        if not isinstance(fields,dict) or len(fields)>12 or any(not isinstance(v,str) or len(v)>300 for v in fields.values()):
            raise ValueError("Document fields must be short strings.")
    return packet


def assess(record,policy,day):
    docs=record["documents"]
    declared=record["declared"]
    checks=[]
    def check(name,expected,seen,group,action):
        checks.append(dict(rule=name,expected=expected,observed=seen or "(missing)",passed=bool(seen) and expected==seen,
                           category=group,reason=f"Check {name.lower()} against the declared record.",next_action=action))
    for key in ["name","address","activity","country"] + (["registration"] if record["kind"]=="Business" else []):
        check("Declared "+key,"provided","provided" if declared.get(key,"").strip() else "","Completeness","Request applicant details")
    required=["identity","address"]+(["registration","ownership"] if record["kind"]=="Business" else [])
    for k in required:
        check(k.title()+" document","present","present" if k in docs else "","Completeness","Request document")
    def match(doc,key,value):
        seen=docs.get(doc,{}).get(key,"").strip()
        check(doc.title()+" "+key,value,seen,"Consistency" if seen else "Completeness","Confirm with applicant")
    match("identity","name",declared["name"])
    if policy["address"]: match("address","address",declared["address"])
    if "identity" in docs and policy["expiry"]:
        value=docs["identity"].get("expires","")
        try: valid=date.fromisoformat(value)>=date.fromisoformat(day)
        except ValueError: valid=False
        check("Identity validity","current","current" if valid else ("invalid date or expired: "+value if value else ""),"Validity" if value else "Completeness","Request dated replacement")
    if record["kind"]=="Business":
        if policy["registration"]:
            match("registration","registration",declared["registration"]); match("registration","name",declared["name"])
        if policy["ownership"]:
            owner=docs.get("ownership",{}).get("owner","").strip()
            check("Named owner","provided","provided" if owner else "","Completeness","Request ownership declaration")
    return checks


def risk(checks):
    failures=[x for x in checks if not x["passed"]]
    count=sum(x["category"]!="Completeness" for x in failures)
    if count: return "High" if count>1 else "Medium"
    return "Requires Manual Review" if failures else "Low"


def connect(path):
    db=sqlite3.connect(path,timeout=15)
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS cases(id INTEGER PRIMARY KEY,record TEXT,policy TEXT,checks TEXT,status TEXT,reviewer TEXT,submitted TEXT,revision INTEGER);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,case_id INT,stamp TEXT,action TEXT,previous TEXT,status TEXT,reviewer TEXT,reason TEXT,snapshot TEXT);
    """)
    return db


def write(db,caseid,record,policy,checks,old,status,actor,reason,action,stamp,revision):
    snapshot=json.dumps(dict(record=record,policy=policy,checks=checks))
    if caseid is None:
        cur=db.execute("INSERT INTO cases(record,policy,checks,status,reviewer,submitted,revision) VALUES(?,?,?,?,?,?,1)",
            (json.dumps(record),json.dumps(policy),json.dumps(checks),status,actor,stamp))
        caseid=cur.lastrowid
    else:
        changed=db.execute("UPDATE cases SET record=?,policy=?,checks=?,status=?,reviewer=?,revision=revision+1 WHERE id=? AND revision=?",
                           (json.dumps(record),json.dumps(policy),json.dumps(checks),status,actor,caseid,revision))
        if changed.rowcount!=1: raise ValueError("Case changed. Reload the current revision.")
    db.execute("INSERT INTO audit(case_id,stamp,action,previous,status,reviewer,reason,snapshot) VALUES(?,?,?,?,?,?,?,?)",
               (caseid,stamp,action,old,status,actor,reason,snapshot))
    return caseid


def timestamp(): return datetime.now(timezone.utc).isoformat(timespec="seconds")


def submit(db,record,policy,actor,stamp=None):
    stamp=stamp or timestamp()
    if actor not in REVIEWERS or not record["declared"]["name"].strip(): raise ValueError("Supply a name and demo reviewer.")
    record=dict(record,documents=parse(json.dumps(record["documents"]).encode(),"packet.json"))
    checks=assess(record,policy,stamp[:10])
    status="Requires review" if any(not x["passed"] for x in checks) else "Pending"
    with db: return write(db,None,record,policy,checks,"",status,actor,"Synthetic intake validated","Intake",stamp,0)


def change(db,caseid,revision,action,actor,reason,docs=None,stamp=None):
    stamp=stamp or timestamp()
    if actor not in REVIEWERS or not reason.strip(): raise ValueError("A demo reviewer and decision reason are required.")
    with db:
        row=db.execute("SELECT * FROM cases WHERE id=?",(caseid,)).fetchone()
        if not row: raise ValueError("Unknown case.")
        old=row["status"]
        record=json.loads(row["record"]); policy=json.loads(row["policy"]); checks=json.loads(row["checks"])
        if action=="Replace documents" and old not in ["Approved","Rejected"]:
            record["documents"]=parse(json.dumps(docs).encode(),"packet.json")
            checks=assess(record,policy,stamp[:10])
            status="Pending" if all(x["passed"] for x in checks) else "Requires review"
        elif action=="Add note": status=old
        elif action in ALLOWED[old]: status=ACTIONS[action]
        else: raise ValueError("This transition is unavailable from the current status.")
        return write(db,caseid,record,policy,checks,old,status,actor,reason.strip()[:3000],action,stamp,revision)


def seed(db):
    with db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM cases LIMIT 1").fetchone():
            return
        for i in range(1,41):
            start=datetime(2026,5,1,tzinfo=timezone.utc)+timedelta(days=i)
            record=example(i)
            checks=assess(record,POLICY,start.date().isoformat())
            status="Pending" if all(c["passed"] for c in checks) else "Requires review"
            cid=write(db,None,record,POLICY,checks,"",status,REVIEWERS[0],"Synthetic intake validated","Intake",start.isoformat(),0)
            action=["Escalate","Approve","Request information","Reject",None,None][i%6]
            if action:
                stamp=(start+timedelta(hours=i%13+1)).isoformat()
                write(db,cid,record,POLICY,checks,status,ACTIONS[action],REVIEWERS[1],"Seeded workflow example",action,stamp,1)
