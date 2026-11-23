# Reaper non-audio runtime boundary

Reaper's runtime, native compiler, IDE, language services and optional integrations are text/program tooling. The Polyglot subcommand is now explicitly text-only.

## Removed from the active interface

- Audio and video content kinds are not accepted by Polyglot.
- The content importer no longer accepts an audio/video media path.
- Listening, speaking, shadowing and conversation session modes are not accepted.
- Phrase cards no longer accept or display pronunciation/audio guidance.
- Review prompts ask for a recalled or written answer; they do not request spoken output.
- Polyglot study plans use reading, writing, analysis, review and reflection.

Subtitle files (`.srt` and `.vtt`) remain supported as text transcript inputs. They are parsed as text; Reaper does not open or play the associated media.

## Existing local databases

The historical SQLite columns `content.media_path`, `phrases.pronunciation` and `profiles.phonetic_focus` are retained as inactive compatibility columns so that an upgrade does not rewrite or discard user-owned databases. The active APIs, importer and CLI no longer read or write them. Reaper does not delete any old media files referenced by an existing database.

## Other Reaper modules

The `impact.sound` lexicon is static written vocabulary for semantic categorization; it is not an audio device, player, recorder, synthesizer or sound-effect engine. There is no audio output/input service or system notification sound path in Reaper.

## Allowed audio repositories

Audio device and kernel sound facilities belong in DuckOS. Creative audio production/sample playback remains in VentuSample. Reaper must not introduce dependencies on either sound subsystem.
