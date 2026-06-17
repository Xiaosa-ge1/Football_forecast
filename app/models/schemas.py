from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ── 预测相关 ──

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


# ── 比赛详情 ──

class MatchEvent(BaseModel):
    minute: int
    type: str                # goal / yellow_card / red_card / substitution / penalty
    team: str                # home / away
    player: str
    description: str = ""    # e.g. "梅西 点球破门"
    extra: str = ""          # assist, VAR 备注等


class MatchStats(BaseModel):
    possession: str = ""           # "52%-48%"
    shots: tuple[int, int] = (0, 0)
    shots_on_target: tuple[int, int] = (0, 0)
    corners: tuple[int, int] = (0, 0)
    fouls: tuple[int, int] = (0, 0)
    yellow_cards: tuple[int, int] = (0, 0)
    red_cards: tuple[int, int] = (0, 0)
    offsides: tuple[int, int] = (0, 0)
    passes: tuple[int, int] = (0, 0)


class MatchDetail(BaseModel):
    match_id: str = ""       # "2026-06-17_MEX_RSA"
    date: str = ""
    home: str = ""
    away: str = ""
    venue: str = ""
    status: str = "未开始"   # 未开始 / 进行中 / 已结束 / 延期
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    events: list[MatchEvent] = []
    home_lineup: list[str] = []
    away_lineup: list[str] = []
    stats: Optional[MatchStats] = None
    referee: str = ""
    attendance: str = ""
    weather: dict = {}
    source: str = ""


# ── 积分榜 ──

class StandingEntry(BaseModel):
    team: str
    group: str               # A-L
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_diff: int = 0
    points: int = 0
    rank: int = 0


# ── 伤停信息 ──

class InjuryReport(BaseModel):
    team: str
    player: str
    injury_type: str = ""    # e.g. "肌肉拉伤"
    severity: str = ""       # 轻 / 中 / 重 / 赛季报销
    expected_return: str = ""
    source: str = ""
    reported_at: str = ""


# ── 爬取状态 ──

class CrawlStatus(BaseModel):
    last_success: str = ""
    last_attempt: str = ""
    sources_used: list[str] = []
    matches_found: int = 0
    standings_found: int = 0
    injuries_found: int = 0
    errors: list[str] = []
    next_scheduled: str = ""
