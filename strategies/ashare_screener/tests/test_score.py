import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from screener.score import (
    leader_score,
    momentum_score,
    capital_score,
    sector_score,
    total_score,
)


WEIGHTS = {"leader": 0.35, "momentum": 0.25, "capital": 0.20, "sector": 0.20}


def test_leader_score_strong_leader():
    row = pd.Series({
        "is_zt": 1,
        "is_sector_leader": 1,
        "consec_zt": 3,
        "zt_first_time_min": 5,
        "seal_ratio_to_circ_pct": 4.0,
        "zt_open_times": 0,
    })
    assert leader_score(row) == 100


def test_leader_score_weak():
    row = pd.Series({
        "is_zt": 0,
        "is_sector_leader": 0,
        "consec_zt": 0,
        "zt_first_time_min": 999,
        "seal_ratio_to_circ_pct": 0,
        "zt_open_times": 0,
    })
    assert leader_score(row) == 0


def test_momentum_sweet_spot():
    row = pd.Series({
        "volume_ratio": 3.0,
        "pct_change": 6.0,
        "price_pos_60": 0.85,
    })
    assert momentum_score(row) == 65


def test_capital_score_full():
    row = pd.Series({
        "net_mf_to_circ_pct": 2.5,
        "lhb_net_buy": 1e8,
        "hot_money_count": 3,
        "north_in_top10": 1,
    })
    assert capital_score(row) == 85


def test_sector_score_strong():
    row = pd.Series({"sector_height": 5, "sector_zt_count": 7})
    assert sector_score(row) == 55


def test_total_score_keys():
    row = pd.Series({})
    out = total_score(row, WEIGHTS)
    for k in ("leader_score", "momentum_score", "capital_score",
              "sector_score", "penalty", "total_score"):
        assert k in out
