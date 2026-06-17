import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.templating import _TemplateResponse
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = str(BASE_DIR / "web" / "templates")

# 国旗 emoji 映射（ISO alpha-2 → Unicode 国旗）
_FLAG_EMOJI = {
    "mx": "\U0001f1f2\U0001f1fd", "za": "\U0001f1ff\U0001f1e6",
    "kr": "\U0001f1f0\U0001f1f7", "cz": "\U0001f1e8\U0001f1ff",
    "ca": "\U0001f1e8\U0001f1e6", "ba": "\U0001f1e7\U0001f1e6",
    "qa": "\U0001f1f6\U0001f1e6", "ch": "\U0001f1e8\U0001f1ed",
    "br": "\U0001f1e7\U0001f1f7", "ma": "\U0001f1f2\U0001f1e6",
    "ht": "\U0001f1ed\U0001f1f9", "gb-sct": "\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "us": "\U0001f1fa\U0001f1f8", "py": "\U0001f1f5\U0001f1fe",
    "au": "\U0001f1e6\U0001f1fa", "tr": "\U0001f1f9\U0001f1f7",
    "de": "\U0001f1e9\U0001f1ea", "cw": "\U0001f1e8\U0001f1fc",
    "ci": "\U0001f1e8\U0001f1ee", "ec": "\U0001f1ea\U0001f1e8",
    "nl": "\U0001f1f3\U0001f1f1", "jp": "\U0001f1ef\U0001f1f5",
    "se": "\U0001f1f8\U0001f1ea", "tn": "\U0001f1f9\U0001f1f3",
    "be": "\U0001f1e7\U0001f1ea", "eg": "\U0001f1ea\U0001f1ec",
    "ir": "\U0001f1ee\U0001f1f7", "nz": "\U0001f1f3\U0001f1ff",
    "es": "\U0001f1ea\U0001f1f8", "cv": "\U0001f1e8\U0001f1fb",
    "sa": "\U0001f1f8\U0001f1e6", "uy": "\U0001f1fa\U0001f1fe",
    "fr": "\U0001f1eb\U0001f1f7", "sn": "\U0001f1f8\U0001f1f3",
    "iq": "\U0001f1ee\U0001f1f6", "no": "\U0001f1f3\U0001f1f4",
    "ar": "\U0001f1e6\U0001f1f7", "dz": "\U0001f1e9\U0001f1ff",
    "at": "\U0001f1e6\U0001f1f9", "jo": "\U0001f1ef\U0001f1f4",
    "pt": "\U0001f1f5\U0001f1f9", "cd": "\U0001f1e8\U0001f1e9",
    "uz": "\U0001f1fa\U0001f1ff", "co": "\U0001f1e8\U0001f1f4",
    "gb-eng": "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "hr": "\U0001f1ed\U0001f1f7", "gh": "\U0001f1ec\U0001f1ed",
    "pa": "\U0001f1f5\U0001f1e6",
}


def flag_emoji(code: str) -> str:
    """ISO alpha-2 国家代码 → Unicode 国旗 emoji。"""
    return _FLAG_EMOJI.get(code, "\U0001f3f3")


def flag_url(code: str, w: int = 40) -> str:
    """生成 flagcdn.com 国旗图片 URL。"""
    return f"https://flagcdn.com/w{w}/{code}.png"


def load_teams() -> list[dict]:
    """从 data/teams.json 加载球队列表。"""
    path = BASE_DIR / "data" / "teams.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("teams", [])
    except (json.JSONDecodeError, KeyError):
        return []


def get_groups() -> dict[str, list[dict]]:
    """按组别整理球队，返回 { 'A': [team, ...], ... }。"""
    groups: dict[str, list[dict]] = {}
    for t in load_teams():
        groups.setdefault(t["group"], []).append(t)
    return dict(sorted(groups.items()))


_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

_env.globals["flag_emoji"] = flag_emoji
_env.globals["flag_url"] = flag_url
_env.globals["load_teams"] = load_teams
_env.globals["get_groups"] = get_groups


def render(name: str, request: Request, **context):
    """渲染模板，返回 Starlette TemplateResponse。"""
    template = _env.get_template(name)
    context["request"] = request
    return _TemplateResponse(template, context)
