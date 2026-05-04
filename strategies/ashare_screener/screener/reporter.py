from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data" / "candidates"


def write_outputs(date: str, gate: dict, plans: list[dict]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    js = DATA_DIR / f"candidates_{date}.json"
    js.write_text(
        json.dumps(
            {"date": date, "gate": gate, "candidates": plans},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    md = REPORT_DIR / f"{date}.md"
    md.write_text(_build_markdown(date, gate, plans), encoding="utf-8")
    return md, js


def _build_markdown(date: str, gate: dict, plans: list[dict]) -> str:
    lines: list[str] = [f"# A股盘后选股报告 {date}", ""]
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## 大盘闸门")
    lines.append("")
    lines.append(f"- 总开关: **{'开' if gate['all_open'] else '关'}**")
    for k, v in gate["checks"].items():
        lines.append(f"  - {k}: {'PASS' if v else 'FAIL'}")
    lines.append("")
    lines.append("- 详情:")
    for k, v in gate["details"].items():
        lines.append(f"  - {k}: {v}")
    lines.append("")

    by_tier: dict[str, list[dict]] = {"S": [], "A": [], "B": []}
    for p in plans:
        if p["tier"] in by_tier:
            by_tier[p["tier"]].append(p)

    for tier, label in [("S", "主攻"), ("A", "守正"), ("B", "观察")]:
        lst = by_tier[tier]
        lines.append(f"## {tier} 档 / {label} ({len(lst)})")
        lines.append("")
        if not lst:
            lines.append("(无)")
            lines.append("")
            continue
        for p in lst:
            t = p["today"]
            lines.append(f"### {p['ts_code']} {p['name']}  [总分 {p['score']}]")
            lines.append(
                f"- 板块: {p['sector']} | 类型: {p['candidate_type']} | "
                f"涨跌 {t['pct_change']:.2f}% | 换手 {t['turnover_rate']:.2f}% | "
                f"量比 {t['volume_ratio']:.2f} | 流通 {t['circ_mv_yi']} 亿"
            )
            s = p["scores"]
            lines.append(
                f"- 子分: 龙头 {s['leader']} / 动量 {s['momentum']} / "
                f"资金 {s['capital']} / 板块 {s['sector']} / 扣分 {s['penalty']}"
            )
            lines.append("- 入选理由:")
            for r in p["reasons"]:
                lines.append(f"  - {r}")
            if p["plan"]["position_pct"] > 0:
                pl = p["plan"]
                lines.append(f"- 计划仓位: {pl['position_pct']}%")
                lines.append(
                    f"- 竞价区间: +{pl['bid_range_pct'][0]}% 至 +{pl['bid_range_pct'][1]}%"
                )
                lines.append(f"- 止损: {pl['stop_loss_pct']}%")
                lines.append("- 放弃条件:")
                for a in pl["abort_if"]:
                    lines.append(f"  - {a}")
                lines.append("- 止盈:")
                for tp in pl["take_profit"]:
                    lines.append(f"  - {tp}")
            lines.append("")
    return "\n".join(lines)
