import json
import os
import random
from typing import Optional

from app.engine.prompt_builder import build_system_prompt

# 尝试导入 openai 库，如果不可用则使用 mock
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

# 从环境变量读取 API 配置
API_KEY = os.getenv("LLM_API_KEY", "")
API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


# ------ 简易 mock 引擎 ------

# 球队档次（用于 mock 生成合理预测）
_TEAM_TIERS = {
    "夺冠热门": ["阿根廷", "西班牙", "法国", "英格兰", "巴西"],
    "一线强队": ["德国", "葡萄牙", "荷兰", "乌拉圭", "克罗地亚", "摩洛哥", "哥伦比亚", "日本", "挪威"],
    "二线强队": ["美国", "墨西哥", "加拿大", "瑞士", "韩国", "土耳其", "瑞典", "奥地利",
                  "比利时", "塞内加尔", "厄瓜多尔", "埃及", "澳大利亚", "苏格兰"],
    "中游新军": ["捷克", "波黑", "卡塔尔", "巴拉圭", "科特迪瓦", "突尼斯", "伊朗", "新西兰",
                  "沙特", "阿尔及利亚", "加纳", "巴拿马", "伊拉克", "乌兹别克斯坦", "约旦",
                  "南非", "海地", "库拉索", "佛得角", "刚果金"],
}

_TIER_SCORE = {
    "夺冠热门": 85,
    "一线强队": 75,
    "二线强队": 60,
    "中游新军": 45,
}


def _get_tier(team: str) -> str:
    for tier, teams in _TEAM_TIERS.items():
        if team in teams:
            return tier
    return "中游新军"


def _mock_predict(team_a: str, team_b: str) -> dict:
    """基于球队档次的模拟预测，返回符合 skill.md 输出格式的 dict。"""
    tier_a = _TIER_SCORE[_get_tier(team_a)]
    tier_b = _TIER_SCORE[_get_tier(team_b)]

    # 基础概率计算
    total = tier_a + tier_b
    raw_win_a = round(tier_a / total * 70)  # 最高 70 左右
    raw_win_b = round(tier_b / total * 70)

    # 加入随机扰动
    noise_a = random.randint(-8, 8)
    noise_b = random.randint(-8, 8)

    prob_a = max(10, min(80, raw_win_a + noise_a))
    prob_b = max(10, min(80, raw_win_b + noise_b))

    # 平局概率
    draw = 100 - prob_a - prob_b
    if draw < 10:
        # 调整让平局不低于 10%
        overflow = 10 - draw
        if prob_a > prob_b:
            prob_a -= overflow // 2
            prob_b -= overflow - overflow // 2
        else:
            prob_b -= overflow // 2
            prob_a -= overflow - overflow // 2
        draw = 100 - prob_a - prob_b

    # 预测比分
    score_a = max(0, round((prob_a / 30) + random.uniform(-0.5, 1.0)))
    score_b = max(0, round((prob_b / 30) + random.uniform(-0.5, 1.0)))
    if score_a == 0 and score_b == 0:
        score_a = 1

    # confidence
    diff = abs(prob_a - prob_b)
    if diff > 25:
        confidence = "高"
    elif diff > 10:
        confidence = "中"
    else:
        confidence = "低"

    # keyFactors
    factors_pool = [
        f"{team_a}近期状态出色",
        f"{team_b}防守组织严密",
        f"{team_a}实力占优",
        f"{team_b}具备爆冷潜力",
        f"两队历史交手{team_a}占优",
        f"{team_b}关键球员缺阵风险",
        f"{team_a}中场控制力更强",
        f"本场淘汰赛压力相当",
        f"{team_a}大赛经验丰富",
        f"{team_b}年轻阵容冲击力强",
    ]
    selected = random.sample(factors_pool, 3)

    # playersToWatch
    watch_a = {"team": team_a, "player": "核心球员", "reason": "球队进攻组织核心"}
    watch_b = {"team": team_b, "player": "关键先生", "reason": "防守端支柱"}

    return {
        "teamA": {"name": team_a, "winProb": prob_a},
        "draw": draw,
        "teamB": {"name": team_b, "winProb": prob_b},
        "predictedScore": f"{score_a}-{score_b}",
        "confidence": confidence,
        "keyFactors": selected,
        "analysis": f"综合分析，{team_a}整体实力{'占优' if prob_a > prob_b else '稍逊'}"
                    f"，本场{'胜算较大' if prob_a > prob_b else '面临考验'}。"
                    f"{team_b}方面{'防守坚韧' if prob_b < 30 else '进攻火力不俗'}"
                    f"，预计比赛{'较为胶着' if draw > 20 else '分胜负概率较高'}"
                    f"。{team_a}需要警惕{team_b}的反击威胁。",
        "playersToWatch": [watch_a, watch_b],
    }


# ------ 真实 LLM 调用 ------

def _llm_predict(team_a: str, team_b: str, system_prompt: str) -> dict:
    """调用 LLM API 获取预测结果。"""
    if not _OPENAI_AVAILABLE:
        raise ImportError("openai 库未安装，请 pip install openai")

    client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请预测这场比赛：{team_a} vs {team_b}"},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    content = resp.choices[0].message.content.strip()
    # 移除可能的 markdown 代码块包裹
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0].strip()
    return json.loads(content)


# ------ 公开接口 ------

def predict(team_a: str, team_b: str) -> dict:
    """对外预测接口。USE_MOCK=true 时使用 mock，否则调用 LLM API。"""
    if USE_MOCK or not API_KEY:
        return _mock_predict(team_a, team_b)

    system_prompt = build_system_prompt()
    try:
        return _llm_predict(team_a, team_b, system_prompt)
    except Exception as e:
        # API 调用失败时 fallback 到 mock
        result = _mock_predict(team_a, team_b)
        result["_fallback"] = True
        result["_error"] = str(e)
        return result
