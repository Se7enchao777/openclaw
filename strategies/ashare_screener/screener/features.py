from __future__ import annotations
from pathlib import Path
import pandas as pd
import yaml
from . import data_pull
from .calendar_util import previous_trade_dates


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _parse_time_min(t) -> float:
    if t is None or pd.isna(t):
        return 999.0
    s = str(t).strip()
    if not s or s in ("nan", "None"):
        return 999.0
    if ":" in s:
        parts = s.split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
    else:
        s = s.zfill(6)
        h = int(s[:2])
        m = int(s[2:4])
    return max(0.0, (h * 60 + m) - (9 * 60 + 30))


def _hot_money_dict() -> tuple[set, set]:
    p = CONFIG_DIR / "hot_money_seats.yaml"
    if not p.exists():
        return set(), set()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return set(data.get("famous_seats", []) or []), set(data.get("blacklist_seats", []) or [])


def _hot_money_count(date: str) -> pd.DataFrame:
    famous, black = _hot_money_dict()
    inst = data_pull.top_inst(date)
    if inst.empty or "exalter" not in inst.columns:
        return pd.DataFrame(columns=["ts_code", "hot_money_count"])
    rows = []
    for code, g in inst.groupby("ts_code"):
        n_f = g["exalter"].isin(famous).sum()
        n_b = g["exalter"].isin(black).sum()
        rows.append({"ts_code": code, "hot_money_count": int(n_f - n_b)})
    return pd.DataFrame(rows)


def _sector_mapping(date: str) -> pd.DataFrame:
    cols = ["ts_code", "primary_sector", "sector_zt_count", "sector_height", "is_sector_leader"]
    try:
        concepts = data_pull.kpl_concept(date)
        cons = data_pull.kpl_concept_cons(date)
    except Exception:
        return pd.DataFrame(columns=cols)
    if concepts.empty or cons.empty or "con_code" not in cons.columns:
        return pd.DataFrame(columns=cols)

    zt_col = "z_t_num" if "z_t_num" in concepts.columns else None
    if zt_col is None:
        for c in ("lu_num", "up_num", "limit_up_num"):
            if c in concepts.columns:
                zt_col = c
                break
    if zt_col is None:
        concepts = concepts.copy()
        concepts["__zt"] = 0
        zt_col = "__zt"

    cr = concepts[["ts_code", "name", zt_col]].rename(
        columns={"ts_code": "concept_code", "name": "concept_name", zt_col: "sector_zt_count"}
    )
    cm = cons[["ts_code", "con_code"]].rename(
        columns={"ts_code": "concept_code", "con_code": "ts_code_stock"}
    )
    cm = cm.merge(cr, on="concept_code", how="left")
    cm = cm.sort_values(["ts_code_stock", "sector_zt_count"], ascending=[True, False])
    primary = cm.drop_duplicates("ts_code_stock", keep="first").rename(
        columns={"ts_code_stock": "ts_code", "concept_name": "primary_sector"}
    )[["ts_code", "primary_sector", "sector_zt_count"]]

    lu = data_pull.limit_list(date)
    if lu.empty or "limit" not in lu.columns:
        primary["sector_height"] = 0
        primary["is_sector_leader"] = 0
        return primary
    lu_u = lu[lu["limit"] == "U"][["ts_code", "limit_times", "first_time"]].copy()
    sec = primary.merge(lu_u, on="ts_code", how="left")
    sh = sec.groupby("primary_sector")["limit_times"].max().reset_index()
    sh.columns = ["primary_sector", "sector_height"]
    primary = primary.merge(sh, on="primary_sector", how="left")
    primary["sector_height"] = primary["sector_height"].fillna(0).astype(int)

    leaders_df = sec.dropna(subset=["limit_times"]).copy()
    if leaders_df.empty:
        primary["is_sector_leader"] = 0
    else:
        leaders_df["limit_times"] = leaders_df["limit_times"].astype(int)
        leaders_df = leaders_df.sort_values(
            ["primary_sector", "limit_times", "first_time"],
            ascending=[True, False, True],
        )
        leader_codes = set(
            leaders_df.drop_duplicates("primary_sector", keep="first")["ts_code"].tolist()
        )
        primary["is_sector_leader"] = primary["ts_code"].isin(leader_codes).astype(int)
    return primary


def _multi_day_return(df: pd.DataFrame, date: str) -> pd.DataFrame:
    prev = previous_trade_dates(date, 5)
    cum = pd.Series(0.0, index=df.index)
    for d in prev:
        rd = data_pull.daily(d)
        if rd.empty:
            continue
        rd = rd[["ts_code", "pct_chg"]].rename(columns={"pct_chg": f"_pct_{d}"})
        df = df.merge(rd, on="ts_code", how="left")
        cum = cum + df[f"_pct_{d}"].fillna(0).reset_index(drop=True)
    df["n_day_return_5"] = cum.values + df["pct_change"].fillna(0).values
    df = df[[c for c in df.columns if not c.startswith("_pct_")]]
    return df


