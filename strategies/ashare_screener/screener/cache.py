from __future__ import annotations
from pathlib import Path
import pandas as pd

CACHE_ROOT = Path(__file__).resolve().parent.parent / "data" / "cache"


def cache_path(endpoint: str, key: str) -> Path:
    p = CACHE_ROOT / endpoint
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{key}.parquet"


def read_cache(endpoint: str, key: str) -> pd.DataFrame | None:
    p = cache_path(endpoint, key)
    if not p.exists():
        return None
    try:
        return pd.read_parquet(p)
    except Exception:
        return None


def write_cache(endpoint: str, key: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    try:
        df.to_parquet(cache_path(endpoint, key), index=False)
    except Exception:
        pass
