from __future__ import annotations
import os
import time
import pandas as pd
import tushare as ts
from .cache import read_cache, write_cache

_pro = None


def pro():
    global _pro
    if _pro is None:
        env_token = os.environ.get("TUSHARE_TOKEN", "").strip()
        if env_token:
            ts.set_token(env_token)
        _pro = ts.pro_api()
    return _pro


def _retry(fn, tries: int = 3, delay: float = 2.0):
    last_err: Exception | None = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(delay * (i + 1))
    if last_err is not None:
        raise last_err


def fetch(endpoint: str, date: str, **kwargs) -> pd.DataFrame:
    cached = read_cache(endpoint, date)
    if cached is not None:
        return cached
    method = getattr(pro(), endpoint)
    try:
        df = _retry(lambda: method(trade_date=date, **kwargs))
    except Exception as e:
        print(f"  [warn] {endpoint}({date}) failed: {e}")
        df = pd.DataFrame()
    if df is None:
        df = pd.DataFrame()
    write_cache(endpoint, date, df)
    return df


def fetch_no_date(endpoint: str, key: str = "all", **kwargs) -> pd.DataFrame:
    cached = read_cache(endpoint, key)
    if cached is not None:
        return cached
    method = getattr(pro(), endpoint)
    try:
        df = _retry(lambda: method(**kwargs))
    except Exception as e:
        print(f"  [warn] {endpoint}({key}) failed: {e}")
        df = pd.DataFrame()
    if df is None:
        df = pd.DataFrame()
    write_cache(endpoint, key, df)
    return df
