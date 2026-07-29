# syntax=docker/dockerfile:1.6

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_HTTP_TIMEOUT=120 \
    PIP_DEFAULT_TIMEOUT=120

ARG PYPI_INDEX_URL=https://pypi.org/simple
ENV UV_DEFAULT_INDEX=${PYPI_INDEX_URL} \
    PIP_INDEX_URL=${PYPI_INDEX_URL}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir -U pip uv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv export --format requirements-txt --no-dev --frozen --no-emit-project \
    -o /tmp/requirements.txt \
    && python -m pip wheel --no-cache-dir -r /tmp/requirements.txt -w /wheels \
    && uv build --wheel --out-dir /wheels \
    && rm -f /tmp/requirements.txt

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 parser \
    && mkdir /app/output \
    && chown parser:parser /app/output

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

USER parser

ENTRYPOINT ["rialcom-parser"]
CMD ["--output", "/app/output/rialcom_tariffs.xlsx"]
