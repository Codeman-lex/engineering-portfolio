from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .design import distribution, exposure, statistics
from .analytics import summary
from .detection import LEVELS, contributions
from .storage import STATES, case, save

COLORS = ["#287b74","#cfaa48","#d7773b","#af4149"]
TEAL = "#167d74"


def chart(fig, height=290):
    fig.update_layout(height=height,margin=dict(l=8,r=14,t=10,b=12),paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#466071",size=12),
                      legend=dict(orientation="h",y=-.18),hoverlabel=dict(font_size=13))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e6ecee")
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False,"scrollZoom":False})


def history(d):
    if d.empty:
        st.info("No earlier activity for this customer.")
        return
    fig=px.scatter(d,x="timestamp",y="amount",color="risk_category",color_discrete_map=dict(zip(LEVELS,COLORS)),
                   hover_data=["transaction_id","device"],labels={"timestamp":"Date (UTC)","amount":"Amount (USD)","risk_category":"Risk"})
    chart(fig)
    st.dataframe(d[["timestamp","transaction_id","amount","device","destination","recent_count","risk_category"]],hide_index=True)


def evidence(row, weights):
    parts=contributions(row,weights).iloc[0]
    active=parts[parts>0].sort_values(ascending=False)
    if active.empty:
        st.caption("No weighted signals triggered.")
    else:
        lines = [
            f'<div class="signal"><span>{escape(name)}</span><meter min="0" max="100" value="{points}"></meter><b>+{points}</b></div>'
            for name, points in active.items()
        ]
        st.html('<div class="signals">' + ''.join(lines) + '</div>')


def overview(d):
    m=summary(d)
    exposure(d, m)
    statistics(m)
    st.subheader("Priority review queue")
    queue = d.loc[d.risk_category != "Low Risk"].nlargest(10, ["risk_score", "amount"])
    if queue.empty:
        st.caption("No transactions crossed the review threshold in this selection.")
    else:
        st.caption("Highest rule scores first. Select a transaction to inspect its evidence.")
        table(queue, "queue")

    with st.container(key="overviewDetails"):
        left, right = st.columns([1.35, 1])
        with left:
            st.subheader("Transaction activity")
            unit = st.segmented_control("Daily measure", ["Volume", "Count"], default="Volume")
            daily = d.set_index("timestamp").amount.resample("D")
            series = daily.count() if unit == "Count" else daily.sum()
            fig = go.Figure(go.Scatter(x=series.index, y=series, mode="lines",
                            line=dict(color="#4b608d", width=2), fill="tozeroy",
                            fillcolor="rgba(113,136,185,.12)"))
            fig.update_yaxes(tickprefix="" if unit == "Count" else "$")
            chart(fig, 220)
        with right:
            st.subheader("Risk distribution")
            distribution(d)
    with st.expander("Geographic exposure"):
        geo=d.assign(flagged=d.risk_category!="Low Risk").groupby("origin").flagged.sum().reset_index()
        chart(px.bar(geo.sort_values("flagged"),x="flagged",y="origin",orientation="h",color_discrete_sequence=[TEAL],
                     labels={"origin":"Origin country","flagged":"Flagged transactions"}))


def table(d,key):
    cols=["transaction_id","risk_category","risk_score","amount","transaction_type","origin","customer_id","timestamp"]
    event=st.dataframe(d[cols],hide_index=True,use_container_width=True,on_select="rerun",selection_mode="single-row",key=key,
                       height="auto" if key != "queue" else min(254, 37+35*len(d)),
                       column_config={"transaction_id":"Transaction","risk_category":"Priority","customer_id":"Customer",
                                      "transaction_type":"Type","origin":"Origin","timestamp":"Time (UTC)","risk_score":st.column_config.ProgressColumn("Rule score",min_value=0,max_value=100,format="%d"),
                                      "amount":st.column_config.NumberColumn("USD",format="$%.2f")})
    if event.selection.rows:
        st.session_state["open_tx"]=d.iloc[event.selection.rows[0]].transaction_id
        st.session_state["goto"]="Investigations"
        st.rerun()


def investigate(engine,d,all_rows,weights):
    chosen=st.session_state.get("open_tx")
    ordered=d.sort_values(["risk_score","timestamp"],ascending=False)
    ids=ordered.transaction_id.tolist()
    # Keep the widget small while supporting any exact ID in the filtered scope.
    tx=st.text_input("Transaction ID",value=chosen if chosen in set(ids) else ids[0],key=f"lookup-{chosen}")
    row=d[d.transaction_id==tx.strip().upper()]
    if row.empty:
        st.info("Enter a transaction ID in the current filter selection.")
        return
    r=row.iloc[0]
    a,b,c=st.columns(3)
    a.metric("Rule score",f"{r.risk_score} / 100",border=True)
    b.metric("Anomaly percentile",f"{r.anomaly:.1f}",border=True)
    c.metric("Supervised probability",f"{r.probability:.1%}",border=True)
    st.write(f"**{r.risk_category}** · {r.transaction_type} · USD {r.amount:,.2f} · {r.timestamp} UTC")
    left,right=st.columns(2)
    with left:
        st.subheader("Detection evidence")
        evidence(row,weights)
        st.write(f"Spend was {r.amount/r.historical_average:.2f}× the prior average of USD {r.historical_average:,.2f}.")
        with st.expander("All transaction fields"):
            st.dataframe(row.T.astype(str).rename(columns={r.name:"Value"}))
    with right:
        st.subheader("Investigation record")
        record=case(engine,r.transaction_id)
        key=f"case-{r.transaction_id}"
        if key not in st.session_state:
            st.session_state[key]=record
        draft=st.session_state[key]
        with st.form(key+"-form-"+str(draft["revision"])):
            status=st.selectbox("Status",STATES,index=STATES.index(draft["status"]))
            notes=st.text_area("Analyst notes",draft["notes"],max_chars=4000)
            submitted=st.form_submit_button("Save investigation")
        if submitted:
            try:
                save(engine,r.transaction_id,status,notes,draft["revision"])
                st.session_state[key]=case(engine,r.transaction_id)
                st.toast("Investigation saved")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if record["revision"]!=draft["revision"] and st.button("Reload latest case"):
            st.session_state[key]=record
            st.rerun()
        report=row.assign(case_status=record["status"],analyst_notes=record["notes"])
        st.download_button("Download case CSV",report.to_csv(index=False),f"{r.transaction_id}.csv")
    st.subheader(f"Prior customer activity · {r.customer_id}")
    history(all_rows[(all_rows.customer_id==r.customer_id)&(all_rows.timestamp<r.timestamp)].tail(100))
