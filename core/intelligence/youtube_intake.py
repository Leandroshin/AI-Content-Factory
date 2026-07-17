"""Zero-cost intake for YouTube sources awaiting transcript and evidence."""

from hashlib import sha256
import re
import time
from urllib.parse import parse_qs, urlparse

from core.intelligence.source_intake import PendingLearningSource, SourceIntakeStatus


_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}


class YouTubePendingSourceIntake:
    """Normalize a YouTube URL without fetching or interpreting its content."""

    BLOCKERS = (
        "transcript_or_verified_captions_missing",
        "timestamped_visual_evidence_missing",
        "claims_not_audited",
        "experiment_not_measured",
        "owner_knowledge_approval_missing",
    )

    def register(self, source_uri: str, *, submitted_at: float | None = None) -> PendingLearningSource:
        external_id = self.video_id(source_uri)
        canonical_uri = f"https://www.youtube.com/watch?v={external_id}"
        fingerprint = sha256(f"youtube:{external_id}".encode("utf-8")).hexdigest()
        return PendingLearningSource(
            intake_id=f"youtube-{fingerprint[:20]}",
            platform="youtube",
            source_uri=canonical_uri,
            external_id=external_id,
            submitted_at=time.time() if submitted_at is None else submitted_at,
            fingerprint=fingerprint,
            status=SourceIntakeStatus.PENDING_TRANSCRIPT,
            blockers=self.BLOCKERS,
        )

    @staticmethod
    def video_id(source_uri: str) -> str:
        if not isinstance(source_uri, str) or not source_uri.strip():
            raise ValueError("A YouTube source URL is required.")
        parsed = urlparse(source_uri.strip())
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise ValueError("YouTube source URL must be public HTTPS without credentials.")
        host = (parsed.hostname or "").lower()
        if host == "youtu.be":
            candidate = parsed.path.strip("/").split("/")[0]
        elif host in _YOUTUBE_HOSTS:
            if "list" in parse_qs(parsed.query):
                raise ValueError("Playlists are not accepted as a single learning source.")
            parts = [part for part in parsed.path.split("/") if part]
            if parsed.path == "/watch":
                candidate = parse_qs(parsed.query).get("v", [""])[0]
            elif len(parts) == 2 and parts[0] in {"shorts", "live"}:
                candidate = parts[1]
            else:
                candidate = ""
        else:
            raise ValueError("Only official YouTube hosts are accepted.")
        if not _VIDEO_ID.fullmatch(candidate):
            raise ValueError("A valid YouTube video ID is required.")
        return candidate

