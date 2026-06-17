import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.templates import render
from app.routes import predict, crawl, feedback

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="绿茵神算 · 2026 世界杯预测系统")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

# 注册路由
app.include_router(predict.router)
app.include_router(crawl.router)
app.include_router(feedback.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render("index.html", request)


@app.on_event("startup")
async def startup():
    """确保 data 目录和关键 JSON 文件存在"""
    data_dir = BASE_DIR / "data"
    for sub in ["predictions", "matches"]:
        (data_dir / sub).mkdir(parents=True, exist_ok=True)

    daily_info_path = data_dir / "daily_info.json"
    if not daily_info_path.exists():
        daily_info_path.write_text(json.dumps({
            "date": "2026-06-11",
            "info": [
                "揭幕战今日打响：墨西哥 vs 南非（墨西哥城阿兹特克球场）",
                "明日（6/12）：加拿大 vs 波黑（多伦多）、美国 vs 巴拉圭（英格尔伍德）"
            ]
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    teams_path = data_dir / "teams.json"
    if not teams_path.exists():
        teams_path.write_text(json.dumps({"teams": []}, ensure_ascii=False, indent=2), encoding="utf-8")
