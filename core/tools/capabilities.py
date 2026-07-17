"""Typed capability model for the AI Company Tool Registry.

Capabilities represent WHAT a tool can do, decoupling
employee intent from specific tool implementations.
"""

from __future__ import annotations

from enum import StrEnum


class Capability(StrEnum):
    """Standard capability identifiers for tool discovery.

    Each value represents a generic action that one or more
    tools may provide. Employees request capabilities, not
    tool names.
    """

    SPEECH_GENERATION = "speech_generation"
    SPEECH_TO_TEXT = "speech_to_text"
    VOICE_CLONE = "voice_clone"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    VIDEO_GENERATION = "video_generation"
    VIDEO_EDITING = "video_editing"
    VIDEO_RENDERING = "video_rendering"
    BROWSER_NAVIGATION = "browser_navigation"
    BROWSER_AUTOMATION = "browser_automation"
    WEB_SEARCH = "web_search"
    REPOSITORY_MANAGEMENT = "repository_management"
    CODE_SEARCH = "code_search"
    CODE_EXECUTION = "code_execution"
    TRANSLATION = "translation"
    TRANSCRIPTION = "transcription"
    TEXT_GENERATION = "text_generation"
    DATABASE = "database"
    STORAGE = "storage"
    EMAIL = "email"
    CALENDAR = "calendar"
    SOCIAL_MEDIA = "social_media"
    DOCUMENT_GENERATION = "document_generation"
    AUDIO_PROCESSING = "audio_processing"
    AUDIO_EDITING = "audio_editing"
