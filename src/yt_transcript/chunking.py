"""Text-based chunking utilities for long transcript summarization."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ChunkingError


@dataclass(frozen=True)
class TextChunk:
    index: int
    start_char: int
    end_char: int
    text: str


def _find_split_index(text: str, start: int, target_end: int, lookback_chars: int = 500) -> int:
    """Find a natural split point near target_end.

    Preference order:
    1) sentence boundaries
    2) paragraph boundaries
    3) newline boundaries
    4) whitespace
    5) hard cut at target_end
    """

    if target_end >= len(text):
        return len(text)

    window_start = max(start + 1, target_end - lookback_chars)
    window = text[window_start:target_end]

    sentence_marks = [". ", "! ", "? ", "… ", ".\n", "!\n", "?\n", "…\n"]
    for mark in sentence_marks:
        idx = window.rfind(mark)
        if idx != -1:
            return window_start + idx + len(mark)

    idx = window.rfind("\n\n")
    if idx != -1:
        return window_start + idx + 2

    idx = window.rfind("\n")
    if idx != -1:
        return window_start + idx + 1

    idx = window.rfind(" ")
    if idx != -1:
        return window_start + idx + 1

    return target_end


def build_text_chunks(
    text: str,
    *,
    max_chars: int,
    overlap_chars: int,
    max_chunks: int = 0,
) -> list[TextChunk]:
    """Build overlapping text chunks from plain text.

    Args:
        text: Full source text.
        max_chars: Max characters per chunk.
        overlap_chars: Character overlap between consecutive chunks.
        max_chunks: Optional safety limit. 0 = unlimited.
    """

    if max_chars <= 0:
        raise ChunkingError("--chunk-max-chars must be > 0")

    if overlap_chars < 0:
        raise ChunkingError("--chunk-overlap-chars must be >= 0")

    if overlap_chars >= max_chars:
        raise ChunkingError("--chunk-overlap-chars must be smaller than --chunk-max-chars")

    if max_chunks < 0:
        raise ChunkingError("--chunk-max-chunks must be >= 0")

    stripped = text.strip()
    if not stripped:
        raise ChunkingError("Cannot chunk empty transcript text")

    chunks: list[TextChunk] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        if max_chunks and len(chunks) >= max_chunks:
            break

        target_end = min(start + max_chars, text_len)
        end = _find_split_index(text, start, target_end)

        if end <= start:
            end = target_end
            if end <= start:
                break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    start_char=start,
                    end_char=end,
                    text=chunk_text,
                )
            )

        if end >= text_len:
            break

        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start

    if not chunks:
        raise ChunkingError("Failed to produce chunks from transcript text")

    return chunks
