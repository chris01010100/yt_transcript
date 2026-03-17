from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from .chunk_cache import (
    ChunkCacheItem,
    compute_run_id,
    ensure_cache_dir,
    load_chunk_summary,
    save_chunk_summary,
    sha256_text,
)
from .chunking import build_text_chunks
from .errors import (
    LLMConfigError,
    OutputDirectoryError,
    OutputFileExistsError,
    OutputWriteError,
    PromptFileNotFound,
)
from .formatting import sanitize_filename, transcript_to_markdown
from .frontmatter import normalize_summary_markdown
from .llm_router import summarize as llm_summarize
from .youtube import (
    extract_video_id,
    fetch_transcript,
    get_oembed_title,
    get_video_publish_date,
)

LogFn = Callable[[str], None]
ProgressFn = Callable[[str, int, int | None], None]


@dataclass(frozen=True)
class PipelineConfig:
    youtube_url: str
    languages: list[str]
    output_dir: Path
    output_dir_create: bool
    overwrite: bool
    full_timestamps: bool
    summarize: bool
    provider: str
    model: str | None
    prompt_file: str
    ollama_base_url: str
    ollama_generate_path: str
    llm_timeout: float
    chunk_max_chars: int
    chunk_overlap_chars: int
    chunk_max_chunks: int
    chunk_cache_dir: Path
    openrouter_api_key: str | None = None
    openrouter_api_url: str | None = None
    openai_api_key: str | None = None
    openai_api_url: str | None = None


@dataclass(frozen=True)
class PipelineResult:
    video_id: str
    title: str
    publish_date: str | None
    raw_path: Path
    summary_path: Path | None
    transcript_md: str
    summary_md: str | None


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


def load_chunk_prompt_template() -> str:
    """Load chunk prompt template from fixed file prompt_chunks.md."""
    filename = "prompt_chunks.md"
    path = Path.cwd() / filename
    if not path.exists():
        module_dir = Path(__file__).parent.parent.parent
        path = module_dir / filename

    if not path.exists():
        raise PromptFileNotFound(f"Chunk prompt file not found: {filename}")

    return path.read_text(encoding="utf-8")


def fill_prompt_template(
    template: str,
    source_url: str,
    video_id: str,
    provider_name: str,
    model_name: str,
    transcript: str,
) -> str:
    """Replace placeholders in the prompt template."""
    return (
        template.replace("{{SOURCE_URL}}", source_url)
        .replace("{{VIDEO_ID}}", video_id)
        .replace("{{LLM_PROVIDER}}", provider_name)
        .replace("{{MODEL_NAME}}", model_name)
        .replace("{{TRANSCRIPT}}", transcript)
    )


def fill_chunk_prompt_template(
    template: str,
    *,
    source_url: str,
    video_id: str,
    provider_name: str,
    model_name: str,
    chunk_index: int,
    chunk_start_char: int,
    chunk_end_char: int,
    chunk_text: str,
) -> str:
    """Replace placeholders in chunk prompt template."""
    return (
        template.replace("{{SOURCE_URL}}", source_url)
        .replace("{{VIDEO_ID}}", video_id)
        .replace("{{LLM_PROVIDER}}", provider_name)
        .replace("{{MODEL_NAME}}", model_name)
        .replace("{{CHUNK_INDEX}}", str(chunk_index))
        .replace("{{CHUNK_START_CHAR}}", str(chunk_start_char))
        .replace("{{CHUNK_END_CHAR}}", str(chunk_end_char))
        .replace("{{CHUNK_TEXT}}", chunk_text)
    )


def ensure_output_dir(path: Path, *, create: bool) -> None:
    if path.exists():
        if not path.is_dir():
            raise OutputDirectoryError(f"Output path is not a directory: {path}")
        return

    if not create:
        raise OutputDirectoryError(f"Output directory does not exist: {path}")

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OutputDirectoryError(
            f"Could not create output directory '{path}': {exc}"
        ) from exc


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


