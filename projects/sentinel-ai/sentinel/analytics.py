from datetime import timedelta
import pandas as pd


def filter_rows(d: pd.DataFrame, dates=(), amounts=None, selections=None, search="") -> pd.DataFrame:
    mask = pd.Series(True,index=d.index)
    if len(dates)==2:
        mask &= d.timestamp.between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1] + timedelta(days=1)),inclusive="left")
    if amounts:
        mask &= d.amount.between(*amounts)
    for col, values in (selections or {}).items():
        if values:
            mask &= d[col].isin(values)
    if search.strip():
        mask &= d.transaction_id.str.contains(search.strip(),case=False,regex=False) | d.customer_id.str.contains(search.strip(),case=False,regex=False)
    return d.loc[mask]


def summary(d):
    flagged = d[d.risk_category!="Low Risk"]
    return dict(total=len(d),volume=d.amount.sum(),flagged=len(flagged),
                high=(d.risk_category=="High Risk").sum(),critical=(d.risk_category=="Critical Risk").sum(),
                average=d.risk_score.mean() if len(d) else 0,exposure=flagged.amount.sum())
