from __future__ import annotations
import pandas as pd
from .tushare_client import fetch, fetch_no_date


def daily(date: str) -> pd.DataFrame:
    return fetch("daily", date)


def daily_basic(date: str) -> pd.DataFrame:
    return fetch("daily_basic", date)


def limit_list(date: str) -> pd.DataFrame:
    return fetch("limit_list_d", date)


def top_list(date: str) -> pd.DataFrame:
    return fetch("top_list", date)


def top_inst(date: str) -> pd.DataFrame:
    return fetch("top_inst", date)


def moneyflow(date: str) -> pd.DataFrame:
    return fetch("moneyflow", date)


def hsgt_top10(date: str) -> pd.DataFrame:
    return fetch("hsgt_top10", date)


def kpl_concept(date: str) -> pd.DataFrame:
    return fetch("kpl_concept", date)


def kpl_concept_cons(date: str) -> pd.DataFrame:
    return fetch("kpl_concept_cons", date)


def stock_basic() -> pd.DataFrame:
    return fetch_no_date("stock_basic", "L", list_status="L")
