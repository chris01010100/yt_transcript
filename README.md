# yt-transcript

Kleines CLI-Script, das YouTube-Untertitel/Transkripte abruft und als Markdown-Datei mit Zeitstempeln speichert.

## Was macht das Script?

- Nimmt eine YouTube-URL entgegen und extrahiert daraus die **Video-ID**.
- Ruft über [`youtube-transcript-api`](https://pypi.org/project/youtube-transcript-api/) das Transcript ab (bevorzugt **Deutsch**, sonst **Englisch**).
- Schreibt das Ergebnis als Markdown in eine Datei namens **`<video_id>.md`**.
- Jede Zeile enthält einen Zeitstempel und den Text:
  
  ```text
  [00:12] …
  [00:18] …
  ```

## Grobe Funktionsweise

1. **Video-ID extrahieren**: Unterstützt URLs der Formen `...watch?v=<id>` und `youtu.be/<id>`.
2. **Transcript laden**: `api.fetch(video_id, languages=["de", "en"])`.
3. **Zeitstempel formatieren**:
   - Standard: `MM:SS` (oder `H:MM:SS`, sobald Stunden auftreten)
   - Mit `--hh`: immer `HH:MM:SS`
4. **Datei schreiben**: Ausgabe wird in `<video_id>.md` im aktuellen Verzeichnis gespeichert.

## Voraussetzungen

- Python **>= 3.12**
- Abhängigkeit: `youtube-transcript-api`

## Installation

Wenn du `uv` verwendest:

```bash
uv sync
```

Danach kannst du das Tool aus der Projektumgebung direkt ausführen:

```bash
uv run yt-transcript <youtube_url> [--hh] [--lang <code> ...]
```

Alternativ mit `pip` (aus dem Repo-Verzeichnis):

```bash
pip install .
```

Danach steht das Kommando `yt-transcript` zur Verfügung.

## Benutzung

```bash
yt-transcript <youtube_url> [--hh] [--lang <code> ...]
```

### Beispiele

Transcript abrufen und mit kompaktem Zeitformat speichern:

```bash
yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Zeitstempel immer zweistellig mit Stunden (`HH:MM:SS`) ausgeben:

```bash
yt-transcript "https://youtu.be/dQw4w9WgXcQ" --hh
```

Bevorzugte Sprachen explizit setzen (repeatable):

```bash
yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --lang de --lang en
```

### Ausgabe

- Es wird eine Datei **`<video_id>.md`** erstellt (z.B. `dQw4w9WgXcQ.md`).
- Format pro Zeile:

```text
[MM:SS] Text
```

bzw. abhängig von der Option auch `H:MM:SS` oder `HH:MM:SS`.

## CLI Optionen

- `--hh`
  - Erzwingt ein fixes Zeitformat `HH:MM:SS`.
  - Ohne Option wird `MM:SS` verwendet (bzw. `H:MM:SS`, sobald Stunden > 0).

- `--lang <code>` (repeatable)
  - Setzt die bevorzugten Transcript-Sprachen in Reihenfolge.
  - Standard: `--lang de --lang en`

## Versionsverlauf

- **0.1**
  - Initiale Version: Transcript abrufen (de/en), Zeitstempel formatieren, Ausgabe als `<video_id>.md`.

## Todo

- **Transcript per LLM zusammenfassen** und die Zusammenfassung als **formatierte Markdown-Datei für Obsidian** mit **YAML Frontmatter** speichern.
  - Routing über **OpenRouter-API** oder **lokales LLM** wie Ollama
  - Das zu verwendende LLM/Model soll **flexibel als Variable** konfigurierbar sein (z.B. CLI-Parameter `--model` oder Env `OPENROUTER_MODEL`).
  - Die Zusammenfassung soll **ausführlich** sein.
- **Wenn es kein Transcript gibt oder wenn ich ein neues Transcript als Option erstellen will**
    - mit yt-dl soll das Audio aus dem Video extrahiert, heruntergeladen werden
    - Anschliessend soll die Audio Datei mit LLM transcribiert werden. Es soll OpenAI STT oder lokale Modelle wie Whisper unterstützt werden
    - Das neu erstellte Transcript soll anschliessend wie ein auch per LLM (Openrouter oder lokales LLM) zusammengefasst und in einer Markdown Datei für Obsidian mit YAML Frontmatter gespeichert werden

### Prompt

Siehe [prompt.md](prompt.md).
