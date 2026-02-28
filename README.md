# yt-transcript

CLI-Tool, das YouTube-Untertitel/Transkripte abruft, als Markdown-Datei mit Zeitstempeln speichert und optional per OpenRouter zusammenfassen kann.

## Was macht das Tool?

- Nimmt eine YouTube-URL entgegen und extrahiert daraus die **Video-ID**.
- Ruft über [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) das Transcript ab (bevorzugt **Deutsch**, sonst **Englisch**).
- Schreibt das Transcript als Markdown in ein frei wählbares Ausgabeverzeichnis.
- Optional: Erstellt eine ausführliche Zusammenfassung mit einem OpenRouter-Modell im selben Ausgabeverzeichnis.
- Dateinamen basieren auf Videotitel + Video-ID und optional Veröffentlichungsdatum.

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
yt-transcript <youtube_url> [--hh] [--lang <code> ...] [--output-dir <dir>] [--overwrite yes|no] [--summarize --model <model_id>]
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

### Zusammenfassung (OpenRouter)

- `--summarize`
  - Aktiviert die Zusammenfassung nach dem Transcript-Abruf.

- `--model <model_id>`
  - OpenRouter Modell-ID (z. B. `openai/gpt-4o-mini`).
  - Pflicht, wenn `--summarize` gesetzt ist.

- `--prompt-file <path>`
  - Pfad zur Prompt-Datei.
  - Standard: `prompt.md`


## Prompt

Der Prompt für die Zusammenfassung liegt in [prompt.md](prompt.md).
Er wird beim Zusammenfassen geladen und mit Platzhaltern befüllt:

- `{{SOURCE_URL}}`
- `{{VIDEO_ID}}`
- `{{MODEL_NAME}}`
- `{{TRANSCRIPT}}`

## Versionsverlauf

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
