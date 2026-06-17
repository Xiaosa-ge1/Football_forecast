import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.templates import render
from app.crawler.match_crawler import fetch_match_info
from app.crawler.scheduler import scheduler
from app.models.schemas import CrawlRequest
from app.database import get_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
router = APIRouter()


def _load_matches() -> list[dict]:
    """从 data/matches/ 加载所有比赛信息（JSON 缓存，向下兼容）。"""
    match_dir = BASE_DIR / "data" / "matches"
    if not match_dir.exists():
        return []
    records = []
    for f in sorted(match_dir.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return records


def _load_matches_from_db() -> list[dict]:
    """从 SQLite 读取比赛列表。"""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM matches ORDER BY date DESC, match_id"
        ).fetchall()
        matches = []
        for r in rows:
            m = dict(r)
            m["events"] = json.loads(m.pop("events_json", "[]"))
            m["home_lineup"] = json.loads(m.pop("home_lineup_json", "[]"))
            m["away_lineup"] = json.loads(m.pop("away_lineup_json", "[]"))
            m["stats"] = json.loads(m.pop("stats_json", "{}"))
            m["weather"] = json.loads(m.pop("weather_json", "{}"))
            matches.append(m)
        return matches
    finally:
        conn.close()


# ── 页面 ──

@router.get("/matches", response_class=HTMLResponse)
async def matches_page(request: Request):
    matches = _load_matches()
    return render("matches.html", request, matches=matches)


# ── 爬取 API ──

@router.post("/api/crawl")
async def api_crawl(req: CrawlRequest):
    """手动触发爬取。"""
    try:
        result = fetch_match_info()
        return JSONResponse(content={"success": True, "data": result})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


# ── 比赛列表 API ──

@router.get("/api/matches")
async def api_matches():
    """返回比赛列表（SQLite 优先，JSON 缓存降级）。"""
    db_matches = _load_matches_from_db()
    if db_matches:
        return JSONResponse(content=db_matches)
    return JSONResponse(content=_load_matches())


# ── 每日情报 API ──

@router.get("/api/daily-info")
async def api_daily_info():
    """返回 data/daily_info.json 内容。"""
    path = BASE_DIR / "data" / "daily_info.json"
    if not path.exists():
        return JSONResponse(content={"date": "", "info": []})
    data = json.loads(path.read_text(encoding="utf-8"))
    return JSONResponse(content=data)


# ── 积分榜 API ──

@router.get("/api/standings")
async def api_standings():
    """返回最新小组积分榜（从 SQLite）。"""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM standings
            WHERE updated_at = (SELECT MAX(updated_at) FROM standings)
            ORDER BY group_name, rank
        """).fetchall()
        return JSONResponse(content=[dict(r) for r in rows])
    finally:
        conn.close()


# ── 爬取状态 API ──

@router.get("/api/crawl/status")
async def api_crawl_status():
    """返回爬取健康状态。"""
    conn = get_db()
    try:
        last_log = conn.execute(
            "SELECT * FROM crawl_log ORDER BY fetched_at DESC LIMIT 1"
        ).fetchone()

        next_run = None
        job = scheduler.get_job("crawl_job")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()

        return JSONResponse(content={
            "last_crawl": dict(last_log) if last_log else None,
            "next_scheduled": next_run,
        })
    finally:
        conn.close()
