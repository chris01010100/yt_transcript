from __future__ import annotations

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
