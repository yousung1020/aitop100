# Multi-stage build with Astral uv for high-speed deployment
FROM ghcr.io/astral-sh/uv:latest AS uv_bin

FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary
COPY --from=uv_bin /uv /uvx /bin/

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PORT=8000

WORKDIR /app

# Install project dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip install --system -r pyproject.toml

# Copy project files
COPY app/ ./app/
COPY docs/ ./docs/

EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
