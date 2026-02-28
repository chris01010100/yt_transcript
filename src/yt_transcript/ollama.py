"""Ollama API client (generate endpoint only)."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from .errors import LLMConfigError, LLMResponseFormatError, OllamaError


def _build_url(base_url: str, generate_path: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise LLMConfigError(
            f"Invalid --ollama-base-url: {base_url}. Expected http(s)://host[:port]"
        )

    if not generate_path.strip():
        raise LLMConfigError("--ollama-generate-path must not be empty")

    path = generate_path if generate_path.startswith("/") else f"/{generate_path}"
    return f"{base_url.rstrip('/')}{path}"


def generate(
    model: str,
    prompt: str,
    *,
    base_url: str = "http://localhost:11434",
    generate_path: str = "/api/generate",
    timeout: float = 120.0,
) -> str:
    """Generate text via Ollama's /api/generate endpoint."""

    url = _build_url(base_url, generate_path)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise OllamaError(f"Ollama request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaError(
            f"Ollama API error ({exc.response.status_code}) at {url}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise OllamaError(
            f"Ollama request failed ({url}). Is Ollama running and reachable? {exc}"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise LLMResponseFormatError("Ollama returned non-JSON response") from exc

    text = data.get("response")
    if not isinstance(text, str) or not text.strip():
        raise LLMResponseFormatError(
            "Unexpected Ollama response format: missing non-empty 'response' field"
        )

    return text
