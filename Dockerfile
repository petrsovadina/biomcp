# -- Stage 1: Build landing page --
FROM node:22-alpine AS web-builder
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install --ignore-scripts
COPY apps/web/ ./
RUN npm run build

# -- Stage 2: Python MCP server --
FROM python:3.11-slim AS server

WORKDIR /app

# System deps for lxml + build
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc build-essential libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python package
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[worker]"

# Copy static landing page into /app/static
COPY --from=web-builder /app/web/out /app/static

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()" || exit 1

EXPOSE 8000

# Default: streamable_http for HTTPS deployment
ENV MCP_MODE=streamable_http
ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "biomcp run --mode ${MCP_MODE} --host 0.0.0.0 --port 8000"]
