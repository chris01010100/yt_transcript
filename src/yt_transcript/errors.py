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


class LLMError(YTTranscriptError):
    """Base exception for LLM provider related failures."""


class OpenRouterError(LLMError):
    """Raised when the OpenRouter API request fails."""


class OpenAIError(LLMError):
    """Raised when the OpenAI API request fails."""


class OllamaError(LLMError):
    """Raised when an Ollama API request fails."""


class LLMConfigError(LLMError):
    """Raised when LLM provider configuration is invalid."""


class LLMResponseFormatError(LLMError):
    """Raised when an LLM provider returns an unexpected response format."""


class PromptFileNotFound(YTTranscriptError):
    """Raised when the prompt template file does not exist."""


class OutputDirectoryError(YTTranscriptError):
    """Raised when the output directory cannot be created or used."""


class OutputFileExistsError(YTTranscriptError):
    """Raised when an output file exists and overwrite is disabled."""


class OutputWriteError(YTTranscriptError):
    """Raised when writing output files fails."""


class ChunkingError(YTTranscriptError):
    """Raised when transcript chunking fails or chunk settings are invalid."""


class ChunkCacheError(YTTranscriptError):
    """Raised when reading/writing chunk cache fails."""
