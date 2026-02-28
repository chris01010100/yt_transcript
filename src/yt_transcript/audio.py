"""Audio download helpers (planned).

This module is intentionally a placeholder for a future yt-dlp integration.
"""

from __future__ import annotations


class AudioDownloadError(Exception):
    pass


def download_audio(*args, **kwargs):  # pragma: no cover
    """Download audio for a YouTube video.

    TODO: Implement using yt-dlp.
    """

    raise NotImplementedError("Audio download not implemented yet")


def cleanup_audio(*args, **kwargs):  # pragma: no cover
    """Cleanup temporary audio files.

    TODO: Implement.
    """

    raise NotImplementedError("Audio cleanup not implemented yet")
