1) Idealer Workflow

Ziel

Immer ein Transcript bekommen, egal ob YouTube eins anbietet oder nicht.

Pipeline (robust & günstig)
	1.	Input: YouTube-URL
	2.	Try #1 (kostenlos): YouTube-Transcript ziehen
	•	Nutze youtube-transcript-api
	•	Ergebnis: Text + Timecodes (Startzeit)
	3.	Fallback (wenn kein Transcript): Audio extrahieren
	•	yt-dlp → nur Audio, z.B. m4a/mp3
	4.	Try #2 (kostenpflichtig, aber zuverlässig): OpenAI Speech-to-Text
	•	Upload Audio → Transcription
	•	Ergebnis: Text (je nach Output auch segmentiert/zeitlich)
	5.	Export: Markdown für Obsidian
	•	YAML Frontmatter (title, url, video_id, created, source=“youtube|openai”)
	•	Body: [mm:ss] text…
	6.	Optional (Qualität): Post-Processing
	•	Zeilen zusammenführen (weniger „abgehackt“)
	•	Kapitel/Outline (LLM, z.B. über OpenRouter)
	•	Keywords/Tags (für Obsidian)

Warum das ideal ist:
	•	80% der Fälle kostenlos und sofort.
	•	20% der Fälle mit OpenAI STT, dafür “immer klappt’s”.
	•	Du hast ein einheitliches Exportformat, egal aus welcher Quelle.

⸻

2) Sauber in VS Code strukturieren

Projektstruktur (klein, aber skalierbar)
	•	src/yt_transcript/ (eigentliche Logik)
	•	__init__.py
	•	cli.py (Argumente parsen, Einstiegspunkt)
	•	youtube.py (ID extrahieren, oEmbed Titel holen, transcript versuchen)
	•	audio.py (yt-dlp wrapper: download/cleanup)
	•	stt_openai.py (OpenAI transcription wrapper)
	•	formatting.py (timestamp formatting, markdown/yaml output)
	•	errors.py (eigene Exceptions wie NoTranscriptFound, etc.)
	•	tests/ (später, optional)
	•	pyproject.toml (uv managed)
	•	README.md

3) CLI-Tool Design (so würd ich’s machen)

Grundprinzip

Ein CLI, das sich anfühlt wie yt-dlp/ffmpeg: simple Defaults, aber starke Flags.

Minimaler Aufruf
	•	yt-transcript <URL>

Sinnvolle Flags (nicht zu viele)

Output
	•	-o, --out <path> Output-Datei oder Ordner
	•	--format md|txt|srt (Default: md)
	•	--timestamps none|start|range (Default: start)
	•	--hh (Zeitformat hh:mm:ss)

Language
	•	--lang de,en (Default: de,en)
	•	--prefer manual|auto (wenn du unterscheiden willst)

Fallback Steuerung
	•	--no-fallback (nur YouTube, kein STT)
	•	--force-stt (immer STT, auch wenn YouTube vorhanden)
	•	--keep-audio (Audio behalten statt löschen)

OpenAI
	•	--openai-model <name> (default sinnvoll vorbelegen)
	•	--openai-key-env OPENAI_API_KEY (damit es aus env kommt, nicht aus params)

Batch
	•	--urls-file urls.txt (jede Zeile eine URL)

Metadata/Obsidian
	•	--frontmatter (default on)
	•	--tags youtube,transcript
	•	--vault-path <path> (optional: direkt ins Obsidian Vault schreiben)

Exit-Codes (profi, aber hilfreich)
	•	0 success
	•	10 no transcript and fallback disabled
	•	20 yt-dlp failed
	•	30 openai stt failed

Logging
	•	-v/--verbose (zeigt Steps + Zeiten)
	•	normal: nur “Saved …”