from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Final

SECRETS_DIR: Final[Path] = Path.home() / ".yt_transcript"
SECRETS_PATH: Final[Path] = SECRETS_DIR / "secrets.json"


def _ensure_dir() -> None:
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_mode_600(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        # Best effort; do not crash UI if chmod is not possible in the runtime.
        pass


def _read_all_secrets() -> dict[str, str]:
    _ensure_dir()

    if not SECRETS_PATH.exists():
        _atomic_write_json(SECRETS_PATH, {})
        _ensure_mode_600(SECRETS_PATH)
        return {}

    try:
        raw: Any = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        _atomic_write_json(SECRETS_PATH, {})
        _ensure_mode_600(SECRETS_PATH)
        return {}

    if not isinstance(raw, dict):
        _atomic_write_json(SECRETS_PATH, {})
        _ensure_mode_600(SECRETS_PATH)
        return {}

    normalized: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key] = value

    if normalized != raw:
        _atomic_write_json(SECRETS_PATH, normalized)
        _ensure_mode_600(SECRETS_PATH)

    return normalized


def _atomic_write_json(path: Path, payload: dict[str, str]) -> None:
    _ensure_dir()
    fd, tmp_name = tempfile.mkstemp(prefix=".secrets.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        _ensure_mode_600(path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def get_api_key(provider: str) -> str | None:
    secrets = _read_all_secrets()
    key = secrets.get(provider, "").strip()
    return key or None


def set_api_key(provider: str, key: str) -> None:
    secrets = _read_all_secrets()
    normalized_provider = provider.strip()
    normalized_key = key.strip()

    if not normalized_provider:
        return

    if normalized_key:
        secrets[normalized_provider] = normalized_key
    else:
        secrets.pop(normalized_provider, None)

    _atomic_write_json(SECRETS_PATH, secrets)