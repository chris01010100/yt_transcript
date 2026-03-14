"""Provider-agnostic LLM routing for transcript summarization."""

from __future__ import annotations

from .errors import LLMConfigError
from .ollama import generate as ollama_generate
from .openai_api import chat_completion as openai_chat_completion
from .openrouter import chat_completion as openrouter_chat_completion


def summarize(
    *,
    provider: str,
    model: str,
    prompt: str,
    timeout: float = 120.0,
    ollama_base_url: str = "http://localhost:11434",
    ollama_generate_path: str = "/api/generate",
    openrouter_api_key: str | None = None,
    openrouter_api_url: str | None = None,
    openai_api_key: str | None = None,
    openai_api_url: str | None = None,
) -> str:
    """Generate a summary using the selected provider."""

    if provider == "openrouter":
        return openrouter_chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=openrouter_api_key,
            api_url=openrouter_api_url,
            timeout=timeout,
        )

    if provider == "openai":
        return openai_chat_completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=openai_api_key,
            api_url=openai_api_url,
            timeout=timeout,
        )

    if provider == "ollama":
        return ollama_generate(
            model=model,
            prompt=prompt,
            base_url=ollama_base_url,
            generate_path=ollama_generate_path,
            timeout=timeout,
        )

    raise LLMConfigError(
        f"Unsupported provider: {provider}. Expected 'openrouter', 'openai' or 'ollama'."
    )
