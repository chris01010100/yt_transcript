import json
import re
import urllib.parse
import urllib.request
from typing import Iterable

from youtube_transcript_api import (
    NoTranscriptFound as YTApiNoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from .errors import InvalidYouTubeUrl, NoTranscriptFound, TranscriptFetchError


_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def get_oembed_title(youtube_url: str) -> str | None:
    """Fetch the video title via YouTube's oEmbed endpoint.

    Returns None if the title cannot be fetched.

    Note: This does not require an API key.
    """

    endpoint = "https://www.youtube.com/oembed"
    query = urllib.parse.urlencode({"url": youtube_url, "format": "json"})
    url = f"{endpoint}?{query}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        title = data.get("title")
        return title if isinstance(title, str) and title.strip() else None
    except Exception:  # noqa: BLE001
        return None


def get_video_publish_date(youtube_url: str) -> str | None:
    """Best-effort retrieval of the video's publish date as YYYY-MM-DD.

    This uses publicly available page metadata and does not require an API key.
    Returns None if no date can be extracted.
    """

    try:
        with urllib.request.urlopen(youtube_url, timeout=10) as resp:  # noqa: S310
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return None

    # Common metadata patterns found on YouTube pages.
    patterns = [
        r'"publishDate":"(\d{4}-\d{2}-\d{2})"',
        r'itemprop="datePublished"\s+content="(\d{4}-\d{2}-\d{2})"',
        r'property="og:video:release_date"\s+content="(\d{4}-\d{2}-\d{2})"',
        r'"dateText"\s*:\s*\{\s*"simpleText"\s*:\s*"(\d{4}-\d{2}-\d{2})"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)

    # Last fallback: pick first strict date occurrence.
    fallback = _DATE_RE.search(html)
    if fallback:
        return fallback.group(1)

    return None


def extract_video_id(url: str) -> str:
    """Extract the 11 character YouTube video id from common URL formats."""

    match = _VIDEO_ID_RE.search(url)
    if not match:
        raise InvalidYouTubeUrl("Could not extract video ID from URL")
    return match.group(1)


def fetch_transcript(video_id: str, languages: Iterable[str] = ("de", "en")):
    """Fetch a transcript for a video.

    Returns the transcript list as produced by youtube_transcript_api.
    """

    try:
        api = YouTubeTranscriptApi()
        return api.fetch(video_id, languages=list(languages))
    except (YTApiNoTranscriptFound, TranscriptsDisabled) as exc:
        raise NoTranscriptFound(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise TranscriptFetchError(str(exc)) from exc
