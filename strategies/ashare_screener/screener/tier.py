from __future__ import annotations
import pandas as pd


def assign_tier(df: pd.DataFrame, gate_open: bool, cfg: dict) -> pd.DataFrame:
    if df.empty:
        return df
    t = cfg["tier"]
    df = df.copy()

    def _tier(row):
        score = float(row["total_score"])
        leader = int(row.get("is_sector_leader", 0) or 0) == 1
        if gate_open and score >= t["s_min_score"] and leader:
            return "S"
        if gate_open and score >= t["a_min_score"]:
            return "A"
        if score >= t["b_min_score"]:
            return "B"
        return "X"

    df["tier"] = df.apply(_tier, axis=1)
    return df


def topk(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if df.empty:
        return df
    t = cfg["tier"]
    s = df.sort_values("total_score", ascending=False)
    return pd.concat([
        s[s["tier"] == "S"].head(t["max_s"]),
        s[s["tier"] == "A"].head(t["max_a"]),
        s[s["tier"] == "B"].head(t["max_b"]),
    ]).reset_index(drop=True)
