from __future__ import annotations
import pandas as pd
from . import data_pull


def market_gate(date: str, cfg: dict) -> dict:
    g = cfg["market_gate"]
    out: dict = {"date": date, "all_open": False, "details": {}, "checks": {}}

    lu = data_pull.limit_list(date)
    if not lu.empty and "limit" in lu.columns:
        zt_count = int((lu["limit"] == "U").sum())
        dt_count = int((lu["limit"] == "D").sum())
        u = lu[lu["limit"] == "U"]
        max_consec = int(u["limit_times"].max()) if not u.empty else 0
    else:
        zt_count = dt_count = max_consec = 0

    daily = data_pull.daily(date)
    total_amount_yi = float(daily["amount"].sum() / 1e5) if not daily.empty else 0.0

    out["details"] = {
        "zt_count": zt_count,
        "dt_count": dt_count,
        "zt_dt_ratio": round(zt_count / max(1, dt_count), 2),
        "max_consec": max_consec,
        "total_amount_yi": round(total_amount_yi, 1),
    }
    out["checks"] = {
        "zt_dt_ratio_ok": out["details"]["zt_dt_ratio"] >= g["min_zt_dt_ratio"],
        "zt_count_ok": zt_count >= g["min_zt_count"],
        "max_consec_ok": max_consec >= g["min_max_consec"],
        "amount_ok": total_amount_yi >= g["min_amount_yi"],
    }
    out["all_open"] = all(out["checks"].values())
    return out


def apply_blacklist(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    bl = cfg["blacklist"]
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    mask &= df["is_st"] == 0
    mask &= df["circ_mv"].fillna(0) >= bl["min_circ_mv_wan"]
    mask &= df["circ_mv"].fillna(0) <= bl["max_circ_mv_wan"]
    mask &= df["n_day_return_5"].fillna(0) < bl["max_5d_return_pct"]
    mask &= df["is_one_word"] == 0
    return df[mask].copy()


def candidate_layer(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if df.empty:
        return df
    c = cfg["candidate"]
    is_first = (
        (df["is_zt"] == 1)
        & (df["consec_zt"] == 1)
        & (df["zt_first_time_min"] <= c["first_zt_max_time_min"])
        & (df["seal_ratio_to_circ_pct"] >= c["min_seal_ratio_pct"])
    )
    is_consec = (
        (df["is_zt"] == 1)
        & (df["consec_zt"] >= 2)
        & (df["is_sector_leader"] == 1)
    )
    is_break = (
        (df["is_zt"] == 0)
        & (df["pct_change"].fillna(0) >= c["breakout_min_pct"])
        & (df["volume_ratio"].fillna(0) >= c["breakout_min_vol_ratio"])
        & (df["sector_zt_count"] >= c["breakout_min_sector_zt"])
    )
    df = df.copy()
    df["candidate_type"] = ""
    df.loc[is_first, "candidate_type"] = "first_zt"
    df.loc[is_consec, "candidate_type"] = "consec_leader"
    df.loc[is_break, "candidate_type"] = "breakout"
    return df[df["candidate_type"] != ""].copy()
