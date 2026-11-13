"""Atomic dataset initialization and optimistic investigation updates."""
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import URL, create_engine, text

from .data import generate, validate
from .detection import classify, contributions

STATES = ["Pending Review", "Investigating", "Escalated", "Resolved"]


def database(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(URL.create("sqlite", database=str(path)), connect_args={"timeout":120})


def initialize(engine, n: int = 100_000, seed: int = 42):
    with engine.begin() as con:
        con.exec_driver_sql("BEGIN IMMEDIATE")
        exists = con.scalar(text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='transactions'"))
        if exists:
            return
        logging.getLogger(__name__).info("Generating %d synthetic events", n)
        d = generate(n,seed)
        d["risk_score"] = contributions(d).sum(axis=1).clip(upper=100)
        d["risk_category"] = classify(d.risk_score)
        validate(d)
        d.to_sql("transactions",con,index=False,chunksize=1000)
        con.exec_driver_sql("CREATE UNIQUE INDEX tx_id ON transactions(transaction_id)")
        con.exec_driver_sql("CREATE INDEX customer_time ON transactions(customer_id,timestamp)")
        con.exec_driver_sql("""CREATE TABLE cases(transaction_id TEXT PRIMARY KEY,
                             status TEXT NOT NULL, notes TEXT NOT NULL, revision INTEGER NOT NULL)""")


def case(engine, tx: str) -> dict:
    with engine.connect() as con:
        row = con.execute(text("SELECT * FROM cases WHERE transaction_id=:tx"),{"tx":tx}).mappings().first()
    return dict(row) if row else dict(transaction_id=tx,status=STATES[0],notes="",revision=0)


def save(engine, tx: str, status: str, notes: str, revision: int):
    if status not in STATES or len(notes)>4000:
        raise ValueError("Invalid investigation status or notes")
    with engine.begin() as con:
        con.exec_driver_sql("BEGIN IMMEDIATE")
        if not con.scalar(text("SELECT 1 FROM transactions WHERE transaction_id=:tx"), {"tx":tx}):
            raise ValueError("Unknown transaction")
        current = con.scalar(text("SELECT revision FROM cases WHERE transaction_id=:tx"), {"tx":tx}) or 0
        if current!=revision:
            raise ValueError("Another analyst updated this case. Reload before saving.")
        con.execute(text("""INSERT INTO cases VALUES (:tx,:status,:notes,:rev)
                         ON CONFLICT(transaction_id) DO UPDATE SET status=excluded.status,
                         notes=excluded.notes,revision=excluded.revision"""),
                    dict(tx=tx,status=status,notes=notes,rev=current+1))


def load(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM transactions ORDER BY timestamp, transaction_id",engine,
                       parse_dates=["timestamp","previous_timestamp"])
