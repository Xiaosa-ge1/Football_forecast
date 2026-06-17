#!/usr/bin/env python3
"""
每日情报更新脚本。
运行方式:  python scripts/update_daily.py [--date YYYY-MM-DD]

从 data/matches/ 读取最新比赛信息，生成每日情报摘要写入 data/daily_info.json。
这个过程模拟了"搬运每天的比赛信息，并生成相应信息概述加入动态 skill"。
"""

import argparse
import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_latest_matches() -> list[dict]:
    """从 data/matches/ 读取最新比赛数据。"""
    match_dir = BASE_DIR / "data" / "matches"
    if not match_dir.exists():
        return []

    files = sorted(match_dir.glob("matches_*.json"), reverse=True)
    if not files:
        return []

    try:
        data = json.loads(files[0].read_text(encoding="utf-8"))
        return data.get("matches", [])
    except (json.JSONDecodeError, KeyError):
        return []


def build_daily_info(matches: list[dict], date_str: str) -> dict:
    """根据比赛信息生成 daily_info.json 所需格式。"""
    info_lines = []

    for m in matches:
        home = m.get("home", "?")
        away = m.get("away", "?")
        venue = m.get("venue", "")
        status = m.get("status", "未开始")

        if status == "未开始":
            line = f"今日比赛：{home} vs {away}"
            if venue:
                line += f"（{venue}）"
            info_lines.append(line)
        elif status == "已结束":
            score = m.get("score", "?-?")
            info_lines.append(f"完场：{home} {score} {away}")
        else:
            info_lines.append(f"{home} vs {away} — {status}")

    if not info_lines:
        info_lines.append("暂无今日比赛信息")

    return {"date": date_str, "info": info_lines}


def main():
    parser = argparse.ArgumentParser(description="更新每日情报")
    parser.add_argument("--date", default=date.today().isoformat(), help="日期 YYYY-MM-DD")
    args = parser.parse_args()

    matches = load_latest_matches()
    daily = build_daily_info(matches, args.date)

    daily_path = BASE_DIR / "data" / "daily_info.json"
    daily_path.write_text(json.dumps(daily, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 每日情报已更新: {daily_path}")
    print(f"   共 {len(daily['info'])} 条情报")


if __name__ == "__main__":
    main()
