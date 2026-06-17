"""APScheduler 定时任务：赛时密集爬取，非赛时低频率。"""

from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

TOURNAMENT_START = "2026-06-11"
TOURNAMENT_END = "2026-07-19"

scheduler = AsyncIOScheduler()


def _is_during_tournament() -> bool:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return TOURNAMENT_START <= today <= TOURNAMENT_END


def _is_match_window() -> bool:
    """比赛窗口大致为北京时间 13:00-23:00（UTC+8 → UTC 05:00-15:00）。"""
    now_utc = datetime.now(timezone.utc)
    return 5 <= now_utc.hour <= 15


def _get_interval_minutes() -> int:
    if not _is_during_tournament():
        return 360  # 非赛时 6 小时一次
    return 15 if _is_match_window() else 60


async def crawl_job():
    """调度器执行的爬取任务。"""
    from app.crawler.match_crawler import fetch_match_info_async
    print(f"[CrawlJob] 开始定时爬取...")
    try:
        result = await fetch_match_info_async()
        print(f"[CrawlJob] 完成: {len(result.get('matches', []))} 场比赛, "
              f"来源: {result.get('source')}")
    except Exception as e:
        print(f"[CrawlJob] 失败: {e}")

    # 动态调整间隔
    new_interval = _get_interval_minutes()
    job = scheduler.get_job("crawl_job")
    if job and job.trigger.interval != new_interval:
        scheduler.reschedule_job("crawl_job", trigger=IntervalTrigger(minutes=new_interval))


def start_scheduler():
    interval = _get_interval_minutes()
    scheduler.add_job(
        crawl_job,
        trigger=IntervalTrigger(minutes=interval),
        id="crawl_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    print(f"[Scheduler] 已启动，间隔 {interval} 分钟")
