from html import escape
import json
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
from workflow import ALLOWED,POLICY,REVIEWERS,assess,change,connect,example,parse,risk,seed,submit

st.set_page_config(page_title="Aegis · Compliance operations",layout="wide")
st.html("<style>"+Path(__file__).with_name("aegis.css").read_text()+"</style>")
st.sidebar.html('<div class="a-brand"><i></i>Aegis<small>Onboarding registry</small></div>')
page=st.sidebar.radio("Compliance operations",["Case desk","Intake simulator","Audit history"])
actor=st.sidebar.selectbox("Synthetic reviewer",REVIEWERS)
st.sidebar.caption("Fictional onboarding records. Demo identities are selectable.")
db=connect(Path(__file__).with_name("aegis.sqlite")); seed(db)
ledger=pd.read_sql_query("SELECT * FROM cases ORDER BY id DESC",db)
events=pd.read_sql_query("SELECT * FROM audit ORDER BY id DESC",db)
if page=="Intake simulator":
    st.title("Intake simulator")
    st.write("Create a fictional applicant, inspect extracted fields and test the review route.")
    kind=st.radio("Applicant type",["Business","Individual"],horizontal=True)
    rec=example(2 if kind=="Business" else 1)
    declared=rec["declared"]
    a,b=st.columns(2)
    for i,key in enumerate(declared): declared[key]=[a,b][i%2].text_input("Declared "+key,declared[key],key=kind+key,max_chars=300)
    st.download_button("Download sample documents",json.dumps(rec["documents"],indent=2),"synthetic-packet.json")
    file=st.file_uploader("Upload synthetic document packet",type=["json"])
    raw=st.text_area("Or edit document JSON",json.dumps(rec["documents"],indent=2),height=170,key=kind+"packet")
    with st.expander("Validation policy"):
        policy={k:st.checkbox("Check "+k,True) for k in POLICY}
    try:
        rec["documents"]=parse(file.getvalue() if file else raw.encode(),file.name if file else "packet.json")
        checks=assess(rec,policy,date.today().isoformat())
        st.subheader("Intake → Extraction → Validation → Human review")
        st.write(f"{len(rec['documents'])} document types extracted · {risk(checks)} · {sum(not c['passed'] for c in checks)} failed checks")
        st.dataframe(checks,hide_index=True)
        if st.button("Submit to case desk"):
            import uuid
            rec["customer_id"]="DEMO-"+uuid.uuid4().hex[:12]
            cid=submit(db,rec,policy,actor); st.success(f"Recorded case {cid}. Open Case desk to review.")
    except ValueError as exc: st.error(str(exc))
elif page=="Audit history":
    st.title("Decision history")
    cid=st.selectbox("Case",ledger.id)
    trail=events[events.case_id==cid]
    for entry in trail.itertuples():
        st.html(f'<div class="a-step"><small>{escape(entry.stamp)} · {escape(entry.reviewer)}</small><b>{escape(entry.action)} → {escape(entry.status)}</b>{escape(entry.reason)}</div>')
    event=st.selectbox("Inspect recorded evidence",trail.id)
    st.json(json.loads(trail.loc[trail.id==event,"snapshot"].iloc[0]))
    st.download_button("Export case history",trail.to_json(orient="records",indent=2),"audit.json")
else:
    st.title("Case registry")

    a,b=st.columns(2)
    statuses=a.multiselect("Status",sorted(ledger.status.unique()))
    query=b.text_input("Search case, customer or applicant")
    view=ledger[ledger.status.isin(statuses)] if statuses else ledger
    view=view[view.apply(lambda r:query.lower() in (str(r.id)+" "+r.record).lower(),axis=1)]
    if view.empty: st.info("No matching cases."); st.stop()
    scoped=events[events.case_id.isin(view.id)]
    done=scoped[scoped.action.isin(["Approve","Reject"])].drop_duplicates("case_id")
    elapsed=(pd.to_datetime(done.stamp,utc=True)-pd.to_datetime(done.case_id.map(view.set_index("id").submitted),utc=True)).dt.total_seconds()/3600
    for col,label,value in zip(st.columns(4),["Cases","Require review","Awaiting information","Mean time to decision"],[len(view),(view.status=="Requires review").sum(),(view.status=="Awaiting information").sum(),f"{elapsed.mean():.1f} h" if len(done) else "—"]): col.metric(label,value)
    with st.expander("Workload and documentation issues"):
        st.bar_chart(view.status.value_counts())
        st.write("Failed checks"); st.dataframe(pd.Series([x["rule"] for c in view.checks for x in json.loads(c) if not x["passed"]],dtype=str).value_counts())
        active=view[~view.status.isin(["Approved","Rejected"])]
        if len(active): st.write("Mean open case age (days)",round((pd.Timestamp.now(tz="UTC")-pd.to_datetime(active.submitted,utc=True)).dt.total_seconds().mean()/86400,1))
        st.caption(f"{(scoped.action=='Escalate').sum()} escalations · {(scoped.action=='Replace documents').sum()} document replacements · Includes synthetic seeded timings.")
    priority=next((i for i,status in enumerate(view.status) if status=="Requires review"),0)
    cid=st.selectbox("Review case",view.id,index=priority,format_func=lambda i:f"Case {i} · {view.loc[view.id==i,'status'].iloc[0]}")
    r=view[view.id==cid].iloc[0]; rec=json.loads(r.record); checks=json.loads(r.checks)
    st.html(f'<section class="a-cover"><small>Case file / {cid:04d}</small><strong>{escape(r.status)}</strong><h2>{escape(rec["declared"]["name"])}</h2><footer>{escape(rec["kind"])} · {escape(rec["customer_id"])} · {escape(r.reviewer)}</footer></section>')
    flagged=[c for c in checks if not c["passed"]]
    st.caption(f'{len(rec["documents"])} document types · {len(flagged)} exceptions · {risk(checks)}')
    for check in flagged:
        st.html(f'<article class="a-slip"><b>{escape({"Address address":"Address mismatch","Identity validity":"Identity expiry"}.get(check["rule"],check["rule"]))}</b><dl><dt>Expected</dt><dd>{escape(check["expected"])}</dd><dt>Observed</dt><dd>{escape(check["observed"])}</dd></dl>{escape(check["next_action"])}</article>')
    with st.expander("All validation checks"): st.dataframe(checks,hide_index=True)
    with st.expander("Declared and extracted fields"): st.json(rec)
    with st.form(f"decision-{cid}-{r.revision}"):
        options=ALLOWED[r.status]+["Add note"]
        if r.status not in ("Approved","Rejected"): options+=["Replace documents"]
        action=st.selectbox("Review action",options)
        raw=st.text_area("Replacement packet (used for Replace documents)",json.dumps(rec["documents"],indent=2))
        reason=st.text_input("Decision reason or note",max_chars=3000)
        if st.form_submit_button("Record action"):
            try:
                docs=parse(raw.encode(),"packet.json") if action=="Replace documents" else None
                change(db,int(cid),int(r.revision),action,actor,reason,docs); st.rerun()
            except ValueError as exc: st.error(str(exc))
    st.dataframe(scoped[scoped.case_id==cid].drop(columns="snapshot"),hide_index=True)
    st.download_button("Export filtered cases",view.to_csv(index=False),"onboarding.csv")
