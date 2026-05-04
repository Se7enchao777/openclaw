"""A股盘后选股入口。

用法:
    cd strategies/ashare_screener
    python run_daily.py --date 20260430
"""
from __future__ import annotations
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from screener.calendar_util import normalize_date, is_trade_date  # noqa: E402
from screener.features import build_features  # noqa: E402
from screener.filter import market_gate, apply_blacklist, candidate_layer  # noqa: E402
from screener.score import score_all  # noqa: E402
from screener.tier import assign_tier, topk  # noqa: E402
from screener.plan import make_plan  # noqa: E402
from screener.reporter import write_outputs  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load(
        (ROOT / "config" / "thresholds.yaml").read_text(encoding="utf-8")
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    args = ap.parse_args()
    date = normalize_date(args.date)

    if not is_trade_date(date):
        print(f"[!] {date} 不是交易日,退出")
        return 1

    cfg = load_config()

    print(f"[1/6] 大盘闸门检查 {date}")
    gate = market_gate(date, cfg)
    print(f"      闸门: {'开' if gate['all_open'] else '关'} | {gate['details']}")

    print("[2/6] 拉取与构建特征")
    df = build_features(date)
    print(f"      全市场样本: {len(df)} 行")

    print("[3/6] 黑名单剔除")
    df = apply_blacklist(df, cfg)
    print(f"      剩余: {len(df)} 行")

    print("[4/6] 候选身份判定")
    df = candidate_layer(df, cfg)
    print(f"      候选: {len(df)} 只")

    if df.empty:
        print("      无候选,只输出闸门状态")
        md, js = write_outputs(date, gate, [])
        print(f"      报告: {md}")
        print(f"      JSON: {js}")
        return 0

    print("[5/6] 综合打分与分档")
    df = score_all(df, cfg["weights"])
    df = assign_tier(df, gate["all_open"], cfg)
    df = topk(df, cfg)

    print("[6/6] 生成计划与报告")
    plans = [make_plan(r, cfg) for _, r in df.iterrows()]
    md, js = write_outputs(date, gate, plans)
    print(f"      报告: {md}")
    print(f"      JSON: {js}")

    s_n = sum(1 for p in plans if p["tier"] == "S")
    a_n = sum(1 for p in plans if p["tier"] == "A")
    b_n = sum(1 for p in plans if p["tier"] == "B")
    print(f"      档位: S={s_n} A={a_n} B={b_n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
