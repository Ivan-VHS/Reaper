# Reaper Polyglot — language immersion workspace

## Purpose

reaper polyglot adds a local-first learning workspace to Reaper. The learning loop is built around understandable input and contextual phrases rather than isolated vocabulary lists:

1. Hear and see a short item with transcript, captions, or visual context.
2. Estimate whether its known-vocabulary coverage is near the learner's chosen 70–90% working range.
3. Save useful phrases with meaning, scene/context, pronunciation, audio reference, and a personal example.
4. Revisit those phrases through deterministic spaced repetition.
5. Retell, record, or discuss the material and log learner-reported confidence and corrections.

The system can create a profile for any target-language name. Language codes and Unicode script detection provide better defaults for common writing systems; an explicit script setting is available when automatic detection is insufficient.

## Install and create a workspace

The feature ships inside the existing Python package and has no third-party runtime dependency.

~~~bash
python -m reaper polyglot init \
  --target-language Spanish \
  --code es \
  --support-language Russian \
  --level A0 \
  --goal "Everyday conversation" \
  --daily-minutes 45 \
  --comprehension-target 0.80
~~~

By default the workspace is stored at ~/.reaper/polyglot.json. Use --store PATH on any command to choose another file. Initialization refuses to overwrite an existing workspace.

The --code option accepts an ISO-style language code such as es, ja, zh, ko, ar, hi, th, ru, or uk. Script can be set explicitly with --script latin|cyrillic|arabic|devanagari|han|japanese|hangul|thai|other. With --script auto, the code/name mapping chooses a starting script family.

## Four-pillar daily plan

~~~bash
python -m reaper polyglot plan
python -m reaper polyglot plan --date 2026-11-20
~~~

The requested daily budget is split deterministically between:

| Pillar | Default share | Practice |
|---|---:|---|
| Audio and visual input | 30% | Short audio/video with transcript, captions, or scene context |
| Contextual reading | 25% | Read a short passage and capture recurring constructions |
| Contextual retention | 20% | Review due phrase cards and create a personal example |
| Speaking and feedback | 25% | Retell, monologue, role-play, and record one correction |

The allocation always sums to the requested daily-minute budget. The supported budget is 15–240 minutes. The daily plan is a suggested routine, not a timer or a claim that Reaper can observe background activity.

## Comprehensible-input estimator

Add a content sample and Reaper stores an estimated known-unit coverage:

~~~bash
python -m reaper polyglot analyze --text "Hola, ¿qué tal? Me llamo Ana."
python -m reaper polyglot add-content \
  --title "First greetings" \
  --text "Hola, ¿qué tal? Me llamo Ana." \
  --source "Beginner dialogue" \
  --audio-ref "media/greetings.mp3"
~~~

The estimator compares text units with saved phrase vocabulary. For spaced writing systems it uses lexical tokens; for compact writing systems such as Han, Japanese, Hangul, and Thai it uses a character-coverage approximation and saved phrase matches. It classifies an item as too_hard, comprehensible, or too_easy relative to the chosen target (default 0.80, configurable from 0.70 to 0.90).

**This is a vocabulary-coverage heuristic, not a comprehension test.** It cannot reliably infer a learner's understanding, idiom knowledge, grammar knowledge, or cultural interpretation. Use the result to shortlist material, then confirm the fit by listening/reading and summarizing the meaning. Japanese text is detected as Japanese when kana is present alongside Han characters; kanji-only samples can be indistinguishable from Chinese.

## Contextual phrase cards

~~~bash
python -m reaper polyglot add-phrase \
  --text "¿Qué tal?" \
  --meaning "How are you? / How's it going?" \
  --context "Casual greeting between friends" \
  --pronunciation "keh tal" \
  --personal-example "¿Qué tal estuvo tu día?" \
  --source "Dialogue 01" \
  --tags greeting conversation \
  --frequency-rank 120
