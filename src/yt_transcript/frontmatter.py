from __future__ import annotations

import json


def _unwrap_markdown_code_fence(markdown: str) -> str:
    text = markdown.strip()
    if not text.startswith("```"):
        return markdown

    lines = text.splitlines()
    if len(lines) < 2:
        return markdown

    if not lines[-1].strip().startswith("```"):
        return markdown

    return "\n".join(lines[1:-1]).strip("\n")


def _extract_leading_frontmatter_blocks(markdown: str) -> tuple[list[str], str]:
    lines = markdown.lstrip("\n").splitlines()
    blocks: list[str] = []
    idx = 0

    while idx < len(lines) and lines[idx].strip() == "---":
        end_idx: int | None = None
        for j in range(idx + 1, len(lines)):
            if lines[j].strip() == "---":
                end_idx = j
                break

        if end_idx is None:
            break

        blocks.append("\n".join(lines[idx + 1 : end_idx]))
        idx = end_idx + 1

        while idx < len(lines) and not lines[idx].strip():
            idx += 1

    remaining = "\n".join(lines[idx:]).rstrip("\n")
    return blocks, remaining


def _parse_frontmatter_block(block: str) -> dict[str, str]:
    result: dict[str, str] = {}

    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- "):
            line = line[2:].strip()

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        if key:
            result[key] = value

    return result


def _parse_tags(value: str | None) -> list[str]:
    if not value:
        return []

    raw = value.strip()
    if not raw:
        return []

    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]

    items = [part.strip().strip('"').strip("'") for part in raw.split(",")]
    tags: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        tags.append(item)
    return tags


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_frontmatter(
    *,
    title: str,
    source_url: str,
    video_id: str,
    language: str,
    llm_provider: str,
    llm_model: str,
    created_at: str,
    tags: list[str],
) -> str:
    tags_json = json.dumps(tags, ensure_ascii=False)
    lines = [
        "---",
        f"title: {_yaml_scalar(title)}",
        f"source_url: {_yaml_scalar(source_url)}",
        f"video_id: {_yaml_scalar(video_id)}",
        f"language: {_yaml_scalar(language)}",
        f"llm_provider: {_yaml_scalar(llm_provider)}",
        f"llm_model: {_yaml_scalar(llm_model)}",
        f"created_at: {_yaml_scalar(created_at)}",
        f"tags: {tags_json}",
        "---",
    ]
    return "\n".join(lines)


def normalize_summary_markdown(
    summary_md: str,
    *,
    source_url: str,
    video_id: str,
    llm_provider: str,
    llm_model: str,
    created_at: str,
    default_title: str,
    language: str = "de",
) -> str:
    unwrapped = _unwrap_markdown_code_fence(summary_md)
    blocks, body = _extract_leading_frontmatter_blocks(unwrapped)

    first_meta = _parse_frontmatter_block(blocks[0]) if blocks else {}
    title = (first_meta.get("title") or "").strip() or default_title
    tags = _parse_tags(first_meta.get("tags"))

    # Keep model-generated tags if present, otherwise provide sensible defaults.
    if not tags:
        tags = ["youtube", "transcript"]

    frontmatter = build_frontmatter(
        title=title,
        source_url=source_url,
        video_id=video_id,
        language=language,
        llm_provider=llm_provider,
        llm_model=llm_model,
        created_at=created_at,
        tags=tags,
    )

    body_no_fence = _unwrap_markdown_code_fence(body)
    cleaned_body = body_no_fence.strip("\n")
    if not cleaned_body:
        return frontmatter + "\n"

    return f"{frontmatter}\n{cleaned_body}\n"
