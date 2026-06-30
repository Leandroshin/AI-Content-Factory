"""Exceptions for the logging subsystem."""


class LoggingError(Exception):
    """Base exception for logging issues."""


class LoggingConfigurationError(LoggingError):
    """Raised when logging configuration is invalid or incomplete."""