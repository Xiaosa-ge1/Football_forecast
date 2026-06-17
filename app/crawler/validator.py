"""Pydantic 校验管道：将爬取的原始 dict 转为合法模型实例。"""

from pydantic import ValidationError

from app.models.schemas import MatchDetail, StandingEntry, InjuryReport


def validate_matches(raw_list: list[dict]) -> tuple[list[MatchDetail], list[str]]:
    """批量校验比赛详情，返回 (合法记录, 错误消息列表)。"""
    valid: list[MatchDetail] = []
    errors: list[str] = []
    for item in raw_list:
        try:
            valid.append(MatchDetail(**item))
        except ValidationError as e:
            errors.append(f"Match validation error ({item.get('home', '?')} vs {item.get('away', '?')}): {e}")
    return valid, errors


def validate_standings(raw_list: list[dict]) -> tuple[list[StandingEntry], list[str]]:
    valid: list[StandingEntry] = []
    errors: list[str] = []
    for item in raw_list:
        try:
            valid.append(StandingEntry(**item))
        except ValidationError as e:
            errors.append(f"Standing validation error ({item.get('team', '?')}): {e}")
    return valid, errors


def validate_injuries(raw_list: list[dict]) -> tuple[list[InjuryReport], list[str]]:
    valid: list[InjuryReport] = []
    errors: list[str] = []
    for item in raw_list:
        try:
            valid.append(InjuryReport(**item))
        except ValidationError as e:
            errors.append(f"Injury validation error ({item.get('player', '?')}): {e}")
    return valid, errors
