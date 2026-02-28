# yt-transcript

CLI-Tool, das YouTube-Untertitel/Transkripte abruft, als Markdown-Datei mit Zeitstempeln speichert und optional per OpenRouter zusammenfassen kann.

## Was macht das Tool?

- Nimmt eine YouTube-URL entgegen und extrahiert daraus die **Video-ID**.
- Ruft über [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) das Transcript ab (bevorzugt **Deutsch**, sonst **Englisch**).
- Schreibt das Transcript als Markdown in **`<video_id>.md`**.
- Optional: Erstellt eine ausführliche Zusammenfassung mit einem OpenRouter-Modell und speichert sie in **`<video_id>_summary.md`** (oder in einen von dir gewählten Pfad).

## Voraussetzungen

- Python **>= 3.12**
- Dependencies:
  - `youtube-transcript-api`
  - `httpx`
- Für Zusammenfassungen: `OPENROUTER_API_KEY` als Umgebungsvariable

## Installation

Mit `uv`:

```bash
uv sync
uv pip install -e .
```

Danach ist das Kommando verfügbar:

```bash
yt-transcript --help
```

## Benutzung

```bash
yt-transcript <youtube_url> [--hh] [--lang <code> ...] [--summarize --model <model_id>]
```

## Beispiele

Transcript abrufen und speichern:

```bash
yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Zeitstempel als `HH:MM:SS` erzwingen:

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --hh
```

Sprachpriorität setzen:

```bash
yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --lang de --lang en
```

Transcript + Zusammenfassung über OpenRouter:

```bash
OPENROUTER_API_KEY="<dein_key>" yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --model "openai/gpt-4o-mini"
```

Zusammenfassung in eigene Datei schreiben:

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --model "openai/gpt-4o-mini" --summary-out "output/summary.md"
```

## Ausgabe

- Transcript: **`<video_id>.md`**
- Zusammenfassung (optional): **`<video_id>_summary.md`** oder Wert aus `--summary-out`

Transcript-Zeilenformat:

```text
[MM:SS] Text
```

(je nach Option auch `H:MM:SS` oder `HH:MM:SS`)

## CLI Optionen

### Transcript

- `--hh`
  - Erzwingt fixes Zeitformat `HH:MM:SS`.

- `--lang <code>` (repeatable)
  - Setzt die bevorzugten Transcript-Sprachen in Reihenfolge.
  - Standard: `de`, `en`

### Zusammenfassung (OpenRouter)

- `--summarize`
  - Aktiviert die Zusammenfassung nach dem Transcript-Abruf.

- `--model <model_id>`
  - OpenRouter Modell-ID (z. B. `openai/gpt-4o-mini`).
  - Pflicht, wenn `--summarize` gesetzt ist.

- `--prompt-file <path>`
  - Pfad zur Prompt-Datei.
  - Standard: `prompt.md`

- `--summary-out <path>`
  - Zielpfad für die Zusammenfassung.
  - Standard: `<video_id>_summary.md`

## Prompt

Der Prompt für die Zusammenfassung liegt in [prompt.md](prompt.md).
Er wird beim Zusammenfassen geladen und mit Platzhaltern befüllt:

- `{{SOURCE_URL}}`
- `{{VIDEO_ID}}`
- `{{MODEL_NAME}}`
- `{{TRANSCRIPT}}`

## Versionsverlauf

- **0.2**
  - OpenRouter-Integration für optionale Transcript-Zusammenfassungen implementiert
  - Neue CLI-Optionen: `--summarize`, `--model`, `--prompt-file`, `--summary-out`
  - Prompt-Auslagerung in `prompt.md` und Platzhalter-Befüllung im Laufzeitprozess
  - Eigene Fehlerbehandlung für Prompt/OpenRouter ergänzt
  - README überarbeitet und auf aktuellen CLI-Stand gebracht

- **0.1**
  - Initiale Transcript-Version
  - Projektstruktur auf `src/yt_transcript` umgestellt
  - CLI über `yt-transcript`

## Todo

- Fallback ohne YouTube-Transcript:
  - Audio mit yt-dlp extrahieren
  - STT mit OpenAI oder lokalem Whisper
  - Danach ebenfalls zusammenfassen und als Obsidian-Markdown mit YAML Frontmatter speichern
