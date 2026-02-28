from __future__ import annotations

import argparse
import sys

from .errors import InvalidYouTubeUrl, NoTranscriptFound, TranscriptFetchError
from .formatting import transcript_to_markdown
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
            "Preferred transcript language (repeatable). "
            "Default: --lang de --lang en"
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    languages = args.languages or ["de", "en"]

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

    output = transcript_to_markdown(transcript, full_timestamps=args.hh)

    filename = f"{video_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Saved {filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
