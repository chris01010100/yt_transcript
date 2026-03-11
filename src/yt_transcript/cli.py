from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import (
    ChunkCacheError,
    ChunkingError,
    InvalidYouTubeUrl,
    LLMConfigError,
    LLMError,
    NoTranscriptFound,
    OutputDirectoryError,
    OutputFileExistsError,
    OutputWriteError,
    PromptFileNotFound,
    TranscriptFetchError,
)
from .pipeline import PipelineConfig, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-transcript",
        description="Fetch a YouTube transcript and save it as a markdown file.",
    )

    parser.add_argument(
        "youtube_url",
        help="YouTube URL (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)",
    )

    parser.add_argument(
        "--hh",
        action="store_true",
        help="Always format timestamps as HH:MM:SS (instead of MM:SS / H:MM:SS).",
    )

    parser.add_argument(
        "--lang",
        action="append",
        dest="languages",
        default=None,
        help=(
            "Preferred transcript language (repeatable). Default: --lang de --lang en"
        ),
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for transcript and summary output files. Default: current directory.",
    )

    parser.add_argument(
        "--overwrite",
        choices=["yes", "no"],
        default="no",
        help="Whether existing output files may be overwritten. Default: no",
    )

    # LLM summarization options
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate a summary after fetching the transcript.",
    )

    parser.add_argument(
        "--provider",
        choices=["openrouter", "ollama"],
        default="openrouter",
        help="LLM provider for summarization. Default: openrouter",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Model ID for summarization (OpenRouter or Ollama). Required if --summarize is set.",
    )

    parser.add_argument(
        "--prompt-file",
        default="prompt.md",
        help="Path to the prompt template file. Default: prompt.md",
    )

    parser.add_argument(
        "--ollama-base-url",
        default="http://localhost:11434",
        help="Ollama base URL. Default: http://localhost:11434",
    )

    parser.add_argument(
        "--ollama-generate-path",
        default="/api/generate",
        help="Ollama generate endpoint path. Default: /api/generate",
    )

    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=120.0,
        help="LLM request timeout in seconds. Default: 120",
    )

    parser.add_argument(
        "--chunk-max-chars",
        type=int,
        default=8000,
        help="Max characters per chunk for map/reduce summarization. Default: 8000",
    )

    parser.add_argument(
        "--chunk-overlap-chars",
        type=int,
        default=1000,
        help="Character overlap between adjacent chunks. Default: 1000",
    )

    parser.add_argument(
        "--chunk-max-chunks",
        type=int,
        default=0,
        help="Safety limit for number of chunks. 0 means unlimited. Default: 0",
    )

    parser.add_argument(
        "--chunk-cache-dir",
        default=".cache/yt-transcript",
        help="Directory for chunk summary cache (resume support). Default: .cache/yt-transcript",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.summarize and not args.model:
        print("Error: --model is required when using --summarize", file=sys.stderr)
        return 5

    config = PipelineConfig(
        youtube_url=args.youtube_url,
        languages=args.languages or ["de", "en"],
        output_dir=Path(args.output_dir),
        output_dir_create=False,
        overwrite=args.overwrite == "yes",
        full_timestamps=args.hh,
        summarize=args.summarize,
        provider=args.provider,
        model=args.model,
        prompt_file=args.prompt_file,
        ollama_base_url=args.ollama_base_url,
        ollama_generate_path=args.ollama_generate_path,
        llm_timeout=args.llm_timeout,
        chunk_max_chars=args.chunk_max_chars,
        chunk_overlap_chars=args.chunk_overlap_chars,
        chunk_max_chunks=args.chunk_max_chunks,
        chunk_cache_dir=Path(args.chunk_cache_dir),
    )

    try:
        run_pipeline(config, log=print)
    except InvalidYouTubeUrl as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except NoTranscriptFound as exc:
        print(f"No transcript found: {exc}", file=sys.stderr)
        return 3
    except TranscriptFetchError as exc:
        print(f"Failed to fetch transcript: {exc}", file=sys.stderr)
        return 4
    except PromptFileNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 6
    except LLMConfigError as exc:
        print(f"LLM configuration error: {exc}", file=sys.stderr)
        return 11
    except LLMError as exc:
        print(f"LLM error: {exc}", file=sys.stderr)
        return 7
    except OutputDirectoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 8
    except OutputFileExistsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 9
    except OutputWriteError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 9
    except ChunkingError as exc:
        print(f"Chunking error: {exc}", file=sys.stderr)
        return 12
    except ChunkCacheError as exc:
        print(f"Chunk cache error: {exc}", file=sys.stderr)
        return 13

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
