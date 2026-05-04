from __future__ import annotations
from datetime import datetime, timedelta
from .tushare_client import pro


def normalize_date(d: str) -> str:
    return d.replace("-", "").replace("/", "")[:8]


def is_trade_date(date: str) -> bool:
    df = pro().trade_cal(exchange="SSE", start_date=date, end_date=date)
    if df is None or df.empty:
        return False
    return int(df.iloc[0]["is_open"]) == 1


def previous_trade_dates(date: str, n: int) -> list[str]:
    end = datetime.strptime(date, "%Y%m%d")
    start = end - timedelta(days=n * 3 + 30)
    df = pro().trade_cal(
        exchange="SSE",
        start_date=start.strftime("%Y%m%d"),
        end_date=date,
    )
    if df is None or df.empty:
        return []
    df = df[df["is_open"] == 1].sort_values("cal_date")
    dates = df["cal_date"].tolist()
    if date in dates:
        idx = dates.index(date)
        return dates[max(0, idx - n):idx]
    return dates[-n:]
