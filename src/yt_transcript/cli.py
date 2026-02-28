from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import (
    InvalidYouTubeUrl,
    NoTranscriptFound,
    OpenRouterError,
    PromptFileNotFound,
    TranscriptFetchError,
)
from .formatting import transcript_to_markdown
from .openrouter import chat_completion
from .youtube import extract_video_id, fetch_transcript


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

    # OpenRouter / Summarization options
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate a summary using OpenRouter after fetching the transcript.",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="OpenRouter model ID for summarization (e.g. openai/gpt-4o-mini). Required if --summarize is set.",
    )

    parser.add_argument(
        "--prompt-file",
        default="prompt.md",
        help="Path to the prompt template file. Default: prompt.md",
    )

    parser.add_argument(
        "--summary-out",
        default=None,
        help="Output path for the summary file. Default: <video_id>_summary.md",
    )

    return parser


def load_prompt_template(prompt_file: str) -> str:
    """Load the prompt template from a file."""
    path = Path(prompt_file)
    if not path.is_absolute():
        # Try relative to current working directory first
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            path = cwd_path
        else:
            # Try relative to the module directory
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    languages = args.languages or ["de", "en"]

    # Validate summarize options
    if args.summarize and not args.model:
        print("Error: --model is required when using --summarize", file=sys.stderr)
        return 5

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

    transcript_md = transcript_to_markdown(transcript, full_timestamps=args.hh)

    # Save transcript
    transcript_filename = f"{video_id}.md"
    with open(transcript_filename, "w", encoding="utf-8") as f:
        f.write(transcript_md)
    print(f"Saved transcript: {transcript_filename}")

    # Summarize if requested
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

            print(f"Generating summary with {args.model}...")
            summary = chat_completion(
                model=args.model,
                messages=[{"role": "user", "content": prompt}],
            )
        except PromptFileNotFound as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 6
        except OpenRouterError as exc:
            print(f"OpenRouter error: {exc}", file=sys.stderr)
            return 7

        # Save summary
        summary_filename = args.summary_out or f"{video_id}_summary.md"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Saved summary: {summary_filename}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
