# 绿茵神算 · 2026 世界杯 AI 预测系统

## 项目简介

基于 `skill.md`（绿茵神算 system prompt）构建的完整 Web 预测系统。提供可视化预测界面、AI 预测引擎、数据爬取和反馈校准功能。

## 仓库结构

```
E:\worldcup2026-prediction-skill\
├── app/                          # Python 后端
│   ├── main.py                   # FastAPI 入口，路由注册，启动配置
│   ├── templates.py              # Jinja2 模板引擎封装
│   ├── routes/
│   │   ├── predict.py            # 预测页面 + API（POST /api/predict）
│   │   ├── crawl.py              # 赛况展示 + 爬取触发（POST /api/crawl）
│   │   └── feedback.py           # 反馈录入 + 统计（POST /api/feedback）
│   ├── engine/
│   │   ├── prompt_builder.py     # 拼接 system prompt（skill.md + daily_info）
│   │   └── predictor.py          # Mock/LLM 预测引擎
│   ├── crawler/
│   │   └── match_crawler.py      # 比赛/伤停数据爬取（原型模拟数据）
│   ├── analysis/
│   │   └── stats.py              # pandas 统计分析（准确率/Brier/分类统计）
│   └── models/
│       └── schemas.py            # Pydantic 数据模型
├── web/
│   ├── static/
│   │   ├── css/style.css         # 绿白清爽风格，响应式
│   │   └── js/app.js             # 全局交互
│   └── templates/
│       ├── base.html             # 导航骨架
│       ├── index.html            # 首页 + 12 组分组表
│       ├── predict.html          # 预测页：选队 → 结果卡片（概率条/比分/因素）
│       ├── matches.html          # 赛况页：比赛列表 + 每日情报
│       └── feedback.html         # 反馈页：比分录入 + 统计分析面板
├── data/                         # JSON 数据存储
│   ├── teams.json                # 48 队索引（名称/组别/档次）
│   ├── predictions/              # 预测记录（UUID.json）
│   ├── matches/                  # 比赛信息
│   └── daily_info.json           # 每日情报（动态覆盖 skill.md §六）
├── scripts/
│   └── update_daily.py           # 每日情报更新脚本（python scripts/update_daily.py）
├── skill.md                      # 核心 system prompt（48 队资料库/方法论/红线）
├── docs/TUTORIAL.md              # 零基础部署教程（面向国内用户）
├── CLAUDE.md                     # 本文件
├── requirements.txt
└── README.md
```

## 启动方式

```bash
cd E:\worldcup2026-prediction-skill
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 浏览器打开 http://localhost:8000
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USE_MOCK` | `true` | `true` 用档次模拟，`false` 调用真实 LLM |
| `LLM_API_KEY` | 空 | LLM API 密钥（DeepSeek / OpenAI） |
| `LLM_API_BASE` | `https://api.deepseek.com` | API 端点 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |

## 核心概念

- **预测引擎**：`prompt_builder.py` 读取 skill.md（静态）拼接 daily_info（动态）构造完整 system prompt → `predictor.py` 调用 LLM 返回结构化 JSON
- **Mock 模式**：默认启用，基于 4 档球队评分（夺冠热门/一线/二线/中游）+ 随机扰动生成合理预测，无需 API Key
- **输出格式**：严格遵循 skill.md §三 JSON Schema（胜平负概率/比分/置信度/关键因素/分析/球员）
- **红线**：禁止投注/赔率建议，输出裸 JSON

## 开发约定

- 修改 `skill.md` 需同时更新 `data/teams.json` 的球队索引
- 每日情报通过 `data/daily_info.json` 注入，格式为 `{"date":"YYYY-MM-DD","info":["..."]}`
- 所有 JSON 文件读写显式指定 `encoding="utf-8"`（Windows 默认 GBK 会导致乱码）
- 新增路由在 `app/routes/` 下创建，在 `app/main.py` 注册

## 关键链接

- Live Demo: http://worldcup.youliaoyun.com
- GitHub: https://github.com/TradingAi666/worldcup2026-prediction-skill
