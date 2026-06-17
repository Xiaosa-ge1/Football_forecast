from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    team_a: str = Field(..., description="球队 A 名称")
    team_b: str = Field(..., description="球队 B 名称")
    match_date: str = Field("2026-06-11", description="比赛日期")


class PlayerWatch(BaseModel):
    team: str
    player: str
    reason: str


class PredictResponse(BaseModel):
    teamA: dict = Field(..., description='{"name": 队名, "winProb": 整数}')
    draw: int = Field(..., ge=0, le=100)
    teamB: dict = Field(..., description='{"name": 队名, "winProb": 整数}')
    predictedScore: str = Field(..., pattern=r"\d+-\d+")
    confidence: str = Field(..., pattern="^(高|中|低)$")
    keyFactors: list[str] = Field(..., min_length=3, max_length=5)
    analysis: str
    playersToWatch: list[PlayerWatch]


class FeedbackRequest(BaseModel):
    prediction_id: str
    team_a_goals: int = Field(..., ge=0)
    team_b_goals: int = Field(..., ge=0)


class CrawlRequest(BaseModel):
    source: Optional[str] = "auto"
