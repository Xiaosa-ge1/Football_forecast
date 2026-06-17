import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.templates import render
from app.crawler.match_crawler import fetch_match_info
from app.models.schemas import CrawlRequest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
router = APIRouter()


def _load_matches() -> list[dict]:
    """从 data/matches/ 加载所有比赛信息。"""
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


@router.get("/matches", response_class=HTMLResponse)
async def matches_page(request: Request):
    matches = _load_matches()
    return render("matches.html", request, matches=matches)


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


@router.get("/api/matches")
async def api_matches():
    """返回已爬取的比赛信息列表。"""
    return JSONResponse(content=_load_matches())
