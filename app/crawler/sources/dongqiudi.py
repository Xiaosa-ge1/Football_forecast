"""懂球帝数据爬取适配器。

目标页面结构（可能会随网站更新变动）：
- 赛程: https://www.dongqiudi.com/data/{data_id}
- API: 懂球帝页面通常内嵌 __NEXT_DATA__ 或 data-* 属性中的 JSON
"""

import json
import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from app.crawler.base import BaseCrawler, CrawlResult
from app.crawler.anti_crawl import random_delay

# 懂球帝世界杯 2026 数据页面 ID（赛程/积分榜共用入口）
DONGQIUDI_BASE = "https://www.dongqiudi.com"
SCHEDULE_URL = f"{DONGQIUDI_BASE}/data"
STANDINGS_URL = f"{DONGQIUDI_BASE}/data/standings/worldcup-2026"

STATUS_MAP = {
    "finished": "已结束",
    "live": "进行中",
    "scheduled": "未开始",
    "postponed": "延期",
    "cancelled": "取消",
}


class DongqiudiCrawler(BaseCrawler):
    @property
    def source_name(self) -> str:
        return "dongqiudi"

    async def crawl(self) -> CrawlResult:
        """执行完整爬取流程，返回统一 CrawlResult。"""
        today = date.today().isoformat()
        result = CrawlResult(source=self.source_name)

        try:
            result.matches = await self.fetch_matches(today)
        except Exception as e:
            result.errors.append(f"Matches fetch failed: {e}")

        await random_delay(1.0, 2.0)

        try:
            result.standings = await self.fetch_standings()
        except Exception as e:
            result.errors.append(f"Standings fetch failed: {e}")

        await random_delay(1.0, 2.0)

        try:
            result.injuries = await self.fetch_injuries()
        except Exception as e:
            result.errors.append(f"Injuries fetch failed: {e}")

        return result

    # ── fetch_matches ──

    async def fetch_matches(self, target_date: str) -> list[dict]:
        """抓取指定日期的比赛数据。"""
        html = await self._get(SCHEDULE_URL)
        raw_matches = self._parse_embedded_json(html)
        if raw_matches:
            return self._normalize_matches(raw_matches, target_date)

        # 降级：尝试 HTML 表格解析
        raw_matches = self._parse_html_table(html)
        return self._normalize_matches(raw_matches, target_date)

    def _parse_embedded_json(self, html: str) -> list[dict]:
        """从页面内嵌 JSON 提取数据（__NEXT_DATA__ 或 window.__INITIAL_STATE__）。"""
        # 尝试 NEXT.js hydratation 数据
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                props = data.get("props", {}).get("pageProps", {})
                matches = props.get("matches") or props.get("matchList") or []
                if matches:
                    return matches
            except (json.JSONDecodeError, KeyError):
                pass

        # 尝试 window.__DATA__ 模式
        m = re.search(r'window\.__DATA__\s*=\s*({.*?});', html, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                return data.get("matches") or data.get("matchList") or []
            except (json.JSONDecodeError, KeyError):
                pass

        # 尝试任意 JSON-LD
        for tag in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                data = json.loads(tag)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                continue

        return []

    def _parse_html_table(self, html: str) -> list[dict]:
        """从 HTML 表格解析比赛数据（降级方案）。"""
        soup = BeautifulSoup(html, "lxml")
        matches = []

        # 尝试常见的比赛卡片/行 class
        for row in soup.select("[class*='match'], [class*='game'], tr[class*='match']"):
            try:
                home_el = row.select_one("[class*='home'] a, [class*='teamA'] a, .home-team")
                away_el = row.select_one("[class*='away'] a, [class*='teamB'] a, .away-team")
                score_el = row.select_one("[class*='score'], .match-score")
                time_el = row.select_one("[class*='time'], .match-time")
                venue_el = row.select_one("[class*='venue'], .location")

                if home_el and away_el:
                    match = {
                        "home": home_el.get_text(strip=True),
                        "away": away_el.get_text(strip=True),
                    }
                    if score_el:
                        parts = score_el.get_text(strip=True).replace(" ", "").split("-")
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            match["home_score"] = int(parts[0])
                            match["away_score"] = int(parts[1])
                    if time_el:
                        match["start_time"] = time_el.get_text(strip=True)
                    if venue_el:
                        match["venue"] = venue_el.get_text(strip=True)
                    matches.append(match)
            except Exception:
                continue

        return matches

    def _normalize_matches(self, raw: list[dict], target_date: str) -> list[dict]:
        """将懂球帝原始格式标准化为 MatchDetail 兼容 dict。"""
        result = []
        for item in raw:
            try:
                home = (item.get("home_team_name") or item.get("team_A_name")
                        or item.get("home") or item.get("team_A", ""))
                away = (item.get("away_team_name") or item.get("team_B_name")
                        or item.get("away") or item.get("team_B", ""))

                if not home or not away:
                    continue

                status_raw = item.get("status") or item.get("match_status", "scheduled")

                events = []
                for evt in item.get("events") or item.get("match_events") or []:
                    events.append({
                        "minute": evt.get("minute") or evt.get("time", 0),
                        "type": evt.get("type") or evt.get("event_type", ""),
                        "team": evt.get("team") or evt.get("side", ""),
                        "player": evt.get("player") or evt.get("player_name", ""),
                        "description": evt.get("description") or evt.get("text", ""),
                        "extra": evt.get("assist") or evt.get("extra", ""),
                    })

                home_lineup = item.get("home_lineup") or item.get("home_formation") or []
                away_lineup = item.get("away_lineup") or item.get("away_formation") or []

                stats_raw = item.get("stats") or item.get("match_stats") or {}
                stats = None
                if stats_raw:
                    stats = {
                        "possession": stats_raw.get("possession", ""),
                        "shots": (
                            stats_raw.get("home_shots", 0) or stats_raw.get("shots", [0, 0])[0],
                            stats_raw.get("away_shots", 0) or stats_raw.get("shots", [0, 0])[1],
                        ),
                        "shots_on_target": (
                            stats_raw.get("home_shots_on_target", 0),
                            stats_raw.get("away_shots_on_target", 0),
                        ),
                        "corners": (
                            stats_raw.get("home_corners", 0),
                            stats_raw.get("away_corners", 0),
                        ),
                        "fouls": (stats_raw.get("home_fouls", 0), stats_raw.get("away_fouls", 0)),
                        "yellow_cards": (stats_raw.get("home_yellow_cards", 0), stats_raw.get("away_yellow_cards", 0)),
                        "red_cards": (stats_raw.get("home_red_cards", 0), stats_raw.get("away_red_cards", 0)),
                        "offsides": (stats_raw.get("home_offsides", 0), stats_raw.get("away_offsides", 0)),
                        "passes": (stats_raw.get("home_passes", 0), stats_raw.get("away_passes", 0)),
                    }

                match_date = item.get("date") or item.get("match_date") or target_date
                match_id = f"{match_date}_{home}_{away}".replace(" ", "_")

                result.append({
                    "match_id": match_id,
                    "date": match_date,
                    "home": home,
                    "away": away,
                    "venue": item.get("venue") or item.get("stadium") or item.get("location", ""),
                    "status": STATUS_MAP.get(status_raw, status_raw),
                    "home_score": item.get("home_score"),
                    "away_score": item.get("away_score"),
                    "events": events,
                    "home_lineup": home_lineup if isinstance(home_lineup, list) else [],
                    "away_lineup": away_lineup if isinstance(away_lineup, list) else [],
                    "stats": stats,
                    "referee": item.get("referee") or item.get("referee_name", ""),
                    "attendance": str(item.get("attendance", "")),
                    "weather": item.get("weather") or {},
                    "source": self.source_name,
                })
            except Exception:
                continue
        return result

    # ── fetch_standings ──

    async def fetch_standings(self) -> list[dict]:
        """抓取小组积分榜。"""
        html = await self._get(STANDINGS_URL)
        raw = self._parse_embedded_json(html)

        if not raw:
            # 尝试直接获取 standings 子数据结构
            raw = self._parse_standings_html(html)

        return self._normalize_standings(raw)

    def _parse_standings_html(self, html: str) -> list[dict]:
        """从 HTML 解析积分榜表（降级）。"""
        soup = BeautifulSoup(html, "lxml")
        groups = []

        for table in soup.select("table[class*='standing'], table[class*='rank'], div[class*='standing'] table"):
            rows = table.select("tr")
            group_name = ""
            for row in rows:
                # 检测分组标题
                group_header = row.select_one("[class*='group'], th[colspan]")
                if group_header:
                    group_name = group_header.get_text(strip=True).replace("组", "").strip()
                    continue

                cells = row.select("td")
                if len(cells) >= 8:
                    try:
                        groups.append({
                            "team": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                            "group": group_name,
                            "played": int(cells[2].get_text(strip=True)) if len(cells) > 2 else 0,
                            "won": int(cells[3].get_text(strip=True)) if len(cells) > 3 else 0,
                            "drawn": int(cells[4].get_text(strip=True)) if len(cells) > 4 else 0,
                            "lost": int(cells[5].get_text(strip=True)) if len(cells) > 5 else 0,
                            "goals_for": int(cells[6].get_text(strip=True)) if len(cells) > 6 else 0,
                            "goals_against": int(cells[7].get_text(strip=True)) if len(cells) > 7 else 0,
                            "goal_diff": int(cells[8].get_text(strip=True)) if len(cells) > 8 else 0,
                            "points": int(cells[9].get_text(strip=True)) if len(cells) > 9 else 0,
                            "rank": 0,
                        })
                    except (ValueError, IndexError):
                        continue
        return groups

    def _normalize_standings(self, raw: list[dict]) -> list[dict]:
        """标准化积分榜数据。"""
        result = []
        for item in raw:
            try:
                team = item.get("team_name") or item.get("team") or item.get("name", "")
                if not team:
                    continue
                group = item.get("group") or item.get("group_name") or ""
                gd = item.get("goal_diff") or item.get("goals_diff", 0)
                if gd is None:
                    gf = item.get("goals_for") or item.get("goals_scored", 0) or 0
                    ga = item.get("goals_against") or item.get("goals_conceded", 0) or 0
                    gd = int(gf) - int(ga)

                result.append({
                    "team": team,
                    "group": group,
                    "played": int(item.get("played") or item.get("matches_played", 0) or 0),
                    "won": int(item.get("won") or item.get("wins", 0) or 0),
                    "drawn": int(item.get("drawn") or item.get("draws", 0) or 0),
                    "lost": int(item.get("lost") or item.get("losses", 0) or 0),
                    "goals_for": int(item.get("goals_for") or item.get("goals_scored", 0) or 0),
                    "goals_against": int(item.get("goals_against") or item.get("goals_conceded", 0) or 0),
                    "goal_diff": int(gd) if gd is not None else 0,
                    "points": int(item.get("points") or item.get("pts", 0) or 0),
                    "rank": int(item.get("rank") or item.get("position", 0) or 0),
                })
            except (ValueError, TypeError):
                continue
        return result

    # ── fetch_injuries ──

    async def fetch_injuries(self) -> list[dict]:
        """抓取伤停信息。懂球帝伤病板块通常位于球队页面子栏目。"""
        injuries = []
        # 尝试通过赛程页面的内嵌数据获取
        html = await self._get(SCHEDULE_URL)
        raw = self._parse_embedded_json(html)
        raw_injuries = raw.get("injuries") if isinstance(raw, dict) else []

        for item in raw_injuries:
            injuries.append({
                "team": item.get("team_name") or item.get("team", ""),
                "player": item.get("player_name") or item.get("player", ""),
                "injury_type": item.get("injury_type") or item.get("reason", ""),
                "severity": item.get("severity") or "中",
                "expected_return": item.get("return_date") or item.get("expected_return", ""),
                "source": self.source_name,
                "reported_at": item.get("reported_at") or item.get("update_time", ""),
            })

        return injuries
