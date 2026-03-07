# yt-transcript

CLI-Tool, das YouTube-Untertitel/Transkripte abruft, als Markdown-Datei mit Zeitstempeln speichert und optional per OpenRouter oder Ollama zusammenfasst.

## Was macht das Tool?

- Nimmt eine YouTube-URL entgegen und extrahiert daraus die **Video-ID**.
- Ruft über [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) das Transcript ab (bevorzugt **Deutsch**, sonst **Englisch**).
- Schreibt das Transcript als Markdown in ein frei wählbares Ausgabeverzeichnis.
- Optional: Erstellt eine ausführliche Zusammenfassung mit OpenRouter oder Ollama im selben Ausgabeverzeichnis.
- Dateinamen basieren auf Videotitel + Video-ID und optional Veröffentlichungsdatum.
- Für lange Transkripte: textbasiertes Chunking + Map/Reduce + Cache/Resume.

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
yt-transcript <youtube_url> [--hh] [--lang <code> ...] [--output-dir <dir>] [--overwrite yes|no] [--summarize --provider <openrouter|ollama> --model <model_id>] [--llm-timeout <seconds>] [--chunk-max-chars <n>] [--chunk-overlap-chars <n>] [--chunk-max-chunks <n>] [--chunk-cache-dir <path>]
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

Transcript + Zusammenfassung über OpenRouter (Default Provider):

```bash
OPENROUTER_API_KEY="<dein_key>" yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --model "openai/gpt-4o-mini"
```

Lange Transkripte mit Chunking + Cache (resumierbar):

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --provider ollama --model "qwen2.5:3b" --chunk-max-chars 7000 --chunk-overlap-chars 900 --chunk-cache-dir ".cache/yt-transcript"
```

Zusammenfassung über Ollama (`/api/generate`):

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --provider ollama --model "qwen2.5:3b"
```

Ollama mit eigener Instanz / eigenem Endpoint:

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --summarize --provider ollama --model "qwen2.5:3b" --ollama-base-url "http://192.168.1.10:11434" --ollama-generate-path "/api/generate"
```

In ein bestimmtes Verzeichnis schreiben (muss existieren):

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --output-dir "output" --summarize --model "openai/gpt-4o-mini"
```

Überschreiben erlauben:

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --output-dir "output" --overwrite yes
```

## Ausgabe

Dateien werden im durch `--output-dir` angegebenen Verzeichnis gespeichert.

Naming-Schema:

- Wenn Veröffentlichungsdatum ermittelt werden kann:
  - Raw: `YYYY-MM-DD <safe_title> (<video_id>)_raw.md`
  - Summary: `YYYY-MM-DD <safe_title> (<video_id>)_summary.md`
- Wenn kein Veröffentlichungsdatum gefunden wird:
  - Raw: `<safe_title> (<video_id>)_raw.md`
  - Summary: `<safe_title> (<video_id>)_summary.md`

Hinweise:
- `<safe_title>` ist der bereinigte Videotitel (dateisystemtauglich).
- Falls kein Titel ermittelt werden kann, wird als Fallback die `video_id` genutzt.

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

- `--output-dir <dir>`
  - Zielverzeichnis für Raw-Transcript und Summary.
  - Das Verzeichnis muss existieren und beschreibbar sein.
  - Standard: aktuelles Verzeichnis `.`

- `--overwrite yes|no`
  - Steuert, ob vorhandene Zieldateien überschrieben werden dürfen.
  - Standard: `no`

### Zusammenfassung (LLM Provider)

- `--summarize`
  - Aktiviert die Zusammenfassung nach dem Transcript-Abruf.

- `--provider <openrouter|ollama>`
  - Wählt den LLM-Provider.
  - Standard: `openrouter`

- `--model <model_id>`
  - Modell-ID für den gewählten Provider.
  - Beispiele:
    - OpenRouter: `openai/gpt-4o-mini`
    - Ollama: `qwen2.5:3b`
  - Pflicht, wenn `--summarize` gesetzt ist.

- `--prompt-file <path>`
  - Pfad zur Prompt-Datei.
  - Standard: `prompt.md`

- `--llm-timeout <seconds>`
  - Timeout für LLM-Requests.
  - Standard: `120`

### Chunking / Map-Reduce (lange Transkripte)

- `--chunk-max-chars <n>`
  - Maximale Zeichenanzahl pro Chunk.
  - Standard: `8000`

- `--chunk-overlap-chars <n>`
  - Zeichen-Overlap zwischen benachbarten Chunks.
  - Standard: `1000`

- `--chunk-max-chunks <n>`
  - Sicherheitslimit für Anzahl der Chunks.
  - `0` bedeutet unbegrenzt.
  - Standard: `0`

- `--chunk-cache-dir <path>`
  - Cache-Verzeichnis für Chunk-Zwischensummaries (Resume bei Abbruch).
  - Standard: `.cache/yt-transcript`

### Ollama (nur Generate-Endpoint)

- `--ollama-base-url <url>`
  - Basis-URL der Ollama-Instanz.
  - Standard: `http://localhost:11434`

