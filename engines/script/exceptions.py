"""Script engine exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import EngineError


class ScriptEngineError(EngineError):
    """Base exception for Script Engine contracts."""


class ScriptTemplateError(ScriptEngineError):
    """Raised when a script template contract is invalid."""


class ScriptRequestError(ScriptEngineError):
    """Raised when a script request contract is invalid."""


class ScriptResponseError(ScriptEngineError):
    """Raised when a script response contract is invalid."""
