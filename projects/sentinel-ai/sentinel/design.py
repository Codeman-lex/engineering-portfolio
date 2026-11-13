"""Brand assets and data-driven monitoring visuals."""
from base64 import b64encode
from pathlib import Path
from urllib.parse import quote

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS / "sentinel.svg"
LOGO_URL = "data:image/svg+xml;base64," + b64encode(LOGO.read_bytes()).decode()
ICONS = [
    '<rect x="3" y="3" width="7" height="7" rx="1"/><path d="M14 4h7v6h-7zM3 14h7v7H3zM14 14h7v7h-7z"/>',
    '<path d="M3 5h18M3 12h18M3 19h18m-14-16v4m9 3v4m-7 3v4"/>',
    '<path d="M3 7V5h7l2 2h9v12H3z"/><circle cx="12" cy="13" r="2.5"/>',
    '<circle cx="10" cy="8" r="3"/><path d="M3 20v-2a7 7 0 0 1 14 0v2m0-15a3 3 0 0 1 0 6m2 2a5 5 0 0 1 3 5"/>',
    '<path d="M9 3h6m-5 0v6L4 19q-1 2 2 2h12q3 0 2-2L14 9V3M7 15h10"/>',
    '<path d="M3 3v17h18M6 15l4-6 4 3 6-8"/>',
    '<path d="M3 4h7l2 2 2-2h7v15h-7l-2 2-2-2H3zM12 6v14"/>',
]


def apply_theme():
    css = (ASSETS / "workspace.css").read_text()
    for i, paths in enumerate(ICONS, start=1):
        icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
        css += f'[data-testid="stSidebar"] [role="radiogroup"] > div:nth-child({i}) label::before{{mask-image:url("data:image/svg+xml,{quote(icon)}")}}'
    st.html(f"<style>{css}</style>")


def brand():
    st.html(f'<div class="identity"><img src="{LOGO_URL}" alt=""><span>Sentinel<span class="brand-ai">AI</span></span></div>')


def money(value):
    if value >= 1_000_000:
        return f"${value/1_000_000:,.2f}M"
    if value >= 10_000:
        return f"${value/1_000:,.1f}K"
    return f"${value:,.2f}"


def exposure(d, totals):
    sums = d.assign(flagged_amount=d.amount.where(d.risk_category != "Low Risk", 0)).set_index("timestamp")
    daily = sums[["amount","flagged_amount"]].resample("D").sum()
    peak = daily.amount.max()
    bars = []
    for day, amount, flagged in daily.itertuples():
        tooltip = f"{day:%d %b} · Volume ${amount:,.0f} · Flagged ${flagged:,.0f}"
        bars.append(f'<i title="{tooltip}" style="height:{100*amount/peak:.2f}%"><b style="height:{100*flagged/amount if amount else 0:.2f}%"></b></i>')
    start, end = daily.index[[0,-1]]
    share = totals["exposure"]/totals["volume"]
    st.html(f"""<section class="exposure"><div class="ex-summary"><div class="ex-title">Flagged exposure</div>
    <div class="ex-money" title="USD {totals['exposure']:,.2f}">{money(totals['exposure'])}</div>
    <div class="ex-share">{share:.1%} of monitored volume</div></div>
    <div class="ex-chart"><div class="ex-legend"><span>Daily volume</span><span>Flagged value</span></div>
    <div class="bars" role="img" aria-label="Daily transaction volume and flagged value, {start:%d %B} to {end:%d %B}">{''.join(bars)}</div>
    <div class="ex-axis"><span>{start:%d %b %Y}</span><span>{end:%d %b %Y}</span></div></div></section>""")


def statistics(totals):
    items = [("Transactions",f"{totals['total']:,}"),("Monitored volume",money(totals["volume"])),
             ("Flagged transactions",f"{totals['flagged']:,}"),("Average rule score",f"{totals['average']:.1f} / 100")]
    st.html('<dl class="statistics">' + ''.join(f"<div><dt>{label}</dt><dd>{value}</dd></div>" for label,value in items) + '</dl>')


def distribution(d):
    levels = ["Critical Risk","High Risk","Medium Risk","Low Risk"]
    counts = d.risk_category.value_counts()
    rows,segments=[],[]
    for level,color in zip(levels,["#b84a45","#d48454","#c4a65d","#8795b5"]):
        count = counts.get(level,0)
        share = count/len(d)
        segments.append(f'<i style="width:{share:.4%};background:{color}"></i>')
        rows.append(f'<div class="risk-row"><span><i style="background:{color}"></i>{level}</span><strong>{count:,}</strong><small>{share:.1%}</small></div>')
    st.html('<div class="risk-strip">'+''.join(segments)+'</div>'+''.join(rows))
