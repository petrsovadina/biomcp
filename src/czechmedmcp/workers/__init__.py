"""Cloudflare Workers module for CzechMedMCP."""

from .worker import create_worker_app

__all__ = ["create_worker_app"]
