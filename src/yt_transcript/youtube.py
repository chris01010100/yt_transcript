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
