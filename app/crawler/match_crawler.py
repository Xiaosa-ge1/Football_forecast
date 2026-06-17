import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def fetch_match_info() -> dict:
    """
    爬取当日比赛/伤停信息。
    原型阶段返回模拟数据，后续可接入真实数据源。
    """
    today = date.today().isoformat()

    matches = [
        {"date": today, "home": "墨西哥", "away": "南非",
         "venue": "阿兹特克球场", "status": "未开始"},
        {"date": today, "home": "韩国", "away": "捷克",
         "venue": "首尔世界杯球场", "status": "未开始"},
    ]

    record = {
        "date": today,
        "matches": matches,
        "source": "模拟数据（原型阶段）",
        "injuries": [],
        "weather": {},
    }

    # 保存到 data/matches/
    match_dir = BASE_DIR / "data" / "matches"
    match_dir.mkdir(parents=True, exist_ok=True)
    path = match_dir / f"matches_{today}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return record
