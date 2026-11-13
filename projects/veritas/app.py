from html import escape
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from lab import RECIPES,TASKS,benchmark,connect,dataset,grade,review,run

st.set_page_config(page_title="Veritas · Evaluation lab",layout="wide")
st.html("<style>"+Path(__file__).with_name("veritas.css").read_text()+"</style>")
st.html('<div class="v-mast"><span class="v-word">Veritas<b>.</b></span><small>Response evaluation laboratory</small></div>')
pages=["Response workbench","Experiment register","Datasets"]
page=st.segmented_control("Laboratory sections",pages,default=pages[0],label_visibility="collapsed") or pages[0]
db=connect(Path(__file__).with_name("veritas.sqlite"))
if not db.execute("SELECT 1 FROM datasets LIMIT 1").fetchone():
    dataset(db,"Synthetic benchmark",benchmark())
sets={r["version"]:r["name"] for r in db.execute("SELECT * FROM datasets")}
with st.popover("Benchmark settings"):
    st.caption("Saved synthetic response fixtures · deterministic grader 1.0")
    version=st.selectbox("Dataset version",sets,format_func=lambda v:sets[v]+" · "+v[:6])
cases=json.loads(db.execute("SELECT body FROM datasets WHERE version=?",(version,)).fetchone()[0])

if page=="Datasets":
    st.title("Dataset library")
    st.write("Edit the JSON template to supply your own cases and both candidate responses.")
    st.download_button("Download dataset template",json.dumps(cases,indent=2),"cases.json")
    name=st.text_input("Dataset name")
    upload=st.file_uploader("Import JSON dataset",type="json")
    if st.button("Save dataset version") and upload:
        try:
            if upload.size>2_000_000: raise ValueError("Maximum file size is 2 MB.")
            key=dataset(db,name,json.loads(upload.getvalue()))
            st.success("Saved version "+key)
        except (ValueError,TypeError,RecursionError) as exc: st.error(str(exc))
    st.dataframe(pd.DataFrame(cases)[["id","task","prompt"]],hide_index=True)
elif page=="Response workbench":
    st.title("Response workbench")

    l,r=st.columns(2)
    task=l.selectbox("Task",TASKS,index=1)
    available=[c for c in cases if c["task"]==task]
    if not available: st.info("No cases in this category."); st.stop()
    first_difference=next((i for i,c in enumerate(available) if c["A"]!=c["B"]),0)
    row=r.selectbox("Test case",available,index=first_difference,format_func=lambda c:c["id"])
    st.html(f'<section class="v-source"><div><small>Source evidence · {escape(row["id"])}</small><h2>{escape(row["prompt"])}</h2>{escape(row["evidence"])}</div><div><small>Reference answer</small><p><code>{escape(row["reference"])}</code></p></div></section>')
    for col,key,recipe in zip(st.columns(2),"AB",RECIPES):
        with col.container(border=True):
            st.html(f'<div class="v-candidate"><b>{key}</b>{recipe}</div>')
            answer=st.text_area("Candidate "+key,row[key],key=row["id"]+key+version,height=80)
            score,checks=grade(row,answer)
            if row["task"]=="Extraction" and score<100:
                expected=json.loads(row["reference"])
                try: observed=json.loads(answer)
                except ValueError: observed=None
                if isinstance(observed,dict):
                    for field,value in expected.items():
                        if not checks["Supported field: "+field]:
                            old=escape(str(observed.get(field,"missing")))
                            st.html(f'<div class="v-edit"><small>{escape(field)} · evidence correction</small><del>{old}</del><span> → </span><ins>{escape(str(value))}</ins></div>')
            lines="".join(f'<div class="v-check {"" if ok else "fail"}"><b>{"✓" if ok else "✕"}</b>{escape(label)}</div>' for label,ok in checks.items())
            st.html(f'<div class="v-grade"><strong>{score:g}</strong><small>points / 100</small></div>'+lines)
    st.caption("Workbench edits are exploratory. Import a dataset to save changed answers as a new fixture set.")
