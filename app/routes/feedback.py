import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.templates import render
from app.models.schemas import FeedbackRequest
from app.analysis.stats import compute_stats

BASE_DIR = Path(__file__).resolve().parent.parent.parent
router = APIRouter()


def _load_predictions() -> list[dict]:
    pred_dir = BASE_DIR / "data" / "predictions"
    if not pred_dir.exists():
        return []
    records = []
    for f in sorted(pred_dir.glob("*.json"), reverse=True):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return records


def _save_feedback(prediction_id: str, team_a_goals: int, team_b_goals: int):
    """保存反馈到预测记录中。"""
    path = BASE_DIR / "data" / "predictions" / f"{prediction_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"预测记录 {prediction_id} 不存在")
    record = json.loads(path.read_text(encoding="utf-8"))
    record["actual_score"] = f"{team_a_goals}-{team_b_goals}"
    record["has_feedback"] = True
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


@router.get("/feedback", response_class=HTMLResponse)
async def feedback_page(request: Request):
    predictions = _load_predictions()
    stats = compute_stats(predictions)
    return render("feedback.html", request, predictions=predictions, stats=stats)


@router.post("/api/feedback")
async def api_feedback(req: FeedbackRequest):
    try:
        record = _save_feedback(req.prediction_id, req.team_a_goals, req.team_b_goals)
        return JSONResponse(content={"success": True, "record": record})
    except FileNotFoundError as e:
        return JSONResponse(status_code=404, content={"success": False, "error": str(e)})


@router.get("/api/feedback/stats")
async def api_feedback_stats():
    predictions = _load_predictions()
    stats = compute_stats(predictions)
    return JSONResponse(content=stats)
