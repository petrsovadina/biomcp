---
color: blue
isContextNode: false
agent_name: Aki
status: claimed
---
# Core & Infrastructure

Základní vrstva: FastMCP singleton, HTTP klient s cache/retry/circuit breaker, konstanty, výjimky, rate limiter, connection pool, utils.

**Root path:** `src/czechmedmcp/` (top-level .py files) + `src/czechmedmcp/utils/`

**Key files:** core.py, constants.py, exceptions.py, http_client.py, auth.py, circuit_breaker.py, connection_pool.py, rate_limiter.py, retry.py, render.py, metrics.py

**Purpose:** Sdílená infrastruktura pro všechny doménové moduly — HTTP pipeline (cache → circuit breaker → retry → parse), FastMCP app singleton, Pydantic helpers, markdown rendering.

[[welcome_to_voicetree]]
