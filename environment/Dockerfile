# Builds the broken starting state.
#
# task.toml sets network_mode = "no-network", so nothing can be downloaded at
# run time or at verify time. Every dependency the agent or the verifier needs
# must be installed here, at build time, and pinned.

FROM python:3.12-slim-bookworm

# curl and procps are not needed by the task itself, but agent harnesses
# routinely shell out to them and try to apt-get them at environment start,
# which fails under a restricted network policy. Baking them in keeps the
# environment usable without opening up egress to the Debian mirrors.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl procps \
    && rm -rf /var/lib/apt/lists/*

# Runtime dependency of the project under test, plus the verifier's test runner.
RUN pip install --no-cache-dir \
      python-dateutil==2.9.0.post0 \
      pytest==8.4.1 \
      pytest-json-ctrf==0.3.5

WORKDIR /app

# Vendored project source. The bug is present in this tree as-is; nothing is
# patched in here. The solution and the hidden tests are NOT copied into the
# image -- Harbor mounts those at /solution and /tests at run time.
COPY croniter/ /app/

ENV PYTHONPATH=/app/src
