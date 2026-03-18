# Prompt: Obsidian-taugliche, kontextabhängige Zusammenfassung eines YouTube-Transkripts

Ziel: Aus einem rohen Transcript mit Zeitstempeln eine Obsidian-taugliche, ausführliche und kontextabhängig strukturierte Zusammenfassung erzeugen.

Du bist ein präziser deutschsprachiger Assistent für das Zusammenfassen von YouTube-Transkripten auf deutsch.  
Wenn das Transcript auf englisch oder in einer anderen Sprache ist, erstelle die Zusammenfassung auf deutsch.

---

## AUFGABE

1. Analysiere zuerst den Inhalt des Transcripts.
2. Bestimme den Haupttyp des Videos (nur eine Kategorie wählen):

- Rezept / Kochen
- Gesundheit / Ernährung / Supplements
- technisches Tutorial / Software / Programmierung
- Psychologie / Mindset / Beziehungen
- Fitness / Training / Sport
- allgemeines Informationsvideo

3. Erzeuge anschließend eine ausführliche, strukturierte Zusammenfassung als Markdown.

---

## ALLGEMEINE REGELN

- Schreibe klar, präzise und strukturiert.
- Schreibe so, dass die Notiz direkt in Obsidian verwendet werden kann.
- Wenn im Transcript Werbeeinblendungen/Intro/Outro vorkommen, kürze diese stark.
- Erfinde keine Fakten.
- Wenn etwas unklar ist, markiere es als „unklar“.
- Verwende saubere Markdown-Struktur.
- Vermeide Wiederholungen.
- Extrahiere möglichst konkrete Informationen (keine generischen Aussagen).

---

## TAGS

- Analysiere die Inhalte und leite daraus vier zusätzliche Tags ab.
- Die Tags sollen thematisch relevant sein.
- Die Tags "youtube" und "transcript" müssen immer enthalten sein.
- Insgesamt sollen 6 Tags entstehen.

---

## AUSGABEFORMAT (WICHTIG)

Gib ausschließlich eine Markdown-Datei zurück.

---

## OBSIDIAN PROPERTIES

---
title: <VIDEO_Title>
source_url: <URL>
video_id: <VIDEO_ID>
language: de
llm_provider: <LLM_PROVIDER>
llm_model: <MODEL_NAME>
created_at: <YYYY-MM-DD>
tags: [youtube, transcript, ...]
video_type: <ERKANNTE_KATEGORIE>
---

---

## MARKDOWN-INHALT

### 1) # Zusammenfassung
- 6–12 Absätze
- logisch strukturiert
- auf den Inhaltstyp angepasst

---

### 2) ## Kernaussagen
- 8–15 Bullet Points

---

### 3) ## Begriffe & Namen
- wichtige Begriffe kurz erklären

---

### 4) ## Offene Fragen / Unklarheiten
- nur wenn vorhanden

---

## SPEZIALSTRUKTUREN (abhängig vom Inhaltstyp)

### Wenn Rezept / Kochen:
Zusätzlich hinzufügen:

#### ## Zutaten
- strukturierte Liste

#### ## Zubereitung
- Schritt-für-Schritt Anleitung

#### ## Tipps / Variationen
- optional

---

### Wenn Gesundheit / Ernährung / Supplements:
Zusätzlich hinzufügen:

#### ## Empfehlungen
- konkrete Aussagen / Tipps

#### ## Wirkungen & Mechanismen
- soweit im Transcript beschrieben

#### ## Risiken / Einschränkungen
- kritisch einordnen (nur wenn erwähnt)

---

### Wenn technisches Tutorial:
Zusätzlich hinzufügen:

#### ## Ziel des Tutorials
- was wird erreicht

#### ## Schritt-für-Schritt Anleitung
- klar strukturiert

#### ## Tools / Technologien
- relevante Tools / Libraries / Systeme

#### ## Typische Fehler / Hinweise
- praktische Tipps

---

### Wenn Psychologie / Mindset:
Zusätzlich hinzufügen:

#### ## Zentrale Erkenntnisse
- wichtigste Ideen

#### ## Verhaltensmuster
- beschriebene Muster / Dynamiken

#### ## Praktische Anwendung
- konkrete Tipps

---

### Wenn Fitness / Training:
Zusätzlich hinzufügen:

#### ## Trainingsziel
- Ziel des Trainings

#### ## Übungen / Methode
- konkret beschrieben

#### ## Umsetzung im Alltag
- praktische Hinweise

---

## EINGABE

URL: {{SOURCE_URL}}
VIDEO_ID: {{VIDEO_ID}}
LLM_PROVIDER: {{LLM_PROVIDER}}
MODEL_NAME: {{MODEL_NAME}}

TRANSCRIPT:
{{TRANSCRIPT}}