- `--ollama-generate-path <path>`
  - Pfad zum Generate-Endpoint.
  - Standard: `/api/generate`


## Prompt

- Finale Zusammenfassung: [prompt.md](prompt.md) (über `--prompt-file` konfigurierbar)
- Teilzusammenfassungen (Chunk-Map): [prompt_chunks.md](prompt_chunks.md) (fester Dateiname, ohne CLI-Option)

Platzhalter in `prompt.md`:
- `{{SOURCE_URL}}`
- `{{VIDEO_ID}}`
- `{{MODEL_NAME}}`
- `{{TRANSCRIPT}}`

Platzhalter in `prompt_chunks.md`:
- `{{SOURCE_URL}}`
- `{{VIDEO_ID}}`
- `{{MODEL_NAME}}`
- `{{CHUNK_INDEX}}`
- `{{CHUNK_START_CHAR}}`
- `{{CHUNK_END_CHAR}}`
- `{{CHUNK_TEXT}}`

## Versionsverlauf

- **0.5**
  - Textbasiertes Chunking für lange Transkripte implementiert (Whisper-kompatibel)
  - Neue CLI-Optionen: `--chunk-max-chars`, `--chunk-overlap-chars`, `--chunk-max-chunks`, `--chunk-cache-dir`
  - Map/Reduce-Pipeline eingeführt (Chunk-Zusammenfassungen + finale Zusammenfassung)
  - Cache/Resume für Chunk-Summaries implementiert
  - Neuer Chunk-Prompt in `prompt_chunks.md`
  - Errorhandling für Chunking/Cache ergänzt

- **0.4**
  - Provider-Auswahl für Zusammenfassung ergänzt: `--provider openrouter|ollama` (Default: `openrouter`)
  - Ollama-Integration über `generate`-Endpoint implementiert
  - Neue Ollama-Optionen: `--ollama-base-url`, `--ollama-generate-path`
  - Neues globales LLM-Timeout: `--llm-timeout`
  - LLM-Routing-Schicht (`llm_router.py`) eingeführt
  - Erweitertes LLM-Errorhandling (Konfiguration/Provider/Response)

- **0.3**
  - Ausgabe-Pfadsteuerung über `--output-dir` eingeführt
  - Überschreibverhalten über `--overwrite yes|no` ergänzt
  - Option `--summary-out` entfernt
  - Dateinamen auf Titel + Video-ID umgestellt und Raw/Summary-Suffix vereinheitlicht
  - Best-effort Ermittlung des Veröffentlichungsdatums ergänzt (Prefix `YYYY-MM-DD` wenn verfügbar)
  - Robustes Errorhandling für Ausgabeverzeichnis, existierende Dateien und Schreibfehler ergänzt

- **0.2**
  - OpenRouter-Integration für optionale Transcript-Zusammenfassungen implementiert
  - Neue CLI-Optionen: `--summarize`, `--model`, `--prompt-file`
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
