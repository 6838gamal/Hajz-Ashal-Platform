# Multi-stage build, as decided in docs/architecture/06-folder-structure-and-deployment.md
FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

FROM base AS runtime
COPY . .
EXPOSE ${PORT:-8000}
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