else:
    st.title("Experiment register")
    recipe=st.selectbox("Prompt instruction fixture",RECIPES)
    threshold=st.slider("Passing threshold",0,100,100)
    scores=[grade(c,c["A" if recipe==RECIPES[0] else "B"])[0] for c in cases]
    st.metric("Preview pass rate",f"{sum(s>=threshold for s in scores)/len(scores):.1%}")
    if st.button("Record experiment"): run(db,version,recipe,threshold)
    runs={r["id"]:dict(r) for r in db.execute("SELECT * FROM runs WHERE version=? ORDER BY id DESC",(version,))}
    if not runs: st.info("Record a run to inspect errors and add a human review."); st.stop()
    chosen=st.selectbox("Recorded run",runs,format_func=lambda i:f"Run {i} · {runs[i]['recipe']} · cutoff {runs[i]['cutoff']}")
    current=runs[chosen]
    rows=json.loads(current["body"])
    df=pd.DataFrame(rows)
    st.caption(current["stamp"]+" · dataset "+version+" · grader "+current["grader"])
    st.bar_chart(df.groupby("task").passed.mean(),y_label="Pass rate")
    st.bar_chart(df.score.value_counts().sort_index(),y_label="Responses",x_label="Score")
    issues=pd.Series([k for x in rows for k,v in x["checks"].items() if not v],dtype=str).value_counts()
    st.write("Failed criteria"); st.dataframe(issues.rename("Failures"))
    peers=[i for i in runs if i!=chosen and runs[i]["grader"]==current["grader"] and runs[i]["cutoff"]==current["cutoff"]]
    if peers:
        other=st.selectbox("Compare at the same cutoff and dataset version",peers)
        before=pd.DataFrame(json.loads(runs[other]["body"])).set_index("id")
        st.metric("Pass-rate change",f"{100*(df.passed.mean()-before.passed.mean()):+.1f} percentage points")
        st.caption(f"Compared with run {other} · {runs[other]['recipe']}")
    a,b,c=st.columns(3)
    task=a.selectbox("Filter task",["All"]+TASKS)
    result=b.selectbox("Outcome",["All","Failed","Passed"])
    error=c.selectbox("Failed criterion",["All"]+list(issues.index))
    lo,hi=st.slider("Score range",0,100,(0,100))
    visible=[x for x in rows if (task=="All" or task==x["task"]) and (result=="All" or x["passed"]==(result=="Passed")) and (error=="All" or x["checks"].get(error) is False) and lo<=x["score"]<=hi]
    history=pd.read_sql_query("SELECT * FROM reviews WHERE run=? ORDER BY id DESC",db,params=(chosen,))
    st.download_button("Export experiment JSON",json.dumps(dict(run={k:v for k,v in current.items() if k!="body"},rows=rows,reviews=history.to_dict("records")),indent=2),"experiment.json")
    st.download_button("Export scores CSV",df.drop(columns="checks").to_csv(index=False),"scores.csv")
    if visible:
        x=st.selectbox("Inspect response",sorted(visible,key=lambda x:x["score"]),format_func=lambda x:f"{x['id']} · {x['score']} points")
        original=next(c for c in cases if c["id"]==x["id"])
        st.write(original["prompt"]); st.info(original["evidence"]); st.code(x["answer"]); st.json(x["checks"])
        with st.form(f"review-{chosen}-{x['id']}"):
            human=st.number_input("Human score",0,100,int(x["score"]))
            tag=st.selectbox("Review tag",["Confirmed","Ambiguous","Clarity","Unsupported claim","Other"])
            note=st.text_input("Explain your score against the reference, clarity or usefulness")
            if st.form_submit_button("Append review"):
                try: review(db,chosen,x["id"],human,tag,note); st.rerun()
                except ValueError as exc: st.error(str(exc))
    else: st.info("No matching responses.")
    if len(history):
        history["disagreement"]=history.score!=history["item"].map(df.set_index("id").score)
        st.subheader("Human review history"); st.dataframe(history,hide_index=True)
