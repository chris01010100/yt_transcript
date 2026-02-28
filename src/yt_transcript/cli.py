from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import (
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
from .formatting import sanitize_filename, transcript_to_markdown
from .llm_router import summarize as llm_summarize
from .youtube import (
    extract_video_id,
    fetch_transcript,
    get_oembed_title,
    get_video_publish_date,
)


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

    return parser


def load_prompt_template(prompt_file: str) -> str:
    """Load the prompt template from a file."""
    path = Path(prompt_file)
    if not path.is_absolute():
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            path = cwd_path
        else:
            module_dir = Path(__file__).parent.parent.parent
            module_path = module_dir / path
            if module_path.exists():
                path = module_path

    if not path.exists():
        raise PromptFileNotFound(f"Prompt file not found: {prompt_file}")

    return path.read_text(encoding="utf-8")


def fill_prompt_template(
    template: str,
    source_url: str,
    video_id: str,
    model_name: str,
    transcript: str,
) -> str:
    """Replace placeholders in the prompt template."""
    return (
        template.replace("{{SOURCE_URL}}", source_url)
        .replace("{{VIDEO_ID}}", video_id)
        .replace("{{MODEL_NAME}}", model_name)
        .replace("{{TRANSCRIPT}}", transcript)
    )


def ensure_output_dir(path: Path) -> None:
    if not path.exists():
        raise OutputDirectoryError(f"Output directory does not exist: {path}")

    if not path.is_dir():
        raise OutputDirectoryError(f"Output path is not a directory: {path}")


def build_output_paths(
    output_dir: Path, *, publish_date: str | None, safe_title: str, video_id: str
) -> tuple[Path, Path]:
    prefix = f"{publish_date} " if publish_date else ""
    base = f"{prefix}{safe_title} ({video_id})"
    raw_path = output_dir / f"{base}_raw.md"
    summary_path = output_dir / f"{base}_summary.md"
    return raw_path, summary_path


def write_text_file(path: Path, content: str, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise OutputFileExistsError(
            f"Output file already exists and overwrite=no: {path}"
        )

    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OutputWriteError(f"Could not write file '{path}': {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    languages = args.languages or ["de", "en"]
    overwrite = args.overwrite == "yes"

    if args.summarize and not args.model:
        print("Error: --model is required when using --summarize", file=sys.stderr)
        return 5

    try:
        output_dir = Path(args.output_dir)
        ensure_output_dir(output_dir)
    except OutputDirectoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 8

    try:
        video_id = extract_video_id(args.youtube_url)
        transcript = fetch_transcript(video_id, languages=languages)
    except InvalidYouTubeUrl as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except NoTranscriptFound as exc:
        print(f"No transcript found: {exc}", file=sys.stderr)
        return 3
    except TranscriptFetchError as exc:
        print(f"Failed to fetch transcript: {exc}", file=sys.stderr)
        return 4

    title = get_oembed_title(args.youtube_url) or video_id
    safe_title = sanitize_filename(title)
    publish_date = get_video_publish_date(args.youtube_url)

    raw_path, summary_path = build_output_paths(
        output_dir,
        publish_date=publish_date,
        safe_title=safe_title,
        video_id=video_id,
    )

    transcript_md = transcript_to_markdown(transcript, full_timestamps=args.hh)

    try:
        write_text_file(raw_path, transcript_md, overwrite=overwrite)
    except (OutputFileExistsError, OutputWriteError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 9

    print(f"Saved transcript: {raw_path}")

    if args.summarize:
        try:
            prompt_template = load_prompt_template(args.prompt_file)
            prompt = fill_prompt_template(
                prompt_template,
                source_url=args.youtube_url,
                video_id=video_id,
                model_name=args.model,
                transcript=transcript_md,
            )

            print(f"Generating summary with {args.provider}:{args.model}...")
            summary = llm_summarize(
                provider=args.provider,
                model=args.model,
                prompt=prompt,
                timeout=args.llm_timeout,
                ollama_base_url=args.ollama_base_url,
                ollama_generate_path=args.ollama_generate_path,
            )
        except PromptFileNotFound as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 6
        except LLMConfigError as exc:
            print(f"LLM configuration error: {exc}", file=sys.stderr)
            return 11
        except LLMError as exc:
            print(f"LLM error: {exc}", file=sys.stderr)
            return 7

        try:
            write_text_file(summary_path, summary, overwrite=overwrite)
        except (OutputFileExistsError, OutputWriteError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 10

        print(f"Saved summary: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
