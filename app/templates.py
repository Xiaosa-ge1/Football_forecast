from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.templating import _TemplateResponse
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = str(BASE_DIR / "web" / "templates")

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def render(name: str, request: Request, **context):
    """渲染模板，返回 Starlette TemplateResponse。"""
    template = _env.get_template(name)
    context["request"] = request
    return _TemplateResponse(template, context)
