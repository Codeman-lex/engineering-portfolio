"""Seeded customer event stream with strictly prior behavioral features."""
from datetime import datetime, timedelta
from collections import defaultdict, deque

import numpy as np
import pandas as pd

COUNTRIES = ["USA", "GBR", "CAN", "DEU", "FRA", "NGA", "IND", "SGP", "AUS"]
TYPES = ["Purchase", "Transfer", "Withdrawal"]


def generate(n: int = 100_000, seed: int = 42) -> pd.DataFrame:
    if n < 1:
        raise ValueError("Transaction count must be positive")
    rng = np.random.default_rng(seed)
    customers = max(8, n // 45)
    popularity = rng.lognormal(0, .8, customers)
    ids = rng.choice(customers, n, p=popularity / popularity.sum())
    times = np.sort(rng.integers(0, 90 * 86400, n))
    # Groups share a customer, device and short time window. Some are benign.
    groups = np.zeros(n, dtype=int)
    labels = rng.random(n) < .003
    for i in range(0, n - 4, 4):
        if rng.random() < .026:
            ids[i:i+4] = ids[i]
            times[i:i+4] = times[i] + np.arange(4) * 19
            groups[i:i+4] = i + 1
            labels[i:i+4] = rng.random() < .72
    home = rng.choice(COUNTRIES, customers)
    prior = rng.lognormal(4.2, .75, customers)
    age = rng.integers(1, 3000, customers)
    counts = np.zeros(customers, int)
    sums = np.zeros(customers)
    recent = defaultdict(deque)
    seen = defaultdict(set)
    previous = {}
    rows = []
    epoch = datetime(2026, 7, 1)
    for i in np.argsort(times, kind="stable"):
        c, t = int(ids[i]), int(times[i])
        cluster, fraud = groups[i], bool(labels[i])
        device = f"D{c}-" + (f"B{cluster}" if cluster else str(rng.choice(4, p=[.94,.035,.02,.005])))
        amount = round(max(.01, prior[c] * rng.lognormal(-.22, .7) *
                           (rng.uniform(2, 12) if cluster or (fraud and rng.random()<.7) else 1)), 2)
        typ = "Transfer" if cluster else rng.choice(TYPES, p=[.74,.18,.08])
        dest = rng.choice(COUNTRIES) if rng.random() < (.63 if cluster else .12) else home[c]
        ip = rng.choice(COUNTRIES) if rng.random() < (.52 if cluster else .04) else home[c]
        q = recent[c]
        while q and q[0] < t - 3600:
            q.popleft()
        stamp = epoch + timedelta(seconds=t)
        category = rng.choice(["Groceries","Retail","Travel","Dining","Services"]) if typ=="Purchase" else typ
        rows.append((f"TX-{i+1:07}", f"CU-{c:05}", stamp, amount, "USD", typ, category,
                     f"M-{category[:2]}{rng.integers(1,90):03}", {"Purchase":"Card","Withdrawal":"ATM","Transfer":"Online"}[typ],
                     home[c], dest, ip, device, age[c]+t//86400,
                     (sums[c]+5*prior[c])/(counts[c]+5), previous.get(c), len(q),
                     int(device not in seen[c]), int(dest!=home[c]), int(typ=="Transfer" and rng.random()<(.75 if cluster else .12)),
                     rng.choice(["Settled","Pending","Declined"],p=[.96,.03,.01]), int(fraud)))
        q.append(t)
        previous[c] = stamp
        seen[c].add(device)
        counts[c] += 1
        sums[c] += amount
    frame = pd.DataFrame(rows, columns="transaction_id customer_id timestamp amount currency transaction_type merchant_category merchant_id channel origin destination ip_country device account_age historical_average previous_timestamp recent_count new_device international new_beneficiary status fraud_label".split())
    validate(frame)
    return frame


def validate(frame: pd.DataFrame) -> None:
    required = set("transaction_id customer_id timestamp amount historical_average recent_count account_age origin destination ip_country new_device new_beneficiary international fraud_label".split())
    if required.difference(frame) or frame[list(required)].isna().any().any():
        raise ValueError("Missing required data")
    nums = frame[["historical_average","amount","account_age","recent_count"]]
    if not np.isfinite(nums).all().all() or (nums.iloc[:,:2]<=0).any().any() or (nums.iloc[:,2:]<0).any().any():
        raise ValueError("Invalid amounts or history")
    if frame.transaction_id.duplicated().any() or pd.to_datetime(frame.timestamp, errors="coerce", format="ISO8601").isna().any():
        raise ValueError("Invalid date or duplicate transaction")
    if not frame[["fraud_label","international","new_device","new_beneficiary"]].isin([0,1]).all().all():
        raise ValueError("Indicators must be binary")
