FROM python:3.11-slim

WORKDIR /app

# System deps for lxml
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc build-essential libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python package
COPY pyproject.toml README.md LICENSE uv.lock ./
COPY src ./src
RUN uv pip install --system --no-cache ".[worker]"

ENV MCP_MODE=streamable_http
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Railway sets PORT automatically
CMD ["sh", "-c", "czechmedmcp run --mode streamable_http --host 0.0.0.0 --port ${PORT}"]
