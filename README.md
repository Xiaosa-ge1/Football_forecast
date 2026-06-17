<div align="center">

# ⚽ 绿茵神算 · 2026 世界杯 AI 预测系统

### 基于 FastAPI 的全栈预测平台 — 可视化界面 + AI 引擎 + 实时数据爬取

[![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)
[![Teams](https://img.shields.io/badge/teams-48-9cf.svg)](#)

🔗 **Live Demo** · [worldcup.youliaoyun.com](http://worldcup.youliaoyun.com)

</div>

---

## 项目简介

绿茵神算是面向 2026 FIFA 世界杯的完整 Web 预测系统，提供：

- **可视化预测界面** — 选择任意两支球队，一键获取胜平负概率、预测比分、关键因素分析
- **AI 预测引擎** — 基于 `skill.md` 构造的 system prompt + LLM（DeepSeek/GPT/Claude），也可脱离 API 用 Mock 模式运行
- **比赛数据爬取** — 从懂球帝自动获取赛程、比分、积分榜、伤停信息
- **反馈校准系统** — 赛后录入真实比分，自动统计预测准确率

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 打开浏览器
# http://localhost:8000
```

无需 API Key 即可体验——默认 Mock 模式基于球队档位和随机扰动生成合理预测。

### 启用真实 LLM 预测

```bash
set USE_MOCK=false
set LLM_API_KEY=your-deepseek-key
set LLM_MODEL=deepseek-chat
```

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `USE_MOCK` | `true` | `true` 用档位模拟；`false` 调用真实 LLM |
| `LLM_API_KEY` | - | LLM API 密钥 |
| `LLM_API_BASE` | `https://api.deepseek.com` | API 端点 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |

## 页面功能

| 页面 | 路由 | 功能 |
|------|------|------|
| **首页** | `/` | 12 组完整分组表、球队索引 |
| **预测** | `/predict` | 选队 → 预测 → 结果卡片（概率条 / 比分 / 关键因素） |
| **赛况** | `/matches` | 比赛列表、每日情报、小组积分榜、爬取状态 |
| **反馈** | `/feedback` | 比分录入、预测准确率统计 |

## 项目结构

```
├── app/
│   ├── main.py                  # FastAPI 入口、路由注册、启动配置
│   ├── database.py              # SQLite 连接管理、建表
│   ├── templates.py             # Jinja2 模板引擎、国旗 emoji 映射
│   ├── routes/
│   │   ├── predict.py           # 预测页面 + POST /api/predict
│   │   ├── crawl.py             # 赛况展示 + 爬取触发 + 数据 API
│   │   └── feedback.py          # 反馈录入 + 统计
│   ├── engine/
│   │   ├── predictor.py         # Mock/LLM 预测引擎
│   │   └── prompt_builder.py    # skill.md + daily_info 拼接 system prompt
│   ├── crawler/
│   │   ├── match_crawler.py     # 爬取编排器
│   │   ├── scheduler.py         # APScheduler 定时任务
│   │   ├── base.py              # 爬虫抽象基类 + circuit breaker
│   │   ├── validator.py         # Pydantic 数据校验
│   │   ├── anti_crawl.py        # UA 轮换、反爬策略
│   │   └── sources/
│   │       └── dongqiudi.py     # 懂球帝适配器
│   ├── analysis/
│   │   └── stats.py             # pandas 准确率 / Brier / 分类统计
│   └── models/
│       └── schemas.py           # Pydantic 数据模型
├── web/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       ├── base.html            # 导航骨架
│       ├── index.html           # 首页
│       ├── predict.html         # 预测页
│       ├── matches.html         # 赛况页
│       └── feedback.html        # 反馈页
├── data/                        # JSON + SQLite 数据存储
├── scripts/
│   └── update_daily.py          # 每日情报更新脚本
├── skill.md                     # 核心 system prompt（48 队资料库）
├── requirements.txt
└── README.md
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器（Jinja2 渲染）                   │
├──────────┬──────────┬──────────┬───────────────────────┤
│  首页     │  预测页   │  赛况页   │  反馈页               │
│ 分组表    │ 预测卡片  │ 比赛+积分 │  统计面板             │
└────┬─────┴────┬─────┴────┬─────┴────┬──────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI 路由层                          │
│  /predict · /api/predict · /matches · /api/crawl         │
│  /api/standings · /api/daily-info · /api/feedback         │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  预测引擎     │ │  爬取模块     │ │  分析模块     │
│ Mock / LLM   │ │  懂球帝适配器  │ │  pandas 统计  │
│ prompt_      │ │  SQLite 存储  │ │  准确率计算   │
│ builder.py   │ │  APScheduler  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │
        ▼               ▼
┌──────────────────────────────────────┐
│           数据层                      │
│  SQLite (worldcup.db) + JSON 文件     │
│  data/matches/ · data/predictions/    │
└──────────────────────────────────────┘
```

### 预测引擎

`prompt_builder.py` 读取 `skill.md`（静态：48 队资料库 + 方法论 + 红线）拼接 `daily_info.json`（动态：每日伤停情报），构造完整 system prompt 输入 LLM。Mock 模式下跳过 API，基于球队 4 档评分 + 随机扰动生成预测。

### 爬取模块

定时（赛时 15 分钟 / 非赛时 6 小时）从懂球帝拉取比赛数据，写入 SQLite 并同步 JSON 缓存。爬取失败自动降级到上次缓存，circuit breaker 防止持续消耗。手动点击"刷新数据"按钮也可触发。

## 核心概念

- **skill.md** — 包含 48 队完整资料库（核心球员、教练、战术体系、隐忧）、4 维评估方法论、严格 JSON 输出契约、反赌红线。既是 LLM 的 system prompt，也是项目的"知识库"
- **Mock 模式** — 默认启用，基于球队档位排名 + 随机扰动生成合理预测，无需任何 API Key
- **每日情报** — `data/daily_info.json` 为动态注入位，覆盖 skill.md 第六节，实现"静态知识 + 动态更新"
- **输出格式** — 严格遵循 JSON Schema（胜平负概率 / 比分 / 置信度 / 关键因素 / 分析 / 关注球员）

## 数据维度

当前爬取模块采集以下数据：

| 维度 | 存储表 | 说明 |
|------|--------|------|
| 比赛赛程 | `matches` | 对阵、场地、开赛时间 |
| 比赛结果 | `matches` | 实时比分、进球事件时间线 |
| 技术统计 | `matches` (JSON) | 控球率、射门、黄红牌、角球 |
| 首发阵容 | `matches` (JSON) | 主/客队首发 11 人 |
| 小组积分榜 | `standings` | P/W/D/L/GF/GA/GD/Pts |
| 伤停信息 | `injuries` | 球员、伤情、预计恢复时间 |
| 每日情报 | `daily_info.json` | 文字摘要，注入 system prompt |

## API 端点

### 预测
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/predict` | 预测页面 |
| POST | `/api/predict` | 执行预测 `{"team_a":"墨西哥","team_b":"南非"}` |

### 比赛数据
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/matches` | 赛况页面 |
| GET | `/api/matches` | 比赛列表（JSON） |
| POST | `/api/crawl` | 手动触发爬取 |
| GET | `/api/standings` | 小组积分榜 |
| GET | `/api/daily-info` | 每日情报 |
| GET | `/api/crawl/status` | 爬取健康状态 |

### 反馈
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/feedback` | 反馈页面 |
| POST | `/api/feedback` | 提交比分反馈 |
| GET | `/api/feedback/stats` | 准确率统计 |

## 每日情报更新

```bash
# 手动更新
python scripts/update_daily.py --date 2026-06-17

# 爬取模块会自动更新 daily_info.json
# 定时任务在赛时每 15 分钟执行一次
```

## 兼容模型

| Provider | Model | 说明 |
|----------|-------|------|
| DeepSeek | `deepseek-chat` | 推荐：成本低、JSON 稳定 |
| OpenAI | `gpt-4o` | 高质量分析 |
| Anthropic | `claude-opus-4-7` | 需 tool_use 强制 JSON |
| 任意 OpenAI 兼容接口 | - | 设置 `LLM_API_BASE` 即可 |

## 开发约定

- 修改 `skill.md` 需同步更新 `data/teams.json` 的球队索引
- 所有 JSON 文件读写显式指定 `encoding="utf-8"`（Windows 默认 GBK 会乱码）
- 新增路由在 `app/routes/` 下创建，在 `app/main.py` 注册
- 爬取失败不抛异常——写日志 + 降级到缓存
- 不输出任何投注/赔率建议（skill.md 第五节红线）

## 声明

- 本系统仅供娱乐与球迷讨论
- 预测结果不构成任何参考依据
- 所有球队/球员信息均为公开资料
- 禁止用于投注、博彩、赔率业务

## License

[MIT](LICENSE) © 2026
