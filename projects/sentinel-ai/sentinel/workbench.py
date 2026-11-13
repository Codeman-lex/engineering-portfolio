import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.metrics import precision_recall_curve

from .data import COUNTRIES
from .detection import classify, contributions, metrics
from .ui import TEAL, chart, evidence


def simulator(models,weights,thresholds):
    preset=st.segmented_control("Simulation scenario", ["Everyday purchase","Rapid transfer","Travel purchase"], default="Everyday purchase") or "Everyday purchase"
    rapid=preset=="Rapid transfer"
    with st.form("simulation-"+preset):
        a,b,c=st.columns(3)
        a.subheader("Transaction")
        b.subheader("Customer history")
        c.subheader("Account & access")
        amount=a.number_input("Amount (USD)",.01,1e8,850. if rapid else 75.,key=preset+"amt")
        mean=b.number_input("Historical average (USD)",.01,1e8,80.)
        age=c.number_input("Account age (days)",0,40000,365)
        home=b.selectbox("Origin country",COUNTRIES)
        dest=a.selectbox("Destination country",COUNTRIES,index=int(rapid or preset=="Travel purchase"),key=preset+"dest")
        ip=c.selectbox("IP country",COUNTRIES,index=int(preset=="Travel purchase"),key=preset+"ip")
        count=b.number_input("Prior transactions in one hour",0,10000,4 if rapid else 0,key=preset+"freq")
        device=c.checkbox("Previously unseen device",value=rapid,key=preset+"dev")
        ben=a.checkbox("New beneficiary",value=rapid,key=preset+"ben")
        submit=st.form_submit_button("Assess simulation",type="primary")
    if submit:
        st.session_state["simulation"]=(preset,dict(amount=amount,historical_average=mean,account_age=age,
            origin=home,destination=dest,ip_country=ip,recent_count=count,new_device=device,
            international=int(home!=dest),new_beneficiary=ben))
    saved=st.session_state.get("simulation")
    if saved and saved[0]==preset:
        row=pd.DataFrame([saved[1]])
        score=min(100,contributions(row,weights).sum(axis=1).item())
        anomaly,prob=models.predict(row)
        st.subheader("Simulated assessment")
        a,b,c=st.columns(3)
        a.metric(classify([score],thresholds)[0],f"{score} / 100",border=True)
        b.metric("Anomaly percentile",f"{anomaly[0]:.1f}",border=True)
        c.metric("Supervised probability",f"{prob[0]:.1%}",border=True)
        st.write(f"Transaction amount is {row.amount[0]/row.historical_average[0]:.2f}× the supplied historical average.")
        evidence(row,weights)


def performance(d,models):
    held=d[d.timestamp>=models.cutoff]
    st.caption(f"Chronological holdout from {models.cutoff} UTC · {len(held):,} filtered transactions")
    if held.empty:
        st.info("Select dates containing held-out transactions.")
        return
    a,b,c=st.columns(3)
    rt=a.slider("Rule score cutoff",0,100,25)
    at=b.slider("Anomaly percentile cutoff",0.,100.,98.)
    pt=c.slider("Supervised probability cutoff",0.,1.,.5)
    methods={"Rules":(held.risk_score,rt),"Isolation Forest":(held.anomaly,at),
             "Logistic regression":(held.probability,pt),"Amount baseline":(held.amount,models.baseline_amount)}
    results=pd.DataFrame({k:metrics(held.fraud_label,score>=t) for k,(score,t) in methods.items()}).T
    st.dataframe(results.style.format({k:"{:.1%}" for k in ["Precision","Recall","F1","FPR"]}).format(
        {k:"{:.0f}" for k in ["TN","FP","FN","TP"]}),use_container_width=True)
    name=st.selectbox("Inspect method",methods.keys())
    score,t=methods[name]
    result=results.loc[name]
    a,b=st.columns(2)
    with a:
        st.subheader("Confusion matrix")
        matrix=[[result.TN,result.FP],[result.FN,result.TP]]
        chart(px.imshow(matrix,text_auto=".0f",x=["Clear","Flagged"],y=["Label 0","Label 1"],
                        color_continuous_scale="Teal",labels=dict(x="Decision",y="Synthetic truth")))
    with b:
        st.subheader("Precision–recall curve")
        if held.fraud_label.nunique()==2:
            p,r,_=precision_recall_curve(held.fraud_label,score)
            ix=np.linspace(0,len(p)-1,min(len(p),600),dtype=int)
            chart(px.line(x=r[ix],y=p[ix],labels={"x":"Recall","y":"Precision"},color_discrete_sequence=[TEAL]))
        else:
            st.info("Both synthetic label classes are needed for this curve.")
    fp=held[(score>=t)&(held.fraud_label==0)]
    st.subheader("False-positive review")
    st.caption(f"{len(fp):,} synthetic label-0 transactions crossed the selected threshold.")
    st.dataframe(fp.nlargest(50,"amount")[["transaction_id","timestamp","amount","risk_score","anomaly","probability"]],hide_index=True)
