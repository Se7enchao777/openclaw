from __future__ import annotations
import pandas as pd


def make_plan(row: pd.Series, cfg: dict) -> dict:
    p = cfg["plan"]
    tier = row["tier"]
    pos = {
        "S": p["s_position_pct"],
        "A": p["a_position_pct"],
    }.get(tier, 0)

    reasons: list[str] = []
    if int(row.get("is_sector_leader", 0) or 0):
        reasons.append(f"板块龙一({row.get('primary_sector', '?')})")
    if int(row.get("consec_zt", 0) or 0) >= 2:
        reasons.append(f"{int(row['consec_zt'])} 连板")
    ft = float(row.get("zt_first_time_min", 999) or 999)
    if ft <= 30:
        h = 9
        m = 30 + int(ft)
        if m >= 60:
            h += 1
            m -= 60
        reasons.append(f"首封 {h}:{m:02d}")
    sr = float(row.get("seal_ratio_to_circ_pct", 0) or 0)
    if sr >= 1.5:
        reasons.append(f"封单/流通市值 {sr:.1f}%")
    hm = int(row.get("hot_money_count", 0) or 0)
    if hm >= 2:
        reasons.append(f"知名游资 {hm} 席")
    lhb = float(row.get("lhb_net_buy", 0) or 0)
    if lhb > 0:
        reasons.append(f"龙虎榜净买入 {lhb / 1e4:.0f} 万")
    sc = int(row.get("sector_zt_count", 0) or 0)
    if sc >= 3:
        reasons.append(f"板块 {sc} 涨停")
    if int(row.get("north_in_top10", 0) or 0):
        reasons.append("北向 Top10")
    nf = float(row.get("net_mf_to_circ_pct", 0) or 0)
    if nf > 1:
        reasons.append(f"主力净流入/流通 {nf:.2f}%")

    return {
        "ts_code": row["ts_code"],
        "name": row.get("name", ""),
        "tier": tier,
        "score": float(row["total_score"]),
        "scores": {
            "leader": float(row["leader_score"]),
            "momentum": float(row["momentum_score"]),
            "capital": float(row["capital_score"]),
            "sector": float(row["sector_score"]),
            "penalty": float(row["penalty"]),
        },
        "sector": row.get("primary_sector", "") or "",
        "candidate_type": row.get("candidate_type", ""),
        "today": {
            "close": float(row.get("close", 0) or 0),
            "pct_change": float(row.get("pct_change", 0) or 0),
            "turnover_rate": float(row.get("turnover_rate", 0) or 0),
            "volume_ratio": float(row.get("volume_ratio", 0) or 0),
            "circ_mv_yi": round(float(row.get("circ_mv", 0) or 0) / 1e4, 2),
            "is_zt": int(row.get("is_zt", 0) or 0),
            "consec_zt": int(row.get("consec_zt", 0) or 0),
        },
        "reasons": reasons,
        "plan": {
            "position_pct": pos,
            "bid_range_pct": p["bid_range_pct"],
            "abort_if": [
                f"竞价低开 < +{p['min_bid_pct']}% 或高开 > +{p['max_bid_pct']}%",
                f"9:45 前跌破均价线 {p['intraday_break_pct']}%",
                "板块第二梯队 30 分钟内炸板 ≥ 2 只",
            ],
            "stop_loss_pct": p["stop_loss_pct"],
            "take_profit": [
                "T+1 涨停 → T+2 减仓 1/2;封板再封 → 留 1/2;炸板 → 全部清仓",
                "出现放量长上影 / 量价背离 → 全部止盈",
            ],
        },
    }
