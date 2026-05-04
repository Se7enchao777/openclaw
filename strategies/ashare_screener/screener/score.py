from __future__ import annotations
import pandas as pd


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def leader_score(row) -> float:
    s = 0.0
    if int(row.get("is_sector_leader", 0) or 0):
        s += 50
    s += min(int(row.get("consec_zt", 0) or 0) * 10, 30)
    ft = float(row.get("zt_first_time_min", 999) or 999)
    if ft <= 15:
        s += 15
    elif ft <= 30:
        s += 8
    sr = float(row.get("seal_ratio_to_circ_pct", 0) or 0)
    if sr >= 3:
        s += 15
    elif sr >= 1.5:
        s += 8
    ot = int(row.get("zt_open_times", 0) or 0)
    if ot == 0 and int(row.get("is_zt", 0) or 0) == 1:
        s += 5
    elif ot >= 2:
        s -= 10
    return _clip(s)


def momentum_score(row) -> float:
    s = 0.0
    vr = float(row.get("volume_ratio", 0) or 0)
    if 2 <= vr <= 5:
        s += 30
    elif vr < 2:
        s += max(0, 30 * vr / 2)
    elif vr > 8:
        s -= 10
    else:
        s += max(0, 30 * (1 - (vr - 5) / 3))
    pc = float(row.get("pct_change", 0) or 0)
    if pc >= 0:
        s += 15
    pos = float(row.get("price_pos_60", 0) or 0)
    if pos >= 0.8:
        s += 20
    elif pos >= 0.6:
        s += 10
    return _clip(s)


def capital_score(row) -> float:
    s = 0.0
    nf = float(row.get("net_mf_to_circ_pct", 0) or 0)
    if nf > 1:
        s += 25
    elif nf > 0:
        s += 10
    if float(row.get("lhb_net_buy", 0) or 0) > 0:
        s += 20
    hm = int(row.get("hot_money_count", 0) or 0)
    if hm >= 2:
        s += 25
    elif hm == 1:
        s += 10
    elif hm < 0:
        s -= 15
    if int(row.get("north_in_top10", 0) or 0):
        s += 15
    return _clip(s)


def sector_score(row) -> float:
    s = 0.0
    sh = int(row.get("sector_height", 0) or 0)
    if sh >= 3:
        s += 30
    elif sh >= 2:
        s += 15
    sc = int(row.get("sector_zt_count", 0) or 0)
    if sc >= 5:
        s += 25
    elif sc >= 3:
        s += 12
    return _clip(s)


def penalty(row) -> float:
    p = 0.0
    r5 = float(row.get("n_day_return_5", 0) or 0)
    if 40 <= r5 < 60:
        p += 15
    return p


def total_score(row, weights: dict) -> dict:
    ls = leader_score(row)
    ms = momentum_score(row)
    cs = capital_score(row)
    ss = sector_score(row)
    pn = penalty(row)
    total = (
        weights["leader"] * ls
        + weights["momentum"] * ms
        + weights["capital"] * cs
        + weights["sector"] * ss
        - pn
    )
    return {
        "leader_score": round(ls, 1),
        "momentum_score": round(ms, 1),
        "capital_score": round(cs, 1),
        "sector_score": round(ss, 1),
        "penalty": round(pn, 1),
        "total_score": round(total, 1),
    }


def score_all(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    if df.empty:
        return df
    rows = df.apply(lambda r: pd.Series(total_score(r, weights)), axis=1)
    return pd.concat(
        [df.reset_index(drop=True), rows.reset_index(drop=True)], axis=1
    )
