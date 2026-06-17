import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def load_skill_text() -> str:
    """读取 skill.md 全文作为静态 system prompt 主体。"""
    skill_path = BASE_DIR / "skill.md"
    if not skill_path.exists():
        return "# skill.md 未找到，请确认文件位置"
    return skill_path.read_text(encoding="utf-8")


def load_daily_info() -> str:
    """读取 data/daily_info.json 拼接为动态情报块。"""
    daily_path = BASE_DIR / "data" / "daily_info.json"
    if not daily_path.exists():
        return ""
    try:
        data = json.loads(daily_path.read_text(encoding="utf-8"))
        info_lines = data.get("info", [])
        date_str = data.get("date", "未知日期")
        if not info_lines:
            return ""
        lines = [f"**情报日期：{date_str}**"]
        lines.extend(f"- {line}" for line in info_lines)
        return "\n".join(lines)
    except (json.JSONDecodeError, KeyError):
        return ""


def build_system_prompt() -> str:
    """拼接完整 system prompt = skill.md + 动态情报覆盖。"""
    skill = load_skill_text()
    daily = load_daily_info()

    if daily:
        # 替换 skill.md §六的内容（从"## 六、最新情报"到文件尾）
        marker = "## 六、最新情报"
        if marker in skill:
            before = skill.split(marker)[0]
            skill = before + f"## 六、最新情报\n\n{daily}\n"
        else:
            skill += f"\n\n## 六、最新情报\n\n{daily}\n"

    return skill
