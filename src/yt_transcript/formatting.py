from __future__ import annotations

import re
from datetime import timedelta


def format_timestamp(seconds: float, full: bool = False) -> str:
    """Format seconds as a timestamp.

    - full=False: MM:SS or H:MM:SS (if hours > 0)
    - full=True:  HH:MM:SS
    """

    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if full:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def transcript_to_markdown(transcript, *, full_timestamps: bool = False) -> str:
    """Convert youtube_transcript_api transcript list to markdown text."""

    lines: list[str] = []
    for entry in transcript:
        ts = format_timestamp(entry.start, full=full_timestamps)
        lines.append(f"[{ts}] {entry.text}")

    return "\n".join(lines) + "\n"


def sanitize_filename(value: str, *, max_length: int = 120) -> str:
    """Sanitize text for filesystem-safe markdown filenames."""

    # Replace separators and problematic characters.
    sanitized = re.sub(r"[\\/:*?\"<>|]", "-", value)
    # Normalize whitespace.
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    # Remove remaining control chars.
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", sanitized)
    # Avoid trailing dots/spaces (problematic on some filesystems).
    sanitized = sanitized.rstrip(" .")

    if not sanitized:
        sanitized = "untitled"

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip(" .")

    return sanitized
