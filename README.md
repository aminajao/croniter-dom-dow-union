# croniter day-of-month / day-of-week union — Harbor terminal task

The agent must restore union (OR) semantics for the day-of-month / day-of-week
split in [croniter](https://github.com/kiorky/croniter), so a schedule whose
day-of-month side can never match still yields the dates its day-of-week side
describes — without breaking the schedules that intersect the two fields
instead.

## Layout

| Path | Purpose |
| --- | --- |
| `instruction.md` | The brief. The only thing the agent sees. |
| `task.toml` | Metadata and config. Network is disabled at run time. |
| `environment/Dockerfile` | Builds the broken starting state. |
| `environment/croniter/` | Vendored croniter source, bug present as-is. |
| `solution/solve.sh` | Reference fix. Scores 1.0 under the oracle. |
| `tests/test_outputs.py` | Hidden tests. |

## Running this task

> **Two environment constraints.** Both come from `network_mode = "no-network"`.

**1. The Docker provider must be able to enforce egress control.** Harbor only
advertises that capability on Linux, or on a macOS Docker host whose VM kernel
has `CONFIG_NFT_FIB_INET`. Docker Desktop's LinuxKit kernel does not, and Harbor
will reject the task with:

```
ValueError: network_mode='no-network' is not supported by EnvironmentType.DOCKER
```

This gate fires at environment start, so it blocks the oracle run as well as
agent runs — nothing will build until it is resolved.

Any Linux host works. On macOS, [Colima](https://github.com/abiosoft/colima)
works where Docker Desktop does not:

```bash
colima start --cpu 4 --memory 8 --disk 60
```

If a reviewer would rather not switch Docker runtimes, changing
`[environment].network_mode` to `"public"` in `task.toml` removes both
constraints below and lets the task run anywhere. That is not the intended
configuration: the bug corresponds to a real upstream PR, so an agent with open
network access can look the fix up rather than solve it.

**2. Agents that install themselves at run time need hosts allowlisted.**
The environment has no egress by default, so an agent harness that fetches
itself will fail during setup. Grant only what the harness needs — notably
*not* `github.com`, since the upstream fix for this bug is public:

```bash
harbor run -p . --agent oracle

harbor run -p . --agent claude-code --model claude-opus-4-8 --n-attempts 5 \
  --n-concurrent 2 \
  --agent-setup-timeout-multiplier 3 \
  --allow-environment-host api.anthropic.com \
  --allow-environment-host downloads.claude.ai \
  --allow-environment-host deb.debian.org
```

`--n-concurrent 2` and the setup-timeout multiplier keep parallel trials from
starving each other while downloading the agent over a constrained network.

## Validation results

| Run | Result |
| --- | --- |
| `--agent oracle` | **1.0** |
| `claude-code` on `claude-opus-4-8`, 5 attempts | **3 of 5** (mean 0.600, no exceptions) |

Every failing trial across every measurement run failed on the same check: a fix
that restores the union but lets `W` schedules silently return a date instead of
raising. The laziest passing implementation — wrapping both halves of the union
in a bare `try/except` — was written by hand during development and fails four
of the hidden tests; most losing agent trials independently produced a variant
of exactly that fix.

## Upstream source and licensing

`environment/croniter/` is croniter at commit
[`70564f2e`](https://github.com/kiorky/croniter/commit/70564f2e3157927b77d396998194fba733f410da),
the parent of the commit that fixed this bug, so the bug is present naturally —
nothing is patched in. Upstream is MIT licensed and `LICENSE` is retained in the
vendored tree. The reference fix corresponds to upstream
[PR #243](https://github.com/kiorky/croniter/pull/243).

Packaging, CI and container files from the upstream repo were dropped. The
library source and its own test suite are kept: that suite (220 tests) passes in
the broken starting state, so it gives nothing away, and the agent can use it to
check for regressions.
