import json
from typing import Optional

try:
    import pandas as pd
    import numpy as np

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


def _parse_result(record: dict) -> Optional[dict]:
    """从预测记录中提取预测值 vs 实际结果。"""
    result = record.get("result")
    actual = record.get("actual_score")
    if not result or not actual:
        return None

    try:
        a_goals, b_goals = map(int, actual.split("-"))
    except (ValueError, AttributeError):
        return None

    prob_a = result.get("teamA", {}).get("winProb", 0)
    prob_draw = result.get("draw", 0)
    prob_b = result.get("teamB", {}).get("winProb", 0)

    # 实际结果：1 = A胜, 0 = 平, -1 = B胜
    if a_goals > b_goals:
        actual_outcome = "A胜"
        actual_prob = prob_a
    elif a_goals == b_goals:
        actual_outcome = "平"
        actual_prob = prob_draw
    else:
        actual_outcome = "B胜"
        actual_prob = prob_b

    # 预测结果
    if prob_a > prob_b and prob_a > prob_draw:
        predicted_outcome = "A胜"
    elif prob_b > prob_a and prob_b > prob_draw:
        predicted_outcome = "B胜"
    else:
        predicted_outcome = "平"

    return {
        "id": record.get("id"),
        "team_a": record.get("team_a"),
        "team_b": record.get("team_b"),
        "predicted_outcome": predicted_outcome,
        "actual_outcome": actual_outcome,
        "is_correct": predicted_outcome == actual_outcome,
        "prob_a": prob_a,
        "prob_draw": prob_draw,
        "prob_b": prob_b,
        "actual_prob": actual_prob,
        "actual_score": actual,
        "predicted_score": result.get("predictedScore"),
    }


def compute_stats(predictions: list[dict]) -> dict:
    """从预测记录列表计算统计指标。"""
    parsed = [_parse_result(p) for p in predictions]
    parsed = [p for p in parsed if p is not None]

    if not parsed:
        return {
            "total": 0,
            "correct": 0,
            "accuracy": 0,
            "brier_score": None,
            "by_outcome": {},
            "recent": [],
        }

    if _HAS_PANDAS:
        df = pd.DataFrame(parsed)
        total = len(df)
        correct = int(df["is_correct"].sum())
        accuracy = round(correct / total * 100, 1) if total > 0 else 0

        # Brier 分数
        brier = float(np.mean((df["actual_prob"] - 100) ** 2)) if total > 0 else None

        # 按结果类型统计
        by_outcome = {}
        for outcome in ["A胜", "平", "B胜"]:
            subset = df[df["actual_outcome"] == outcome]
            if len(subset) > 0:
                by_outcome[outcome] = {
                    "total": int(len(subset)),
                    "correct": int(subset["is_correct"].sum()),
                    "accuracy": round(int(subset["is_correct"].sum()) / len(subset) * 100, 1),
                }

        recent = df.tail(10).to_dict("records") if len(df) > 0 else []

    else:
        total = len(parsed)
        correct = sum(1 for p in parsed if p["is_correct"])
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        brier = None
        by_outcome = {}
        recent = parsed[-10:]

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "brier_score": brier,
        "by_outcome": by_outcome,
        "recent": recent,
    }
