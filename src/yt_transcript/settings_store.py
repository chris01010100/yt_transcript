from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Final

SETTINGS_DIR: Final[Path] = Path.home() / ".yt_transcript"
SETTINGS_PATH: Final[Path] = SETTINGS_DIR / "settings.json"

DEFAULT_SETTINGS: Final[dict[str, Any]] = {
    "llm_endpoint": "https://openrouter.ai/api/v1/chat/completions",
    "llm_model": "",
    "temperature": 0.2,
    "max_tokens": 1200,
}


def _ensure_dir() -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_settings(raw: Any) -> dict[str, Any]:
    merged = dict(DEFAULT_SETTINGS)

    if isinstance(raw, dict):
        if raw.get("llm_endpoint") is not None:
            merged["llm_endpoint"] = str(raw["llm_endpoint"])
        if raw.get("llm_model") is not None:
            merged["llm_model"] = str(raw["llm_model"])

        try:
            merged["temperature"] = float(raw.get("temperature", merged["temperature"]))
        except (TypeError, ValueError):
            merged["temperature"] = DEFAULT_SETTINGS["temperature"]

        try:
            merged["max_tokens"] = int(raw.get("max_tokens", merged["max_tokens"]))
        except (TypeError, ValueError):
            merged["max_tokens"] = DEFAULT_SETTINGS["max_tokens"]

    return merged


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _ensure_dir()
    fd, tmp_name = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def save_settings(settings: dict[str, Any]) -> None:
    normalized = _normalize_settings(settings)
    _atomic_write_json(SETTINGS_PATH, normalized)


def load_settings() -> dict[str, Any]:
    _ensure_dir()

    if not SETTINGS_PATH.exists():
        defaults = dict(DEFAULT_SETTINGS)
        save_settings(defaults)
        return defaults

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        defaults = dict(DEFAULT_SETTINGS)
        save_settings(defaults)
        return defaults

    normalized = _normalize_settings(data)

    if normalized != data:
        save_settings(normalized)

    return normalized