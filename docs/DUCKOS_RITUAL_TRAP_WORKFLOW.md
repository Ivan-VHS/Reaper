# DuckOS Concrete Thump timing workflow

**Project:** Reaper  
**Related OS:** DuckOS  
**Maintainer:** Ivan-VHS  
**Status:** companion language example; no audio engine integration

## Purpose

DuckOS Concrete Thump can export a Reaper source timing helper. This example demonstrates Reaper as a small, inspectable systems-language tool in the existing DuckOS/Reaper process boundary. It calculates swung eighth-note offbeat markers on a sixteenth-note timing grid from BPM and swing values.

The helper does **not** load samples, synthesize sound, render audio, access an audio device, create MIDI, or control a DAW. Reaper remains a systems programming language and hardware development studio; this companion example does not change that product identity.

## Run the checked-in example

From the Reaper repository root:

~~~sh
python -m reaper --check examples/duckos_ritual_trap_grid.rpr
python -m reaper examples/duckos_ritual_trap_grid.rpr
~~~

For a DuckOS checkout with the Reaper submodule initialized:

~~~sh
duckos reaper check examples/duckos_ritual_trap_grid.rpr
duckos reaper typecheck examples/duckos_ritual_trap_grid.rpr
~~~

The DuckOS bridge runs static checks on a user-selected Reaper source file. It does not automatically launch the program, import samples or grant file/device access.

## Timing model

The helper treats the profile as a 4/4 sixteenth-note grid. A 50% swing setting is straight timing. Values above 50% delay alternating offbeats; the formula is explicit in the source and should be treated as a timing convention for this helper, not as a claim of exact hardware-MPC emulation.

For each offbeat index, the script reports a marker in milliseconds. These values are reference data for manual arrangement in an external audio application.

## DuckOS workflow

1. Open Mora → Concrete Thump.
2. Select the vocal tradition and chant/song sources independently.
3. Import only audio you own, have permission to use, or can verify as public-domain/licensed. Imported files can be auditioned, sequenced and rendered to a local four-bar WAV in the browser.
4. Save the profile and export the Reaper timing helper.
5. Run the DuckOS Reaper static check on the exported source; run typecheck where supported.
6. Open Reaper Studio separately to inspect or edit the generated language source.

## Boundaries and privacy

- Audio import is local and user initiated. No file is uploaded or transmitted.
- The browser profile stores rhythm settings and sample metadata only, not audio bytes. Re-select files after reopening Mora to preview them again.
- Sample files are limited to eight entries, 25 MiB each and 80 MiB total per open Concrete Thump session.
- The JSON profile export contains metadata, not embedded audio.
- Orthodox liturgical repertoire and East Slavic folk/seasonal/ceremonial repertoire are separate selectable source families. Combining them is an arrangement choice, not a claim that they are the same historical tradition.
- Reaper does not receive sample bytes or control the browser sequencer. Its helper only calculates timing markers.
- Native audio drivers, system mixing, MIDI integration, advanced synthesis, multitrack editing, waveform editing and hardware routing remain outside this companion workflow.
