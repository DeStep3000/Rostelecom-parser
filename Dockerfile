# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable


FROM python:3.12-slim

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 1000 parser \
    && mkdir /app/output \
    && chown parser:parser /app/output

COPY --from=builder --chown=parser:parser /app/.venv /app/.venv

USER parser

ENTRYPOINT ["rialcom-parser"]
CMD ["--output", "/app/output/rialcom_tariffs.xlsx"]
