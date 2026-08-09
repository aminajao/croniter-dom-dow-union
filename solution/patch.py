"""Reference fix, applied as an exact text replacement.

Restores union (OR) semantics for the day-of-month / day-of-week split in
croniter._calc_next: when only one side of the union is unsatisfiable, that
side contributes no dates and the other side must still be allowed to match.
Only when both sides fail is there genuinely no such date.

The guard matters. '#' (nth weekday of month) and 'W' (nearest weekday) are
carried by nth_weekday_of_month and self.nearest_weekday rather than by the
DAY/DOW fields, so blanking those fields does not isolate either half -- each
side remains an intersection. Swallowing a failure there would silently drop a
field from the schedule, so in that case the error is left to propagate.
"""

import pathlib
import sys

TARGET = pathlib.Path("/app/src/croniter/croniter.py")

OLD = '''                bak = expanded[DOW_FIELD]
                expanded[DOW_FIELD] = ["*"]
                t1 = self._calc(current, expanded, nth_weekday_of_month, is_prev)
                expanded[DOW_FIELD] = bak
                expanded[DAY_FIELD] = ["*"]

                t2 = self._calc(current, expanded, nth_weekday_of_month, is_prev)
'''

NEW = '''                # Under OR semantics an unsatisfiable side -- the 31st in a month
                # that has no 31st, say -- contributes no dates rather than ruling
                # out the expression, so the other side must still be able to
                # match. Only both sides failing means there is no such date.
                #
                # That only holds while each side is a clean operand. '#' and 'W'
                # are not carried by the DAY/DOW fields but by nth_weekday_of_month
                # and self.nearest_weekday, so blanking the fields above does not
                # remove them and each side stays an intersection. Swallowing a
                # failure there would drop the other field from the schedule
                # instead, so let it propagate.
                clean_split = not nth_weekday_of_month and not self.nearest_weekday

                bak = expanded[DOW_FIELD]
                expanded[DOW_FIELD] = ["*"]
                try:
                    t1 = self._calc(current, expanded, nth_weekday_of_month, is_prev)
                except CroniterBadDateError:
                    if not clean_split:
                        raise
                    t1 = None
                expanded[DOW_FIELD] = bak
                expanded[DAY_FIELD] = ["*"]

                try:
                    t2 = self._calc(current, expanded, nth_weekday_of_month, is_prev)
                except CroniterBadDateError:
                    if not clean_split:
                        raise
                    t2 = None

                if t1 is None:
                    if t2 is None:
                        raise CroniterBadDateError(
                            "failed to find prev date" if is_prev else "failed to find next date"
                        )
                    return t2
                if t2 is None:
                    return t1
'''


def main() -> int:
    source = TARGET.read_text()

    if OLD not in source:
        sys.stderr.write(f"anchor not found in {TARGET}; refusing to patch\n")
        return 1

    TARGET.write_text(source.replace(OLD, NEW, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
