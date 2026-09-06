from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Bucket:
    start: date
    end: date


def local_date_at(instant: datetime, timezone: str) -> date:
    """Return the configured calendar date for an aware Polar timestamp."""
    if instant.tzinfo is None:
        raise ValueError("instant must include timezone information")
    return instant.astimezone(ZoneInfo(timezone)).date()


def day_bucket(value: date) -> Bucket:
    return Bucket(start=value, end=value + timedelta(days=1))


def week_bucket(value: date) -> Bucket:
    start = value - timedelta(days=value.weekday())
    return Bucket(start=start, end=start + timedelta(days=7))


def month_bucket(value: date) -> Bucket:
    start = value.replace(day=1)
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return Bucket(start=start, end=end)


def recent_day_buckets(end_date: date) -> list[Bucket]:
    """Return the 28 calendar-day buckets ending with ``end_date``."""
    first_date = end_date - timedelta(days=27)
    return [day_bucket(first_date + timedelta(days=offset)) for offset in range(28)]


def recent_week_buckets(end_date: date) -> list[Bucket]:
    """Return 26 ISO-week buckets ending with the week containing ``end_date``."""
    latest = week_bucket(end_date)
    first_start = latest.start - timedelta(weeks=25)
    return [
        Bucket(
            start=first_start + timedelta(weeks=offset),
            end=first_start + timedelta(weeks=offset + 1),
        )
        for offset in range(26)
    ]


def month_buckets(first_date: date, last_date: date) -> list[Bucket]:
    """Return every calendar-month bucket touching the inclusive input range."""
    if first_date > last_date:
        return []
    bucket = month_bucket(first_date)
    result: list[Bucket] = []
    while bucket.start <= last_date:
        result.append(bucket)
        bucket = month_bucket(bucket.end)
    return result