def run_pipeline(
    config: PipelineConfig,
    *,
    log: LogFn | None = None,
    progress: ProgressFn | None = None,
) -> PipelineResult:
    log = log or (lambda _: None)

    if config.summarize and not config.model:
        raise LLMConfigError("Model is required when summarize is enabled.")

    ensure_output_dir(config.output_dir, create=config.output_dir_create)

    log("Fetching transcript...")
    video_id = extract_video_id(config.youtube_url)
    transcript = fetch_transcript(video_id, languages=config.languages)

    title = get_oembed_title(config.youtube_url) or video_id
    safe_title = sanitize_filename(title)
    publish_date = get_video_publish_date(config.youtube_url)

    raw_path, summary_path = build_output_paths(
        config.output_dir,
        publish_date=publish_date,
        safe_title=safe_title,
        video_id=video_id,
    )

    transcript_md = transcript_to_markdown(
        transcript, full_timestamps=config.full_timestamps
    )
    write_text_file(raw_path, transcript_md, overwrite=config.overwrite)
    log(f"Saved transcript: {raw_path}")

    summary_md: str | None = None
    summary_result_path: Path | None = None

    if config.summarize:
        model = config.model
        if model is None:
            raise LLMConfigError("Model is required when summarize is enabled.")

        log("Loading prompt templates...")
        final_prompt_template = load_prompt_template(config.prompt_file)
        chunk_prompt_template = load_chunk_prompt_template()
        created_at_date = datetime.now().date().isoformat()

        chunks = build_text_chunks(
            transcript_md,
            max_chars=config.chunk_max_chars,
            overlap_chars=config.chunk_overlap_chars,
            max_chunks=config.chunk_max_chunks,
        )

        total_chunks = len(chunks)
        if progress:
            progress("chunking", 0, total_chunks)

        chunk_prompt_hash = sha256_text(chunk_prompt_template)
        final_prompt_hash = sha256_text(final_prompt_template)
        run_id = compute_run_id(
            video_id=video_id,
            provider=config.provider,
            model=model,
            chunk_max_chars=config.chunk_max_chars,
            chunk_overlap_chars=config.chunk_overlap_chars,
            chunk_max_chunks=config.chunk_max_chunks,
            chunk_prompt_hash=chunk_prompt_hash,
            final_prompt_hash=final_prompt_hash,
        )

        cache_dir = config.chunk_cache_dir / video_id / run_id
        ensure_cache_dir(cache_dir)

        chunk_summaries: list[str] = []
        cache_hits = 0

        log(f"Summarizing {total_chunks} chunks...")
        for index, chunk in enumerate(chunks, start=1):
            chunk_sha = sha256_text(chunk.text)
            cached = load_chunk_summary(
                cache_dir,
                chunk.index,
                expected_text_sha=chunk_sha,
            )
            if cached:
                cache_hits += 1
                chunk_summaries.append(cached)
                if progress:
                    progress("chunking", index, total_chunks)
                continue

            chunk_prompt = fill_chunk_prompt_template(
                chunk_prompt_template,
                source_url=config.youtube_url,
                video_id=video_id,
                provider_name=config.provider,
                model_name=model,
                chunk_index=chunk.index,
                chunk_start_char=chunk.start_char,
                chunk_end_char=chunk.end_char,
                chunk_text=chunk.text,
            )

            chunk_summary = llm_summarize(
                provider=config.provider,
                model=model,
                prompt=chunk_prompt,
                timeout=config.llm_timeout,
                ollama_base_url=config.ollama_base_url,
                ollama_generate_path=config.ollama_generate_path,
                openrouter_api_key=config.openrouter_api_key,
                openrouter_api_url=config.openrouter_api_url,
                openai_api_key=config.openai_api_key,
                openai_api_url=config.openai_api_url,
            )

            save_chunk_summary(
                cache_dir,
                ChunkCacheItem(
                    chunk_index=chunk.index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    text_sha256=chunk_sha,
                    summary_md=chunk_summary,
                ),
            )
            chunk_summaries.append(chunk_summary)
            if progress:
                progress("chunking", index, total_chunks)

        log(f"Chunks done (cache hits: {cache_hits}/{total_chunks}).")

        aggregated_chunk_summaries = "\n\n".join(
            f"## Chunk {idx + 1}\n{summary}"
            for idx, summary in enumerate(chunk_summaries)
        )

        final_prompt = fill_prompt_template(
            final_prompt_template,
            source_url=config.youtube_url,
            video_id=video_id,
            provider_name=config.provider,
            model_name=model,
            transcript=aggregated_chunk_summaries,
        )

        log(f"Generating final summary with {config.provider}:{model}...")
        if progress:
            progress("final_summary", 0, 1)

        summary_md = llm_summarize(
            provider=config.provider,
            model=model,
            prompt=final_prompt,
            timeout=config.llm_timeout,
            ollama_base_url=config.ollama_base_url,
            ollama_generate_path=config.ollama_generate_path,
            openrouter_api_key=config.openrouter_api_key,
            openrouter_api_url=config.openrouter_api_url,
            openai_api_key=config.openai_api_key,
            openai_api_url=config.openai_api_url,
        )
        summary_md = normalize_summary_markdown(
            summary_md,
            source_url=config.youtube_url,
            video_id=video_id,
            llm_provider=config.provider,
            llm_model=model,
            created_at=created_at_date,
            default_title=title,
            language=(config.languages[0] if config.languages else "de"),
        )
        if progress:
            progress("final_summary", 1, 1)

        write_text_file(summary_path, summary_md, overwrite=config.overwrite)
        summary_result_path = summary_path
        log(f"Saved summary: {summary_path}")

    return PipelineResult(
        video_id=video_id,
        title=title,
        publish_date=publish_date,
        raw_path=raw_path,
        summary_path=summary_result_path,
        transcript_md=transcript_md,
        summary_md=summary_md,
    )