def build_features(date: str) -> pd.DataFrame:
    daily = data_pull.daily(date)
    basic = data_pull.daily_basic(date)
    if daily.empty or basic.empty:
        return pd.DataFrame()

    df = daily.merge(
        basic[["ts_code", "turnover_rate", "volume_ratio", "circ_mv", "total_mv"]],
        on="ts_code",
        how="left",
    )
    df = df.rename(columns={"pct_chg": "pct_change"})

    lu = data_pull.limit_list(date)
    if not lu.empty and "limit" in lu.columns:
        lu_u = lu[lu["limit"] == "U"][[
            "ts_code", "first_time", "last_time", "open_times",
            "limit_times", "fd_amount", "fc_ratio",
        ]].rename(columns={
            "first_time": "zt_first_time",
            "last_time": "zt_last_time",
            "open_times": "zt_open_times",
            "limit_times": "consec_zt",
            "fd_amount": "seal_amount",
            "fc_ratio": "seal_ratio_to_circ_pct",
        })
        lu_u["zt_first_time_min"] = lu_u["zt_first_time"].apply(_parse_time_min)
        lu_u["is_zt"] = 1
        df = df.merge(lu_u, on="ts_code", how="left")

    for col, default in [
        ("is_zt", 0), ("consec_zt", 0), ("zt_first_time_min", 999),
        ("zt_open_times", 0), ("seal_amount", 0), ("seal_ratio_to_circ_pct", 0),
    ]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)

    df["is_zt"] = df["is_zt"].astype(int)
    df["consec_zt"] = df["consec_zt"].astype(int)
    df["zt_open_times"] = df["zt_open_times"].astype(int)
    df["is_one_word"] = (
        (df["is_zt"] == 1)
        & (df["zt_first_time_min"] <= 1)
        & (df["zt_open_times"] == 0)
        & (df["high"] == df["low"])
    ).astype(int)

    mf = data_pull.moneyflow(date)
    if not mf.empty and "net_mf_amount" in mf.columns:
        df = df.merge(mf[["ts_code", "net_mf_amount"]], on="ts_code", how="left")
    if "net_mf_amount" not in df.columns:
        df["net_mf_amount"] = 0
    df["net_mf_amount"] = df["net_mf_amount"].fillna(0)
    df["net_mf_to_circ_pct"] = (df["net_mf_amount"] / 10) / df["circ_mv"].replace(0, pd.NA) * 100
    df["net_mf_to_circ_pct"] = df["net_mf_to_circ_pct"].fillna(0)

    lhb = data_pull.top_list(date)
    if not lhb.empty and "net_amount" in lhb.columns:
        s = lhb.groupby("ts_code")["net_amount"].sum().reset_index()
        s = s.rename(columns={"net_amount": "lhb_net_buy"})
        df = df.merge(s, on="ts_code", how="left")
    if "lhb_net_buy" not in df.columns:
        df["lhb_net_buy"] = 0
    df["lhb_net_buy"] = df["lhb_net_buy"].fillna(0)

    hm = _hot_money_count(date)
    df = df.merge(hm, on="ts_code", how="left")
    df["hot_money_count"] = df["hot_money_count"].fillna(0).astype(int)

    north = data_pull.hsgt_top10(date)
    if not north.empty and "ts_code" in north.columns:
        codes = set(north["ts_code"].tolist())
        df["north_in_top10"] = df["ts_code"].isin(codes).astype(int)
    else:
        df["north_in_top10"] = 0

    sec = _sector_mapping(date)
    if not sec.empty:
        df = df.merge(sec, on="ts_code", how="left")
    for c, default in [("primary_sector", ""), ("sector_zt_count", 0),
                       ("sector_height", 0), ("is_sector_leader", 0)]:
        if c not in df.columns:
            df[c] = default
        df[c] = df[c].fillna(default)
    df["sector_zt_count"] = df["sector_zt_count"].astype(int)
    df["sector_height"] = df["sector_height"].astype(int)
    df["is_sector_leader"] = df["is_sector_leader"].astype(int)

    sb = data_pull.stock_basic()
    if not sb.empty:
        df = df.merge(sb[["ts_code", "name", "list_date"]], on="ts_code", how="left")
    if "name" not in df.columns:
        df["name"] = ""
    df["is_st"] = df["name"].astype(str).str.contains("ST", na=False).astype(int)

    df["price_pos_60"] = 0.5
    df = _multi_day_return(df, date)
    df = df[~df["ts_code"].str.endswith(".BJ", na=False)].copy()
    return df
