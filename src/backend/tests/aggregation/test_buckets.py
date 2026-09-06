from datetime import UTC, date, datetime

import pytest

from polar_app.aggregation.buckets import (
    day_bucket,
    local_date_at,
    month_bucket,
    month_buckets,
    recent_day_buckets,
    recent_week_buckets,
    week_bucket,
)


def test_day_week_and_month_buckets_use_calendar_boundaries() -> None:
    assert day_bucket(date(2026, 2, 28)).end == date(2026, 3, 1)
    assert week_bucket(date(2026, 1, 1)).start == date(2025, 12, 29)
    assert week_bucket(date(2026, 1, 1)).end == date(2026, 1, 5)
    assert month_bucket(date(2024, 2, 29)).end == date(2024, 3, 1)
    assert month_bucket(date(2026, 12, 12)).end == date(2027, 1, 1)


def test_local_date_conversion_handles_dst_boundaries() -> None:
    assert local_date_at(datetime(2026, 3, 29, 0, 30, tzinfo=UTC), "Europe/Berlin") == date(
        2026, 3, 29
    )
    assert local_date_at(datetime(2026, 3, 29, 22, 30, tzinfo=UTC), "Europe/Berlin") == date(
        2026, 3, 30
    )


def test_local_date_conversion_requires_an_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone"):
        local_date_at(datetime(2026, 3, 29, 0, 30), "Europe/Berlin")


def test_recent_ranges_have_the_required_contiguous_bucket_counts() -> None:
    days = recent_day_buckets(date(2026, 9, 4))
    weeks = recent_week_buckets(date(2026, 9, 4))

    assert len(days) == 28
    assert days[0].start == date(2026, 8, 8)
    assert days[-1].end == date(2026, 9, 5)
    assert len(weeks) == 26
    assert weeks[0].start == date(2026, 3, 9)
    assert weeks[-1].start == date(2026, 8, 31)
    assert all(
        current.end == following.start for current, following in zip(days, days[1:], strict=False)
    )
    assert all(
        current.end == following.start
        for current, following in zip(weeks, weeks[1:], strict=False)
    )


def test_month_buckets_cover_all_history_without_gaps() -> None:
    buckets = month_buckets(date(2025, 11, 18), date(2026, 2, 1))

    assert [(bucket.start, bucket.end) for bucket in buckets] == [
        (date(2025, 11, 1), date(2025, 12, 1)),
        (date(2025, 12, 1), date(2026, 1, 1)),
        (date(2026, 1, 1), date(2026, 2, 1)),
        (date(2026, 2, 1), date(2026, 3, 1)),
    ]
    assert month_buckets(date(2026, 2, 2), date(2026, 2, 1)) == []
