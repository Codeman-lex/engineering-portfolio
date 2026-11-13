import logging
import math
import os
from pathlib import Path

import streamlit as st

from sentinel.design import LOGO_URL, apply_theme, brand
from sentinel.analytics import filter_rows
from sentinel.detection import LEVELS, RULES, WEIGHTS, classify, contributions, train
from sentinel.storage import database, initialize, load
from sentinel.ui import history, investigate, overview, table
from sentinel.workbench import performance, simulator

st.set_page_config(page_title="Sentinel AI · Risk intelligence", page_icon=LOGO_URL, layout="wide")
logging.basicConfig(level=logging.INFO)
apply_theme()


@st.cache_resource(show_spinner="Preparing synthetic transactions and training detection models…")
def bootstrap(path,count):
    engine=database(Path(path))
    initialize(engine,count)
    frame=load(engine)
    models=train(frame)
    frame["anomaly"],frame["probability"]=models.predict(frame)
    return engine,frame,models


try:
    engine,raw,models=bootstrap(os.getenv("SENTINEL_DB","data/sentinel.sqlite"),int(os.getenv("SENTINEL_ROWS","100000")))
except Exception:
    logging.exception("Workspace initialization failed")
    st.error("Could not initialize the dataset. Check the database path, row count and server log.")
    st.stop()

pages=["Overview","Transaction explorer","Investigations","Customer profiles","Risk simulator","Model performance","Methodology"]
descriptions=["Monitor transaction activity, review exposure, and investigate high-priority signals.",
              "Search the ledger and select a transaction to open its investigation.",
              "Review transaction evidence, record findings, and track case status.",
              "Explore customer spending, device usage, and geographic activity.",
              "Assess hypothetical transactions against the same rules and models used in monitoring.",
              "Compare detectors on the held-out portion of the synthetic event stream.",
              "Understand how the dataset, rules, and model evaluations are constructed."]
if "goto" in st.session_state:
    st.session_state["navigation"]=st.session_state.pop("goto")
with st.sidebar:
    brand()
    page = st.radio("Analyst workspace", pages, key="navigation", label_visibility="collapsed")
    st.html(f'<div class="env"><b><i></i>Synthetic workspace</b><small>{len(raw):,} transactions · USD</small></div>')

st.html(f'<div class="dateline">Financial intelligence &nbsp; / &nbsp; {page}</div>')
st.title("Risk overview" if page=="Overview" else page)
if page != "Overview":
    st.write(descriptions[pages.index(page)])
toolbar = st.container(horizontal=True, gap="small")
with toolbar.popover("Scoring rules", icon=":material/tune:"):
    st.caption("Session settings apply to rules across the workspace. Scores are capped at 100.")
    ws=st.columns(4)
    weights=tuple(ws[i%4].number_input(name,0,100,int(w)) for i,(name,w) in enumerate(zip(RULES,WEIGHTS)))
    cs=st.columns(3)
    thresholds=tuple(c.number_input(name,1,100,v) for c,name,v in zip(cs,LEVELS[1:],(25,50,75)))
if not thresholds[0]<thresholds[1]<thresholds[2]:
    st.error("Set strictly increasing risk thresholds.")
    st.stop()
d=raw
if weights!=WEIGHTS or thresholds!=(25,50,75):
    score=contributions(raw,weights).sum(axis=1).clip(upper=100)
    d=raw.assign(risk_score=score,risk_category=classify(score,thresholds))

if page not in ["Risk simulator","Methodology"]:
    with toolbar.popover("Filter ledger", icon=":material/filter_list:"):
        a,b,c=st.columns(3)
        dates=a.date_input("Dates (UTC)",(d.timestamp.min().date(),d.timestamp.max().date()))
        lo=b.number_input("Minimum USD",min_value=0.,value=0.)
        hi=c.number_input("Maximum USD",min_value=0.,value=float(d.amount.max()))
        sel={}
        for i,(col,label) in enumerate([("transaction_type","Transaction type"),("risk_category","Risk category"),
            ("origin","Origin country"),("merchant_category","Merchant category"),("customer_id","Customer"),("fraud_label","Synthetic label")]):
            sel[col]=[a,b,c][i%3].multiselect(label,sorted(d[col].unique()),key="filter-"+col)
    view=filter_rows(d,dates,(lo,hi),sel)
    if view.empty or len(dates)!=2:
        st.info("No complete date range or matching transactions. Adjust the filters to continue.")
        st.stop()

if page=="Overview":
    overview(view)
elif page=="Transaction explorer":
    search=st.text_input("Search transaction or customer ID",placeholder="TX-0000001 or CU-00001")
    found=filter_rows(view,search=search)
    a,b,c=st.columns(3)
    order=a.selectbox("Sort by",["timestamp","risk_score","amount","transaction_id"])
    asc=b.toggle("Ascending order")
    ordered=found.sort_values([order] if order=="transaction_id" else [order,"transaction_id"],ascending=asc)
    n=int(c.number_input("Page",1,max(1,math.ceil(len(found)/50)),1))
    st.caption(f"{len(found):,} matching transactions · 50 per page")
    table(ordered.iloc[(n-1)*50:n*50],f"ledger-{n}-{order}-{asc}-{search}")
    if st.button("Prepare filtered CSV"):
        st.download_button("Download filtered ledger",ordered.to_csv(index=False),"sentinel-ledger.csv")
elif page=="Investigations":
    investigate(engine,view,d,weights)
elif page=="Customer profiles":
    customer=st.selectbox("Customer ID",sorted(view.customer_id.unique()))
    h=view[view.customer_id==customer]
    a,b,c,e=st.columns(4)
    a.metric("Typical spend (median)",f"${h.amount.median():,.2f}",border=True)
    b.metric("Devices observed",h.device.nunique(),border=True)
    c.metric("Destination countries",h.destination.nunique(),border=True)
    e.metric("Flagged transactions",(h.risk_category!="Low Risk").sum(),border=True)
    history(h)
elif page=="Risk simulator":
    simulator(models,weights,thresholds)
elif page=="Model performance":
    performance(view,models)
else:
    st.markdown(Path("docs/methodology.md").read_text())
