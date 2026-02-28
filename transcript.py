import re
import sys
from datetime import timedelta
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not match:
        raise ValueError("Could not extract video ID from URL")
    return match.group(1)


def format_timestamp(seconds: float, full: bool = False) -> str:
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if full:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcript.py <youtube_url> [--hh]")
        sys.exit(1)

    url = sys.argv[1]
    use_full_format = "--hh" in sys.argv

    video_id = extract_video_id(url)

    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=["de", "en"])

    lines = []

    for entry in transcript:
        ts = format_timestamp(entry.start, full=use_full_format)
        lines.append(f"[{ts}] {entry.text}")

    output = "\n".join(lines)

    filename = f"{video_id}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Saved {filename}")


if __name__ == "__main__":
    main()
