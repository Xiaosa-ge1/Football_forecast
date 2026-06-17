"""爬取编排器：调用懂球帝适配器获取真实数据，写入 SQLite + JSON 缓存。"""

import json
from datetime import date, datetime
from pathlib import Path

import httpx

from app.crawler.base import CrawlResult, circuit_breaker
from app.crawler.sources.dongqiudi import DongqiudiCrawler
from app.crawler.validator import validate_matches, validate_standings, validate_injuries
from app.database import get_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _model_to_row_dict(match) -> dict:
    """将 MatchDetail Pydantic 模型转为 SQLite 行 dict。"""
    stats = match.stats
    stats_json = json.dumps({
        "possession": stats.possession if stats else "",
        "shots": list(stats.shots) if stats else [0, 0],
        "shots_on_target": list(stats.shots_on_target) if stats else [0, 0],
        "corners": list(stats.corners) if stats else [0, 0],
        "fouls": list(stats.fouls) if stats else [0, 0],
        "yellow_cards": list(stats.yellow_cards) if stats else [0, 0],
        "red_cards": list(stats.red_cards) if stats else [0, 0],
        "offsides": list(stats.offsides) if stats else [0, 0],
        "passes": list(stats.passes) if stats else [0, 0],
    }, ensure_ascii=False)

    return {
        "match_id": match.match_id,
        "date": match.date,
        "home": match.home,
        "away": match.away,
        "venue": match.venue,
        "status": match.status,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "events_json": json.dumps([e.model_dump() for e in match.events], ensure_ascii=False),
        "home_lineup_json": json.dumps(match.home_lineup, ensure_ascii=False),
        "away_lineup_json": json.dumps(match.away_lineup, ensure_ascii=False),
        "stats_json": stats_json,
        "referee": match.referee,
        "attendance": match.attendance,
        "weather_json": json.dumps(match.weather, ensure_ascii=False),
        "source": match.source,
    }


def _save_to_db(result: CrawlResult):
    """将爬取结果写入 SQLite。"""
    conn = get_db()
    try:
        matches_valid, _ = validate_matches(result.matches)
        for m in matches_valid:
            row = _model_to_row_dict(m)
            conn.execute("""
                INSERT OR REPLACE INTO matches
                (match_id, date, home, away, venue, status, home_score, away_score,
                 events_json, home_lineup_json, away_lineup_json, stats_json,
                 referee, attendance, weather_json, source, updated_at)
                VALUES (:match_id, :date, :home, :away, :venue, :status, :home_score, :away_score,
                        :events_json, :home_lineup_json, :away_lineup_json, :stats_json,
                        :referee, :attendance, :weather_json, :source, datetime('now'))
            """, row)

        standings_valid, _ = validate_standings(result.standings)
        for s in standings_valid:
            conn.execute("""
                INSERT OR REPLACE INTO standings
                (team, group_name, played, won, drawn, lost, goals_for, goals_against,
                 goal_diff, points, rank, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (s.team, s.group, s.played, s.won, s.drawn, s.lost,
                  s.goals_for, s.goals_against, s.goal_diff, s.points, s.rank))

        injuries_valid, _ = validate_injuries(result.injuries)
        for i in injuries_valid:
            conn.execute("""
                INSERT INTO injuries (team, player, injury_type, severity, expected_return, source, reported_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (i.team, i.player, i.injury_type, i.severity, i.expected_return, i.source))

        conn.execute("""
            INSERT INTO crawl_log (source, fetched_at, matches_count, standings_count, injuries_count, success)
            VALUES (?, datetime('now'), ?, ?, ?, 1)
        """, (result.source, len(matches_valid), len(standings_valid), len(injuries_valid)))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _write_json_cache(result: CrawlResult, today: str):
    """写 JSON 缓存文件，保持向下兼容。"""
    match_dir = BASE_DIR / "data" / "matches"
    match_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "date": today,
        "matches": result.matches,
        "source": result.source,
        "injuries": result.injuries,
        "standings": result.standings,
        "weather": {},
        "errors": result.errors,
    }
    path = match_dir / f"matches_{today}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json_cache() -> dict | None:
    """加载最近日期的 JSON 缓存作为降级数据。"""
    match_dir = BASE_DIR / "data" / "matches"
    if not match_dir.exists():
        return None
    files = sorted(match_dir.glob("matches_*.json"), reverse=True)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("matches") or data.get("injuries"):
                return data
        except (json.JSONDecodeError, KeyError):
            continue
    return None


def _build_result(result: CrawlResult, today: str) -> dict:
    """将 CrawlResult 转为 API 响应格式。"""
    return {
        "date": today,
        "matches": result.matches,
        "source": result.source,
        "injuries": result.injuries,
        "standings": result.standings,
        "errors": result.errors,
        "weather": {},
    }


async def _do_crawl() -> CrawlResult:
    """异步爬取核心逻辑。"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        crawler = DongqiudiCrawler(client)
        return await crawler.crawl()


async def fetch_match_info_async() -> dict:
    """异步版爬取入口：供调度器使用。"""
    today = date.today().isoformat()

    if circuit_breaker.is_open("dongqiudi"):
        cached = _load_json_cache()
        if cached:
            cached["source"] = "缓存（爬取下线）"
            return cached
        return {"date": today, "matches": [], "source": "不可用", "injuries": [], "weather": {}}

    try:
        result = await _do_crawl()
        circuit_breaker.record_success("dongqiudi")
    except Exception as e:
        circuit_breaker.record_failure("dongqiudi")
        cached = _load_json_cache()
        if cached:
            cached["source"] = f"缓存（爬取失败: {e}）"
            return cached
        return {"date": today, "matches": [], "source": f"爬取失败: {e}", "injuries": [], "weather": {}}

    if not result:
        cached = _load_json_cache()
        return cached or {"date": today, "matches": [], "source": "无数据", "injuries": [], "weather": {}}

    try:
        _save_to_db(result)
    except Exception:
        pass

    _write_json_cache(result, today)
    return _build_result(result, today)


def fetch_match_info() -> dict:
    """同步版爬取入口：供路由处理器使用（保持向下兼容）。"""
    import asyncio
    return asyncio.run(fetch_match_info_async())
