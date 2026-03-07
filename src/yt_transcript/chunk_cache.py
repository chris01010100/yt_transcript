"""Chunk summary cache for resumable long-running summarization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .errors import ChunkCacheError


@dataclass(frozen=True)
class ChunkCacheItem:
    chunk_index: int
    start_char: int
    end_char: int
    text_sha256: str
    summary_md: str


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_run_id(
    *,
    video_id: str,
    provider: str,
    model: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    chunk_max_chunks: int,
    chunk_prompt_hash: str,
    final_prompt_hash: str,
) -> str:
    raw = "|".join(
        [
            video_id,
            provider,
            model,
            str(chunk_max_chars),
            str(chunk_overlap_chars),
            str(chunk_max_chunks),
            chunk_prompt_hash,
            final_prompt_hash,
        ]
    )
    return sha256_text(raw)[:16]


def ensure_cache_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ChunkCacheError(f"Could not create/use chunk cache directory '{path}': {exc}") from exc


def chunk_cache_file(cache_dir: Path, chunk_index: int) -> Path:
    return cache_dir / f"chunk_{chunk_index:04d}.json"


def load_chunk_summary(cache_dir: Path, chunk_index: int, expected_text_sha: str) -> str | None:
    file_path = chunk_cache_file(cache_dir, chunk_index)
    if not file_path.exists():
        return None

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ChunkCacheError(f"Could not read cache file '{file_path}': {exc}") from exc

    if payload.get("text_sha256") != expected_text_sha:
        return None

    summary = payload.get("summary_md")
    if not isinstance(summary, str) or not summary.strip():
        return None

    return summary


def save_chunk_summary(cache_dir: Path, item: ChunkCacheItem) -> None:
    file_path = chunk_cache_file(cache_dir, item.chunk_index)

    payload = {
        "chunk_index": item.chunk_index,
        "start_char": item.start_char,
        "end_char": item.end_char,
        "text_sha256": item.text_sha256,
        "summary_md": item.summary_md,
    }

    try:
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise ChunkCacheError(f"Could not write cache file '{file_path}': {exc}") from exc
