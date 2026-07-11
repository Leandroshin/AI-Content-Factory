"""Backward-compatible import for hosted Hotmart persistence."""

from core.integrations.hotmart.postgres import HotmartPostgresStore

__all__ = ["HotmartPostgresStore"]
