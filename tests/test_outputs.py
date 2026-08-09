"""Hidden tests for the day-of-month / day-of-week union task.

Adapted from the upstream regression suite for kiorky/croniter#243.

These tests are outcome-graded: they assert on the datetimes the schedule
produces and on whether an error is raised, never on how the fix was written.

Roughly half of them exist to fail a lazy implementation rather than to confirm
a correct one. Wrapping both halves of the union in a bare try/except -- the
obvious shortcut -- restores the headline case but silently drops a field from
schedules that use '#' or 'W', which the *_still_raises tests below catch.
"""

from datetime import datetime

import pytest

from croniter import CroniterBadDateError, croniter


def _next_days(expr, start, count):
    itr = croniter(expr, start)
    return [(d.year, d.month, d.day) for d in (itr.get_next(datetime) for _ in range(count))]


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("0 0 31 2 0", [(2026, 2, 1), (2026, 2, 8), (2026, 2, 15)]),
        ("0 0 30 2 0", [(2026, 2, 1), (2026, 2, 8), (2026, 2, 15)]),
        ("0 0 31 4 0", [(2026, 4, 5), (2026, 4, 12), (2026, 4, 19)]),
    ],
)
def test_unsatisfiable_day_of_month_still_yields_day_of_week_dates(expr, expected):
    """get_next walks the day-of-week side when the day-of-month side can never occur."""
    assert _next_days(expr, datetime(2026, 1, 1), 3) == expected


def test_unsatisfiable_day_of_month_walks_backwards_too():
    """get_prev has the same union behaviour as get_next."""
    itr = croniter("0 0 31 2 0", datetime(2026, 3, 1))
    got = [(d.year, d.month, d.day) for d in (itr.get_prev(datetime) for _ in range(3))]
    assert got == [(2026, 2, 22), (2026, 2, 15), (2026, 2, 8)]


def test_match_reports_day_of_week_hits():
    """match() answers on the day-of-week side instead of reporting no match at all."""
    assert croniter.match("0 0 31 2 0", datetime(2026, 2, 1)) is True
    assert croniter.match("0 0 31 2 0", datetime(2026, 2, 2)) is False


def test_croniter_range_spans_the_day_of_week_side():
    """croniter_range enumerates the union rather than coming back empty."""
    from croniter import croniter_range

    got = list(croniter_range(datetime(2026, 2, 1), datetime(2026, 2, 28), "0 0 31 2 0"))
    assert [(d.month, d.day) for d in got] == [(2, 1), (2, 8), (2, 15), (2, 22)]


# --- The schedules below must keep raising. -------------------------------
# Each one is a case where a blanket "ignore the failure" fix produces a date
# that the schedule does not actually describe.


@pytest.mark.parametrize("expr", ["0 0 31 2 *", "0 0 30 2 *"])
def test_unsatisfiable_day_of_month_alone_still_raises(expr):
    """With no day-of-week side to fall back on there is genuinely no such date."""
    with pytest.raises(CroniterBadDateError):
        croniter(expr, datetime(2026, 1, 1)).get_next(datetime)


@pytest.mark.parametrize(
    "expr",
    ["30 23 8-9 JAN MON-FRI#1", "0 0 1 2 fri#2", "0 0 15 * fri#2"],
)
def test_nth_weekday_with_restricted_day_of_month_still_raises(expr):
    """'#' schedules intersect the two fields, so an unsatisfiable pair is an error."""
    with pytest.raises(CroniterBadDateError):
        croniter(expr, datetime(2026, 1, 1)).get_next(datetime)


def test_nearest_weekday_with_restricted_day_of_week_still_raises():
    """'W' schedules likewise intersect, so they cannot silently drop a field."""
    with pytest.raises(CroniterBadDateError):
        croniter("0 0 31w 2 0", datetime(2026, 1, 1)).get_next(datetime)


def test_both_sides_unsatisfiable_reports_the_direction_searched():
    """When neither side can match, the existing directional error is still raised."""
    itr = croniter("0 0 31 2 0 0 2026", datetime(2027, 6, 1))
    with pytest.raises(CroniterBadDateError) as excinfo:
        itr.get_next(datetime)
    assert str(excinfo.value) == "failed to find next date"

    itr = croniter("0 0 31 2 0 0 2026", datetime(2025, 6, 1))
    with pytest.raises(CroniterBadDateError) as excinfo:
        itr.get_prev(datetime)
    assert str(excinfo.value) == "failed to find prev date"


def test_existing_schedules_are_unaffected():
    """Ordinary schedules, and the AND semantics of a restricted pair, still hold."""
    assert _next_days("0 0 * * 0", datetime(2026, 1, 1), 3) == [
        (2026, 1, 4),
        (2026, 1, 11),
        (2026, 1, 18),
    ]
    # Both fields restricted and both satisfiable: still a union, not an intersection.
    assert _next_days("0 0 1 1 0", datetime(2026, 1, 1), 3) == [
        (2026, 1, 4),
        (2026, 1, 11),
        (2026, 1, 18),
    ]
