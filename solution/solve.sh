#!/bin/bash
#
# Reference solution. Takes the environment from broken to passing.
# Run by the Oracle agent from /solution.

set -euo pipefail

python3 /solution/patch.py

# Fail loudly here rather than in the verifier if the patch did not take.
python3 - <<'PY'
from datetime import datetime

from croniter import croniter

got = [d.day for d in (lambda it: [it.get_next(datetime) for _ in range(3)])(
    croniter("0 0 31 2 0", datetime(2026, 1, 1))
)]
assert got == [1, 8, 15], got
PY