python -m reaper polyglot due
python -m reaper polyglot review --id phrase-000001 --rating good
~~~

Cards retain the original expression, meaning, context, source, optional audio reference, pronunciation note, learner-written example, tags, and optional frequency rank. The rank is user-supplied; Reaper does not claim to ship a universal frequency corpus.

Review ratings are again, hard, good, and easy. Intervals use a simple SM-2-inspired schedule with a bounded ease factor. The date can be injected for reproducible planning/tests using --date YYYY-MM-DD. Reaper does not force a review when a card is not yet due.

## Study log, progress, and profile tuning

~~~bash
python -m reaper polyglot log \
  --pillar audio_visual \
  --minutes 20 \
  --comprehension 0.82 \
  --notes "Understood the main idea on the second listen"

python -m reaper polyglot log \
  --pillar speaking_feedback \
  --minutes 10 \
  --oral-confidence 3 \
  --notes "Retold the scene; review past tense"

python -m reaper polyglot status
python -m reaper polyglot configure \
  --level A2 \
  --daily-minutes 50 \
  --comprehension-target 0.85 \
  --romanization-bridge off
~~~

The phase label (setup, sound_foundation, comprehensible_input, guided_output, authentic_content, automation) is based on cumulative logged exposure hours. It is a planning heuristic only; it does not predict CEFR level or guarantee a learning timeline. The profile's level remains learner-controlled.

All commands support --json for structured output. For example:

~~~bash
python -m reaper polyglot status --json
python -m reaper polyglot due --json
~~~

## Python API

The same engine is available to scripts:

~~~python
from reaper import PolyglotWorkspace

workspace = PolyglotWorkspace.create(
    "my-spanish.json",
    target_language="Spanish",
    language_code="es",
    support_language="Russian",
    daily_minutes=45,
    comprehension_target=0.80,
)

workspace.add_phrase(
    "¿Qué tal?",
    "How's it going?",
    context="Casual greeting between friends",
    pronunciation="keh tal",
    personal_example="¿Qué tal estuvo tu día?",
)
estimate = workspace.analyze_text("Hola, ¿qué tal? Me llamo Ana.")
plan = workspace.daily_plan()
workspace.save()
~~~

PolyglotWorkspace.load(path) opens an existing workspace. configure(...), add_content(...), review_phrase(...), log_session(...), due_phrases(...), and status(...) are also exposed. PolyglotError represents invalid profiles or learning operations.

## Script and pronunciation adaptation

The profile can mark Latin, Cyrillic, Arabic, Devanagari, Han, Japanese, Hangul, Thai, or another script family. Guidance is added for script-specific reading risks (for example, kana/kanji pairing, vowelled Arabic examples, Hangul sound changes, and stress marks). Tonal-language profiles default to tone-aware pronunciation notes and daily-plan reminders.

Romanization is treated as a temporary bridge, represented by a profile setting that the learner can turn off as native-script reading improves. Reaper stores pronunciation notes; it does not currently synthesize speech, fetch media, transcribe audio, identify phonemes, score tones, or recognize spoken output.

## Boundaries and future adapters

- Workspace data is a versioned UTF-8 JSON file, written atomically. It remains local; this feature does not upload a learner's notes or recordings.
- audio_ref is metadata pointing to a user-managed audio asset. Reaper does not resolve or play that file.
- Speaking practice is planned and logged through self-assessment and correction notes. Automated pronunciation feedback requires a separately configured ASR/pronunciation provider and is not claimed by this implementation.
- Content recommendations are heuristic and use saved vocabulary. There is no bundled licensed corpus, frequency database, dictionary, translator, or content downloader.
- The four pillars and exposure-hour phases are configurable planning guidance, not a medical or cognitive assessment and not a promise of fluency.

The module is deliberately kept separate from the .rpr language grammar. It is a first-party Reaper application/library subsystem accessible through the CLI and Python API; no new language keywords or implicit filesystem/network effects are introduced into ordinary Reaper programs.
