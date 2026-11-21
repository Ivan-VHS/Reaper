# Mental Wellbeing Awareness reference

Reaper exposes an offline reference catalogue through its CLI:

```sh
python -m reaper wellbeing --catalog
python -m reaper wellbeing --topic antidepressant-myths
python -m reaper wellbeing --topic support-pyramid --json
```

The runtime only reads a bounded, versioned local JSON bundle. It does not execute a symptom checker, infer mood from programs or telemetry, or provide medication advice. See `reaper/wellbeing.py` and `tests/test_wellbeing.py`.


## Source and evidence boundary

Source: [ебаут — «Депресія — тема табу? Ознаки депресії, міфи довкола антидепресантів, як допомогти собі»](https://www.youtube.com/watch?v=brNbnipJ-i8), published 2025-11-23, duration 1:20:01. The supplied transcript contains only 00:00–00:07:55 and 01:17:16–01:19:53. The large middle portion is missing. Each topic carries evidence status and timestamp offsets. The 280-million figure is recorded as a claim voiced in the episode, not as a current verified statistic.

## Product safety contract

- Education and destigmatisation only; no diagnosis, screening, risk score, treatment plan or symptom interpretation.
- No inference from CPU, device, audio, project, work-pattern or user telemetry.
- No medication, dosage, start/stop or substitution instructions. The episode's closing advice says medication should be taken only by a psychiatrist's prescription.
- The speakers' experiences and the Stutz pyramid are attributed as personal statements, not medical protocols.
- Missing transcript sections remain explicitly unavailable. The title's reference to antidepressant myths is not evidence of what was said about those myths.

## Data contract

`data/wellbeing/depression-awareness.v1.json` follows `schemas/wellbeing-reference.v1.schema.json`. `evidence_status=insufficient_transcript` means a topic is named by the video title but cannot be summarised from the supplied excerpts.
