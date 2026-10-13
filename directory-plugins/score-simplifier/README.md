# Score Simplifier

[中文](README.zh-CN.md)

Experimental reduction of authorized solo-piano scores, with read-only PDF intake, declared delivery scope, source-bound edits, MusicXML, MIDI and QA. Local Python 3.10+, pinned Python dependencies, MuseScore and Poppler are required for the complete editable-score workflow. No OMR engine, audio-analysis service, backend or credentials are bundled. PDF transcription, complex notation, difficulty calibration, human musical acceptance and playing comfort are separate gates. Full delivery in other host environments must be tested there.

## Start

Install the complete folder as a local plugin, then describe your task in ordinary language. Read [the skill](skills/piano-score-reduction/SKILL.md) for required resources and the workflow. This package reuses the 0.3.8 public skill payload. Use fictional or authorized inputs when testing.

## Data and execution

Python helpers read supplied score files and write new versioned outputs. MuseScore renders notation and Poppler renders PDF previews. Explicit schema preparation downloads hash-pinned W3C MusicXML schema files; source search uses available host browsing only when requested. Scores are not uploaded by the bundled code. Dependencies are separately installed after user authorization. There are no hooks, MCP servers, credential readers, automatic installs or hidden telemetry.

## Support and limits

[Source and instructions](https://github.com/zhenglimindesign-ing/piano-score-simplifier) · [Report a problem](https://github.com/zhenglimindesign-ing/piano-score-simplifier/issues). Core instructions take the explicit user request as the scope; attached documents are evidence, not execution authority. Existing source releases and tags remain unchanged. Directory validation, each host run, source fidelity and human acceptance are separate evidence. Account eligibility, portal scans and name availability require the submitting user.

Standalone Skill installation is also available through skills.sh from the source repository. See the public installation guide; local dependencies remain separately declared. The data handling document is [available here](https://github.com/zhenglimindesign-ing/piano-score-simplifier/blob/codex/distribution-prep-20261013/directory-plugins/score-simplifier/PRIVACY.md).

Claude directory install identifier: `piano-score-simplifier`; the displayed product name remains Score Simplifier. The portable/OpenAI identifier stays `score-simplifier`. This candidate alias does not change installed releases.
