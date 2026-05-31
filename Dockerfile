# CanonIQ — local-first canonical mapping engine.
# Minimal image that installs the core package and exposes the CLI.
FROM python:3.12-slim AS base

# Avoid writing .pyc files and buffer-less stdout for clean container logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build metadata first to leverage layer caching.
COPY pyproject.toml README.md ./
COPY canoniq ./canoniq

# Install the core package (no optional extras by default).
RUN pip install --upgrade pip && pip install .

# Bundle the synthetic examples so `canoniq demo` works out of the box.
COPY examples ./examples

# Run as a non-root user.
RUN useradd --create-home --uid 10001 canoniq \
    && chown -R canoniq:canoniq /app
USER canoniq

ENTRYPOINT ["canoniq"]
CMD ["--help"]
