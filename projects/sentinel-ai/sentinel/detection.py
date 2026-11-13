"""Shared feature contract for historical and simulated observations."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LEVELS = ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]
RULES = ["Spending spike", "Rapid activity", "Unseen device", "IP mismatch", "New beneficiary", "Cross-border", "Young account"]
WEIGHTS = (30, 26, 14, 16, 13, 8, 6)


def features(d: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(dict(spend_ratio=d.amount/d.historical_average, recent=d.recent_count,
        device=d.new_device, geography=(d.origin!=d.ip_country).astype(int),
        beneficiary=d.new_beneficiary, international=d.international, age=d.account_age), index=d.index)


def contributions(d: pd.DataFrame, weights=WEIGHTS) -> pd.DataFrame:
    if len(weights)!=len(RULES) or any(w<0 or w>100 for w in weights):
        raise ValueError("Each rule needs a weight from 0 to 100")
    x = features(d)
    flags = [x.spend_ratio>=3, x.recent>=2, x.device, x.geography, x.beneficiary, x.international, x.age<30]
    return pd.DataFrame({name: flag.astype(int)*weight for name,flag,weight in zip(RULES,flags,weights)})


def classify(scores, thresholds=(25,50,75)):
    if not 0 < thresholds[0] < thresholds[1] < thresholds[2] <= 100:
        raise ValueError("Cutoffs must increase within 1–100")
    return np.array(LEVELS)[np.searchsorted(thresholds, scores, side="right")]


@dataclass
class Models:
    isolation: IsolationForest
    supervised: object
    calibration: np.ndarray
    cutoff: pd.Timestamp
    baseline_amount: float

    def predict(self, d: pd.DataFrame):
        x = features(d)
        raw = -self.isolation.score_samples(x)
        percentile = 100*np.searchsorted(self.calibration,raw,side="right")/len(self.calibration)
        return percentile, self.supervised.predict_proba(x)[:,1]


def train(d: pd.DataFrame) -> Models:
    cutoff = d.timestamp.sort_values().iloc[int(.8*len(d))]
    past = d[d.timestamp<cutoff]
    if past.fraud_label.nunique()!=2:
        raise ValueError("Training requires both label classes")
    x = features(past)
    forest = IsolationForest(n_estimators=80, random_state=42).fit(x)
    logistic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(x,past.fraud_label)
    return Models(forest,logistic,np.sort(-forest.score_samples(x)),cutoff,float(past.amount.quantile(.99)))


def metrics(labels, predictions) -> dict:
    tn,fp,fn,tp = confusion_matrix(labels,predictions,labels=[0,1]).ravel()
    p,r,f,_ = precision_recall_fscore_support(labels,predictions,average="binary",zero_division=0)
    return dict(Precision=p,Recall=r,F1=f,FPR=fp/max(1,tn+fp),TN=tn,FP=fp,FN=fn,TP=tp)
