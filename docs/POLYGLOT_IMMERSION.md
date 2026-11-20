# Reaper Polyglot Immersion

## Purpose

Polyglot is a local-first learning subsystem inside Reaper. It turns the immersion workflow into persistent, inspectable data rather than a collection of reminders:

- separate profiles for any number of target languages, each with a native/explanation language, an approximate CEFR level, a goal and a daily time budget;
- an offline content library for texts, dialogues, stories, articles and references to audio/video files;
- phrase cards that preserve translation, context, pronunciation hints, source and tags;
- due-date scheduling with a compact ease/interval model and a review history;
- a daily plan that shifts time between input, reading, review and output according to level and due-card pressure;
- a content queue ranked around the requested 70–90% known-token band;
- session logging, seven-day progress reporting and JSON export.

This is an executable first implementation, not a claim that a desktop language tutor, speech AI or automatic translator already exists.

## Storage and privacy

The default SQLite database is:

- Windows: %USERPROFILE%\.reaper\polyglot.sqlite3
- Linux/macOS: ~/.reaper/polyglot.sqlite3

Set REAPER_POLYGLOT_HOME to choose another directory, or pass --db PATH after reaper polyglot.

The subsystem performs no network requests, web scraping, telemetry or automatic uploads. Imported content remains in the local database. A media path is stored as a reference; audio/video is not copied or played by the current implementation. Keep copyright and source permissions in mind when importing material.

## Quick start

~~~sh
# Create a target-language profile
reaper polyglot init English --native Russian --level A0 \
  --goal "comfortable everyday conversation" --minutes 45

# Add a transcript, article, dialogue or subtitle file
reaper polyglot content add ./lesson-one.srt --kind dialogue --level A1 \
  --media ./lesson-one.mp3 --source "course lesson 1"

# Add useful phrases in context
reaper polyglot phrase add "Could you say that again?" \
  --translation "Не могли бы вы повторить?" \
  --context "A polite request when you did not catch a sentence" \
  --pronunciation "kəd juː seɪ ðæt əˈɡen" --tag conversation

# See today's balanced routine and available material
reaper polyglot plan
reaper polyglot suggest
reaper polyglot content list

# Review due phrases, then record speaking/writing practice
reaper polyglot review
reaper polyglot practice --mode speaking --minutes 8
reaper polyglot report

# Add another language without replacing the first
reaper polyglot init 日本語 --native Russian --level A0 --minutes 30
reaper polyglot --target 日本語 plan

# Back up one profile as portable JSON
reaper polyglot --target English export --output english-study.json
~~~

Without --target, commands work when exactly one profile exists. If several languages are configured, select one explicitly.

## Daily learning loop

1. Import a short item that is interesting and mostly understandable. Supported text inputs are UTF-8 .txt, .md, .srt and .vtt; subtitle timestamps and cue numbers are stripped.
2. Add a small number of reusable phrases, including a translation and the original context. Attach pronunciation hints, source labels and tags where useful.
3. Run reaper polyglot plan. A0–A2 profiles bias the schedule towards comprehensible listening/reading. B1–C2 profiles reserve more time for output and conversation. Pending reviews increase the review share, within a bounded limit.
4. Run reaper polyglot review. The native-language meaning is shown first; recall the target phrase aloud or in writing, reveal the answer, then grade recall from 0 to 5.
5. Record speaking, writing, shadowing or conversation with practice or session. The score is a self-assessment, not an automatic language evaluation.
6. Use suggest to choose imported material and report to check whether practice is regular.

The generated plan is an allocation of minutes, not a timer or a guarantee of a particular learning outcome.

## Comprehensibility estimate

A reviewed phrase contributes its tokens to the profile's known-term set. For every imported item the engine calculates the share of body tokens present in that set and flags items between 70% and 90%. This is a transparent heuristic:

- it is not a CEFR classifier, semantic understanding test or proof that the learner understands 80% of a text;
- context, inflection, polysemy and cognates are not modelled;
- Chinese/Japanese/Korean text currently receives a rough character-level estimate because morphological segmentation is not bundled;
- the estimate improves as phrase cards are reviewed, but should be combined with the learner's own comprehension judgement.

No text is silently translated or sent to an external service.

## Spaced repetition

New cards are due immediately. The learner assigns a rating:

| Rating | Meaning | Scheduling effect |
|---:|---|---|
| 0–2 | Failed or very difficult recall | Reset to one day; lower ease; count a lapse |
| 3 | Recalled with effort | Continue with a conservative interval |
| 4 | Correct and reasonably easy | Normal interval growth |
| 5 | Immediate, confident recall | Slightly increase ease and interval growth |

The first successful review is scheduled after one day, the next after three days, then the previous interval is multiplied by the card's ease factor. Ease is bounded to avoid runaway intervals. This is a compact, explainable scheduler rather than a claim of a scientifically optimal memory model.

## Command reference

| Command | Purpose |
|---|---|
| reaper polyglot init LANGUAGE --native LANGUAGE | Create or update a profile |
| reaper polyglot profile | List configured profiles |
| reaper polyglot content add FILE | Import transcript or reading material |
| reaper polyglot content list | List material and estimated coverage |
| reaper polyglot phrase add PHRASE --translation TEXT | Create a contextual review card |
| reaper polyglot phrase list --due | Show cards due now |
| reaper polyglot plan | Generate the daily routine |
| reaper polyglot suggest | Rank material by estimated comprehension |
| reaper polyglot review | Run interactive phrase recall |
| reaper polyglot practice --mode speaking | Record an output practice session |
| reaper polyglot session --minutes N --mode reading | Record any completed session |
| reaper polyglot report | Show progress and recent activity |
| reaper polyglot export --output FILE | Export profile data as JSON |

Use reaper polyglot COMMAND --help for command-specific options. The global --db and --target options go immediately after polyglot.

## Current implementation boundaries

The current Python reference implementation supports persistence, import, contextual phrase review, a basic adaptive plan, reporting and export. The following require later adapters or modules and are intentionally not faked:

- media playback, subtitle/audio synchronisation and waveform/transcript alignment;
- speech-to-text, pronunciation scoring and text-to-speech;
- automatic translation, LLM feedback and dialogue simulation;
- language-specific morphological tokenizers and validated CEFR placement tests;
- a native C17 implementation and a dedicated Reaper Studio study interface.

These boundaries keep the subsystem useful offline and prevent false claims about capabilities that are not implemented.
