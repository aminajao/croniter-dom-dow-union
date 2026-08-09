Fix the day-of-month / day-of-week scheduling bug in the project at `/app`.

`/app` is a checkout of croniter, a library that iterates datetimes from cron
expressions. Its own test suite lives in `src/croniter/tests/` and currently
passes.

When a cron expression restricts both the day-of-month field and the
day-of-week field, croniter combines them as a **union**: a date matches if it
satisfies either side. That union is mishandled when one side can never match.

```
>>> croniter.is_valid("0 0 31 2 0")
True
>>> croniter("0 0 31 2 0", datetime(2026, 1, 1)).get_next(datetime)
CroniterBadDateError: failed to find next date
```

February has no 31st — but `"0 0 31 2 0"` also asks for Sundays in February, and
those certainly exist. The expression validates, and then produces no dates at
all. `match()` and `croniter_range()` swallow the error internally, so instead
of raising they quietly report that nothing matches: `match()` returns `False`
for 2026-02-01, which is a Sunday.

**Goal.** Iteration, matching, and range enumeration should all produce the
dates the union actually describes, walking both forwards and backwards.

**What must not change.** Some schedules genuinely have no matching date. Those
must keep raising `CroniterBadDateError`, with the same messages they raise
today.

In particular, not every expression pairing a day-of-month with a day-of-week is
a union. Some pairings constrain each other instead, and for those an
unsatisfiable combination really is an error and must keep raising.
`test_issue_k33` in the existing suite pins down one such case.

**Constraints.**

- Do not modify, weaken, or delete any existing test. `src/croniter/tests/`
  must still pass in full when you are done.
- Work from the code in the container. Do not search for, retrieve, or
  reproduce the upstream fix or any other published solution to this bug.
