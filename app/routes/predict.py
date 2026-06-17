import json
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.templates import render, load_teams
from app.engine.predictor import predict
from app.models.schemas import PredictRequest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
router = APIRouter()


def _save_prediction(record: dict):
    """保存预测记录到 data/predictions/。"""
    pred_dir = BASE_DIR / "data" / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    record["_saved_at"] = date.today().isoformat()
    path = pred_dir / f"{record['id']}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/predict", response_class=HTMLResponse)
async def predict_page(request: Request):
    teams = load_teams()
    return render("predict.html", request, teams=teams)


@router.post("/api/predict")
async def api_predict(req: PredictRequest):
    result = predict(req.team_a, req.team_b)

    record = {
        "id": str(uuid.uuid4()),
        "team_a": req.team_a,
        "team_b": req.team_b,
        "match_date": req.match_date,
        "result": result,
    }
    _save_prediction(record)

    return JSONResponse(content=result)


@router.get("/api/predict/history")
async def predict_history():
    """返回所有历史预测记录。"""
    pred_dir = BASE_DIR / "data" / "predictions"
    if not pred_dir.exists():
        return JSONResponse(content=[])

    records = []
    for f in sorted(pred_dir.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return JSONResponse(content=records)


@router.get("/api/teams")
async def list_teams():
    """返回球队列表。"""
    return JSONResponse(content=load_teams())
