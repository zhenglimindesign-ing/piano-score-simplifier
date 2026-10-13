# PDF intake, delivery and work checkpoints

Read this reference for PDF sources, graphical delivery or a stage budget checkpoint. The helpers are read-only checks; they do not provide OMR or an automatic PDF arranger.

## Intake

```sh
python scripts/preflight.py --input SOURCE.pdf --score-kind voice_piano --delivery reduced_pdf
```

The agent chooses flags from the source and request; the user need not learn them. The helper reports the source SHA256, page count and up to three sampled pages. Image resources and extracted text only indicate whether a scan is likely. They do not establish readability, staff roles or correct notes. Render and view representative pages using the available local PDF tools; confirm source roles and protected material. A `voice_piano` declaration protects voice and lyrics conceptually, not by automatic transcription.

Check a coherent phrase internally, including melody, bass, accidentals, rests, ties and tuplets, before full processing. Keep any OMR result as a candidate until notation and source comparison agree. If a probe cannot support reliable notation, report its localized failure and select a mapped manual/graphical route within the request, or propose a concrete change of scope when necessary. A complete delivery can follow an internal probe without waiting for the friend to play it.

The current core accepts one piano MusicXML part. A PDF containing voice, other instruments or complex notation requires separately mapped source preparation; metadata intake is not proof of support for arranging those parts.

## Delivery contract

| ID | What appears on the page | Editable score and playback |
|---|---|---|
| `annotated_pdf` | Original notes remain, with omission markings | No complete editable score promised; optional diagnostic clips |
| `reduced_pdf` | Selected glyphs are actually erased; whole systems are repaginated | No complete editable score promised; optional diagnostic clips |
| `editable_score` | Canonical notation is re-engraved with omitted notes removed or replaced by rests | Complete MusicXML and checked MIDI for the declared full/phrase scope |

Explain these differences using the same source phrase when the requested result is ambiguous. Do not require three mockups when the user's choice is already clear. Preserve scans and earlier versions. Label excerpt files with their actual page/system/bar and excluded voices or performance features. A reduced PDF is a usable practice artifact, not evidence of calibrated L3 or complete semantic transcription.

## Local graphical record guard

Before erasing glyphs, source-check the affected material and normalize its physical noteheads, tie endpoints and accidental dependencies. `--pdf-edit-records RECORD.json` binds checks to the original `--input` hash. It catches duplicate/shared printed heads being treated as independent omissions, dangling/incorrect ties and missing accidental transfers. It does not read raw OMR or repair pixels.

Minimal record structure:

```json
{
  "source_sha256": "SHA256 of original PDF",
  "heads": [{"id": "h1", "page": 1, "bounds": [10, 20, 12, 8], "pitch": 60}],
  "edits": [{"id": "h1"}],
  "ties": [],
  "removed_tie_ids": [],
  "accidental_dependencies": [],
  "accidental_transfers": []
}
```

Bounds are `[x, y, width, height]` in the same page-image coordinate system. Heads overlapping at intersection-over-union >= 0.8 require source review and consolidation into one physical head record; do not create an extra rest for a duplicate recognition. Ties have `id`, `start`, `stop`; verify pitches and endpoints against the printed curve. Accidental dependencies/transfers have `from`, `to`, `sign`. Record checks remain scoped to supplied records, with source fidelity and musical acceptance `NOT_RUN`.

## Stage budget

```sh
python scripts/preflight.py --budget-state work/stage.json
```

```json
{
  "stage": "pdf_probe",
  "observed": {"elapsed_minutes": 8, "input_tokens": 50000, "cached_input_tokens": 40000, "output_tokens": 2000},
  "limits": {"elapsed_minutes": 20, "uncached_input_plus_output_tokens": 50000},
  "repair_attempts": 1,
  "gate_status": "FAIL"
}
```

Record observed stage deltas from available runtime evidence. Subtract a baseline from cumulative counters; after a reset or missing data, retain unknown values. `input_tokens` includes cached input. The helper computes uncached input plus output; reasoning output is already included in output. This number is neither account quota usage nor a monetary price. Wall time is not active human labor. Keep reusable setup/development separate from recurring per-score work.

For `pdf_probe`, the default elapsed checkpoint is 20 minutes; other stages have no implicit time limit. Token limits are optional and explicit. Reaching a declared checkpoint, or failing the same gate after two repairs, returns `REPLAN_METHOD`: retain the best candidate, stop repeating that method, localize the issue and continue independent authorized work. A passed repair is not blocked solely because two attempts ran. Changing delivery, musical identity, paid infrastructure or materially increasing cost needs a concrete user decision; ordinary changes of implementation do not require repeated permission.

Preflight exit codes: 0 means the read-only inspection completed, not score acceptance; 1 means an input/record error; 2 means graphical record checks failed; 3 means a budget checkpoint calls for replanning this method. The MusicXML pipeline also accepts `--budget-state` and refuses a budget-exhausted run before creating its output directory. These helpers do not monitor or change account billing.

## Review evidence

Separate source/notation review, MIDI event comparison, engine readback, audio data checks, actual audio analysis and human audition/playing. No audio-analysis channel means no agent listening claim. Preserve `NOT_RUN` for unperformed experience checks. Verify time-modified rests and shared-key sustained notes early; engine-specific articulation is an explicit difference, never a reason to relax notation checks silently.
