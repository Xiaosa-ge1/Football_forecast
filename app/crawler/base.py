import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.crawler.anti_crawl import get_headers


@dataclass
class CrawlResult:
    source: str
    fetched_at: str = ""
    matches: list[dict] = field(default_factory=list)
    standings: list[dict] = field(default_factory=list)
    injuries: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_seconds: int = 300):
        self.threshold = failure_threshold
        self.recovery = recovery_seconds
        self._failures: dict[str, list[float]] = {}

    def is_open(self, source: str) -> bool:
        timestamps = self._failures.get(source, [])
        now = time.time()
        recent = [t for t in timestamps if now - t < self.recovery]
        self._failures[source] = recent
        return len(recent) >= self.threshold

    def record_failure(self, source: str):
        self._failures.setdefault(source, []).append(time.time())

    def record_success(self, source: str):
        self._failures[source] = []


circuit_breaker = CircuitBreaker()


class BaseCrawler(ABC):
    """爬虫适配器基类。子类实现三个 fetch 方法即可接入。"""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def fetch_matches(self, target_date: str) -> list[dict]: ...

    @abstractmethod
    async def fetch_standings(self) -> list[dict]: ...

    @abstractmethod
    async def fetch_injuries(self) -> list[dict]: ...

    async def _get(self, url: str, max_retries: int = 3) -> str:
        """带重试的 HTTP GET 请求。"""
        for attempt in range(max_retries):
            try:
                resp = await self.client.get(
                    url, headers=get_headers(), timeout=15.0
                )
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503) and attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                    continue
                raise
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")
