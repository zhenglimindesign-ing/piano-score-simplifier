# Install the skill and verify your first run

[中文](INSTALL.zh-CN.md) · [Usage guide](../README.md)

Score Simplifier handles solo-piano scores with an established source and permission basis. Start with a short, readable score and verify that your chosen host can deliver files. MusicXML/MXL can enter inspection directly; PDFs first need transcription and source checks.

## 1. Obtain the complete skill folder

Score Simplifier is the public project name; the current skill ID and install-folder name remain `piano-score-reduction` for compatibility.

Download `piano-score-reduction-<version>.zip` from the [v0.3.7 release](https://github.com/zhenglimindesign-ing/piano-score-simplifier/releases/tag/v0.3.7), then extract it. Use its complete `piano-score-reduction` folder. If you received a repository archive, use `skills/piano-score-reduction` instead and copy the root `LICENSE` and `NOTICE` into the installed folder. Keep these contents together:

```text
piano-score-reduction/
  SKILL.md
  requirements.txt
  LICENSE
  NOTICE
  scripts/
  references/
  assets/
```

Copying only `SKILL.md` omits scripts and the engraving style. Preserve the old installation and score outputs when updating; use a separate test project if the installed version is uncertain.

## 2. Place or load it in your host

**Evidence version:** the host trials below are inherited v0.3.6 evidence (with earlier full-workflow evidence identified). v0.3.7 has new local package/runtime checks; independent v0.3.7 Claude Code / Claude web / ChatGPT Work trials were NOT_RUN. See the [current evidence matrix](SUPPORT.en.md).

| Host | Installation / entrypoint | Verified boundary |
|---|---|---|
| Codex local project | Put the folder at `.agents/skills/piano-score-reduction/`, open that project and name the skill in your request | Codex CLI 0.145.0 on the recorded macOS configuration completed bilingual first generation, localized revision, retention and negative-input tests |
| Claude Code local project | Put it at `.claude/skills/piano-score-reduction/`, open that project and request the skill | Claude Code 2.1.218 on the recorded macOS configuration completed the fixed bilingual protocol and final v0.3.6 affected checks from the loaded project skill with MuseScore 4.7.5 |
| Claude web | Customize → Skills → Add skill → Upload skill; select the portable ZIP and enable the skill, then attach a score in a dedicated chat | Fixed v0.3.4 native installation and bilingual workflow verified with a declared adapter; final v0.3.6 exact temporary source independently passed layout/revision/retention/unsupported-input checks with MuseScore3 3.2.3 and no adapter. The existing native installation was preserved |
| ChatGPT Work execution | Attach the complete portable ZIP and authorized score in a dedicated Work chat; explicitly request extraction and actual execution | Fixed v0.3.4 bilingual workflow and exact final v0.3.6 affected checks independently passed in temporary Work execution on Ubuntu 24.04.3/Python 3.12.14/MuseScore 4.3.2 AppImage, including downloaded actual files, scoped revision, retention and unsupported input. Native persistent plugin installation and other ChatGPT modes were not tested |

Project paths above are relative to the project you open, not to the extracted skill folder. Account features and permissions belong to each host. One local CLI configuration does not establish every desktop sandbox or cloud route.

## 3. Let the agent check dependencies

Send this where the skill is loaded:

```text
Use the installed piano-score-reduction skill.
Run preflight in the actual execution environment, checking Python,
the pinned dependencies, MuseScore and PDF page inspection.
Handle ordinary missing dependencies in an isolated environment.
Preserve my inputs and earlier versions. Explain access issues that need me.
A program path alone is not proof of successful engraving.
```

Execution needs Python 3.10+, the skill's pinned Python requirements, MuseScore for PDF engraving and `pdftoppm` for page inspection. Audio export is optional. The agent owns routine environment work; you provide the score and musical goal.

Complete local tests used Python 3.14.0, lxml 6.1.3, mido 1.3.3, MuseScore 4.7.5 and Poppler. Claude web used Python 3.12.3 and official Ubuntu MuseScore3 3.2.3. The detector now includes `mscore3`. v0.3.6 includes an MS3 native-score/style/reload PDF path, with version-matched styles and retained logs/intermediates; canonical XML and internal MIDI stay authoritative. Its actual extracted macOS MuseScore 4.7.5 checks and Claude Code loaded-skill checks pass. Claude web independently passed the integrated MS3 path without an adapter; actual PDFs, XML, MIDI and retained parent versions were audited. ChatGPT Work final checks also pass with its explicitly selected MuseScore 4.3.2 AppImage launcher. Fixed v0.3.4 full bilingual host acceptance and final-version affected checks are recorded separately.

On macOS a workspace sandbox may prevent MuseScore PasteBoard/XPC access. Keep the actual error and resolve the host's renderer permission. Local tests used an invocation allowing rendering; Claude Code tool allowances were invocation-scoped, with no global settings change.

Optional macOS commands from the project root after Codex installation:

```sh
python3 -m venv work/venv
work/venv/bin/python -m pip install -r .agents/skills/piano-score-reduction/requirements.txt
work/venv/bin/python .agents/skills/piano-score-reduction/scripts/preflight.py
```

For Claude Code use `.claude/skills/`; when working directly from the repository use `skills/`. These commands inventory dependencies, not actual engraving or file delivery.

## 4. Generate, open and revise one score

Provide a short original or appropriately authorized solo-piano score. Prefer MusicXML for the first environment check, then send:

```text
Use the installed piano-score-reduction skill on this score.
Make an L2 Mini with a coherent ending, preserving the main melody
and easing the accompaniment. Retain my original file.
Give me downloadable PDF, MusicXML, MIDI, arrangement notes and QA.
Actually render and inspect every PDF page; record checks not performed.
```

Open the downloaded PDF, import the XML in notation software and open the MIDI. Then request a concrete revision, for example:

> In bar 6, reduce the left-hand chord stretch while keeping the melody and all other bars unchanged. Save a new version and retain the previous one.

Confirm both versions remain available, the change stays within the requested bars and the report names musical losses. Malformed or unsupported notation should also produce an honest retained error report.

## Read the result and resolve problems

| Result / symptom | What to do |
|---|---|
| `REVIEW_REQUIRED` | Technical checks passed; review the changes and try the arrangement. This does not certify musical quality or an examination grade |
| `FAIL` | A recorded check failed, including poor page layout; ask the agent to repair it and retain the failed version |
| `INCOMPLETE` | Required checks could not run or notation is unsupported; read the missing check and keep the source intact |
| `ERROR` | Execution, input or plan validation failed; provide the actual error for correction |
| Instructions but no downloadable files | Loading instructions did not establish execution; check the host runtime, renderer and file-delivery route |

Human listening/playing and grade calibration are separate from file checks and remain unverified. They are nonblocking for the experimental first release. No guarantee applies to every score, notation feature, hand size or host configuration.

The [AI instructions](../skills/piano-score-reduction/SKILL.md) and [execution reference](../skills/piano-score-reduction/references/workflow.en.md) explain source handling, supported notation and version retention. Describe a difficulty naturally; no ability questionnaire or engineering thresholds are required.
