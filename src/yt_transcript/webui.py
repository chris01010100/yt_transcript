from __future__ import annotations

import asyncio
import os
import queue
from pathlib import Path
from typing import Any, Literal, cast

import flet as ft

from .pipeline import PipelineConfig, run_pipeline


ThemeChoice = Literal["system", "light", "dark"]


def _theme_mode_from_choice(choice: ThemeChoice) -> ft.ThemeMode:
    if choice == "light":
        return ft.ThemeMode.LIGHT
    if choice == "dark":
        return ft.ThemeMode.DARK
    return ft.ThemeMode.SYSTEM


def _stage_label(stage: str) -> str:
    if stage == "chunking":
        return "Chunk summaries"
    if stage == "final_summary":
        return "Final summary"
    return stage


def main() -> None:
    host = os.environ.get("YT_TRANSCRIPT_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("YT_TRANSCRIPT_WEB_PORT", "8550"))
    ft.app(target=app_main, view=ft.AppView.WEB_BROWSER, host=host, port=port)


async def app_main(page: ft.Page) -> None:
    page.title = "yt-transcript WebUI"
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO, use_material3=True)
    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE, use_material3=True)
    page.theme_mode = ft.ThemeMode.SYSTEM

    log_lines_max = 200
    is_running = False
    current_status = "Idle"
    summary_value = ""
    result_path_value = ""

    event_queue: queue.Queue[tuple[str, Any]] = queue.Queue()

    def show_snack(message: str) -> None:
        snack = ft.SnackBar(content=ft.Text(message), open=True)
        page.overlay.append(snack)
        page.update()

    # --- Header / Theme ---
    theme_dropdown = ft.Dropdown(
        label="Theme",
        value="system",
        width=170,
        options=[
            ft.dropdown.Option("system", "System"),
            ft.dropdown.Option("light", "Light"),
            ft.dropdown.Option("dark", "Dark"),
        ],
    )

    # --- Inputs ---
    youtube_url = ft.TextField(
        label="YouTube URL",
        hint_text="https://www.youtube.com/watch?v=...",
        expand=True,
    )
    provider = ft.Dropdown(
        label="LLM Provider",
        value="openrouter",
        options=[
            ft.dropdown.Option("openrouter"),
            ft.dropdown.Option("ollama"),
        ],
        width=220,
    )
    model = ft.TextField(
        label="Model",
        hint_text="openai/gpt-4o-mini oder qwen2.5:3b",
        expand=True,
    )

    lang_de = ft.Checkbox(label="de", value=True)
    lang_en = ft.Checkbox(label="en", value=True)
    lang_fr = ft.Checkbox(label="fr", value=False)
    lang_es = ft.Checkbox(label="es", value=False)

    summarize_checkbox = ft.Checkbox(label="Summarize", value=True, disabled=True)
    overwrite_switch = ft.Switch(label="Overwrite existing files", value=False)
    prompt_file = ft.TextField(label="Prompt file", value="prompt.md", expand=True)

    ollama_base_url = ft.TextField(
        label="Ollama base URL",
        value="http://localhost:11434",
        expand=True,
    )
    ollama_generate_path = ft.TextField(
        label="Ollama generate path",
        value="/api/generate",
        expand=True,
    )

    ollama_fields = ft.Column(
        controls=[ollama_base_url, ollama_generate_path],
        spacing=10,
        visible=False,
    )

    # --- Progress / Status ---
    status_text = ft.Text("Status: Idle", weight=ft.FontWeight.W_500)
    progress_text = ft.Text("Progress: -", size=12)
    progress_ring = ft.ProgressRing(visible=False)

    # --- Log ---
    log_list = ft.ListView(
        expand=True,
        spacing=6,
        auto_scroll=True,
        height=220,
    )

    # --- Summary ---
    summary_title = ft.Text("Summary", size=18, weight=ft.FontWeight.BOLD)
    summary_saved_path = ft.Text("", selectable=True, size=12)
    summary_md = ft.Markdown(
        value="Noch keine Zusammenfassung vorhanden.",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )

    run_button = ft.FilledButton(content="Start")
    reset_button = ft.OutlinedButton(content="Reset")

    def selected_languages() -> list[str]:
        langs: list[str] = []
        if lang_de.value:
            langs.append("de")
        if lang_en.value:
            langs.append("en")
        if lang_fr.value:
            langs.append("fr")
        if lang_es.value:
            langs.append("es")
        return langs or ["de", "en"]

    def set_running_state(running: bool) -> None:
        nonlocal is_running
        is_running = running
        run_button.disabled = running
        youtube_url.disabled = running
        provider.disabled = running
        model.disabled = running
        lang_de.disabled = running
        lang_en.disabled = running
        lang_fr.disabled = running
        lang_es.disabled = running
        overwrite_switch.disabled = running
        prompt_file.disabled = running
        ollama_base_url.disabled = running
        ollama_generate_path.disabled = running
        theme_dropdown.disabled = running
        progress_ring.visible = running

    def add_log_line(text: str) -> None:
        if len(log_list.controls) >= log_lines_max:
            log_list.controls = log_list.controls[-(log_lines_max - 1) :]
        log_list.controls.append(ft.Text(text, size=12, selectable=True))

    def rebuild_summary() -> None:
        summary_md.value = summary_value or "Noch keine Zusammenfassung vorhanden."
        summary_saved_path.value = (
            f"Gespeichert unter: {result_path_value}" if result_path_value else ""
        )

    def update_provider_visibility() -> None:
        ollama_fields.visible = provider.value == "ollama"

    async def drain_events_until_done(done_marker: asyncio.Event) -> None:
        nonlocal current_status, summary_value, result_path_value
        while True:
            processed_any = False
            try:
                while True:
                    kind, payload = event_queue.get_nowait()
                    processed_any = True
                    if kind == "log":
                        add_log_line(str(payload))
                    elif kind == "progress":
                        stage, current, total = cast(
                            tuple[str, int, int | None], payload
                        )
                        current_status = _stage_label(stage)
                        if total is None or total <= 0:
                            progress_text.value = f"Progress: {current_status}"
                        else:
                            progress_text.value = (
                                f"Progress: {current_status} ({current}/{total})"
                            )
                    elif kind == "result_summary":
                        summary_value = str(payload)
                    elif kind == "result_path":
                        result_path_value = str(payload)
                    elif kind == "error":
                        add_log_line(f"Error: {payload}")
                    elif kind == "status":
                        status_text.value = f"Status: {payload}"
            except queue.Empty:
                pass

            rebuild_summary()
            if processed_any:
                page.update()

            if done_marker.is_set():
                # one final drain after done
                try:
                    while True:
                        kind, payload = event_queue.get_nowait()
                        if kind == "log":
                            add_log_line(str(payload))
                        elif kind == "progress":
                            stage, current, total = cast(
                                tuple[str, int, int | None], payload
                            )
                            current_status = _stage_label(stage)
                            if total is None or total <= 0:
                                progress_text.value = f"Progress: {current_status}"
                            else:
                                progress_text.value = (
                                    f"Progress: {current_status} ({current}/{total})"
                                )
                        elif kind == "result_summary":
                            summary_value = str(payload)
                        elif kind == "result_path":
                            result_path_value = str(payload)
                        elif kind == "error":
                            add_log_line(f"Error: {payload}")
                        elif kind == "status":
                            status_text.value = f"Status: {payload}"
                except queue.Empty:
                    pass

                rebuild_summary()
                page.update()
                return

            await asyncio.sleep(0.15)

    async def on_theme_change(_: Any) -> None:
        choice = cast(ThemeChoice, theme_dropdown.value or "system")
        page.theme_mode = _theme_mode_from_choice(choice)
        page.update()

    async def on_provider_change(_: Any) -> None:
        update_provider_visibility()
        page.update()

    async def on_reset(_: Any) -> None:
        if is_running:
            return
        youtube_url.value = ""
        provider.value = "openrouter"
        model.value = ""
        lang_de.value = True
        lang_en.value = True
        lang_fr.value = False
        lang_es.value = False
        overwrite_switch.value = False
        prompt_file.value = "prompt.md"
        ollama_base_url.value = "http://localhost:11434"
        ollama_generate_path.value = "/api/generate"
        log_list.controls.clear()
        status_text.value = "Status: Idle"
        progress_text.value = "Progress: -"
        update_provider_visibility()
        page.update()

    async def on_run(_: Any) -> None:
        nonlocal summary_value, result_path_value

        if is_running:
            return

        if not (youtube_url.value or "").strip():
            show_snack("Bitte YouTube-URL eingeben.")
            return

        if not (model.value or "").strip():
            show_snack("Bitte ein LLM-Modell eintragen.")
            return

        summary_value = ""
        result_path_value = ""
        rebuild_summary()
        log_list.controls.clear()
        status_text.value = "Status: Running"
        progress_text.value = "Progress: Starting..."
        add_log_line("Starting job...")

        set_running_state(True)
        update_provider_visibility()
        page.update()

        output_dir = Path("output")
        config = PipelineConfig(
            youtube_url=(youtube_url.value or "").strip(),
            languages=selected_languages(),
            output_dir=output_dir,
            output_dir_create=True,
            overwrite=bool(overwrite_switch.value),
            full_timestamps=False,
            summarize=True,
            provider=(provider.value or "openrouter"),
            model=(model.value or "").strip(),
            prompt_file=(prompt_file.value or "prompt.md").strip(),
            ollama_base_url=(ollama_base_url.value or "http://localhost:11434").strip(),
            ollama_generate_path=(
                ollama_generate_path.value or "/api/generate"
            ).strip(),
            llm_timeout=120.0,
            chunk_max_chars=8000,
            chunk_overlap_chars=1000,
            chunk_max_chunks=0,
            chunk_cache_dir=Path(".cache/yt-transcript"),
        )

        done = asyncio.Event()

        def worker() -> None:
            def log_cb(msg: str) -> None:
                event_queue.put(("log", msg))

            def progress_cb(stage: str, current: int, total: int | None) -> None:
                event_queue.put(("progress", (stage, current, total)))

            try:
                event_queue.put(("status", "Running"))
                result = run_pipeline(config, log=log_cb, progress=progress_cb)
                if result.summary_md:
                    event_queue.put(("result_summary", result.summary_md))
                if result.summary_path:
                    event_queue.put(("result_path", str(result.summary_path)))
                event_queue.put(("status", "Done"))
                event_queue.put(("log", "Job finished successfully."))
            except Exception as exc:  # noqa: BLE001
                event_queue.put(("status", "Failed"))
                event_queue.put(("error", str(exc)))
            finally:
                done.set()

        drainer_task = asyncio.create_task(drain_events_until_done(done))
        await asyncio.to_thread(worker)
        await drainer_task

        set_running_state(False)
        update_provider_visibility()
        page.update()

    theme_dropdown.on_select = lambda e: asyncio.create_task(on_theme_change(e))
    provider.on_select = lambda e: asyncio.create_task(on_provider_change(e))
    run_button.on_click = lambda e: asyncio.create_task(on_run(e))
    reset_button.on_click = lambda e: asyncio.create_task(on_reset(e))

    update_provider_visibility()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("yt-transcript WebUI", size=24, weight=ft.FontWeight.BOLD),
            theme_dropdown,
        ],
    )

    input_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Input", size=18, weight=ft.FontWeight.BOLD),
                    youtube_url,
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(provider, col={"xs": 12, "md": 4}),
                            ft.Container(model, col={"xs": 12, "md": 8}),
                        ]
                    ),
                    ft.Text("Sprachen", weight=ft.FontWeight.W_500),
                    ft.Row(
                        controls=[lang_de, lang_en, lang_fr, lang_es],
                        wrap=True,
                        spacing=10,
                    ),
                    ft.Row(
                        controls=[summarize_checkbox, overwrite_switch],
                        wrap=True,
                        spacing=16,
                    ),
                    prompt_file,
                    ollama_fields,
                    ft.Row(
                        controls=[run_button, reset_button, progress_ring],
                        spacing=12,
                    ),
                    status_text,
                    progress_text,
                ],
            ),
        )
    )

    log_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("Log", size=18, weight=ft.FontWeight.BOLD),
                    log_list,
                ],
            ),
        )
    )

    summary_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                spacing=10,
                controls=[
                    summary_title,
                    summary_saved_path,
                    ft.Container(
                        content=summary_md,
                        expand=True,
                    ),
                ],
            ),
        )
    )

    left_column = ft.Column(
        expand=True,
        spacing=12,
        controls=[input_card, log_card],
    )
    right_column = ft.Column(
        expand=True,
        spacing=12,
        controls=[summary_card],
    )

    content = ft.ResponsiveRow(
        controls=[
            ft.Container(left_column, col={"xs": 12, "md": 6}),
            ft.Container(right_column, col={"xs": 12, "md": 6}),
        ],
        run_spacing=12,
    )

    page.add(header, content)
    page.update()
