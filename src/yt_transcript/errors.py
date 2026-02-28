"""Project specific exceptions.

Keeping our own exception hierarchy makes it easier to provide clean CLI errors
without leaking third-party library details.
"""


class YTTranscriptError(Exception):
    """Base exception for this project."""


class InvalidYouTubeUrl(YTTranscriptError):
    """Raised when a YouTube video ID cannot be extracted from a given URL."""


class NoTranscriptFound(YTTranscriptError):
    """Raised when no transcript is available in the requested languages."""


class TranscriptFetchError(YTTranscriptError):
    """Raised when a transcript could not be fetched for any other reason."""