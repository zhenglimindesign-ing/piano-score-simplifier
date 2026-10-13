# Submission handoff: score-simplifier

[中文](SUBMISSION.zh-CN.md)

Status: locally prepared review candidate. No official draft, review, publication, release or tag was created or changed.

## OpenAI

Open https://platform.openai.com/plugins → Create plugin → Skills only. Upload the complete candidate ZIP. Review the generated `.codex-plugin/plugin.json`, listing fields and skill product targeting. The package already includes square icons, bounded descriptions, three starter prompts, dependency disclosure and local data-handling documentation. ZIP-only skills have optional listing URLs; do not invent a published privacy URL. Identity verification, Apps Management write access, policy attestations and portal safety/security scans remain manual. Portal conversion and directory installation are NOT VERIFIED.

The core local workspace workflow is scoped to CODEX in agents/openai.yaml. The official migration guidance asks developers whose core value requires local execution or arbitrary local-file access to contact their OpenAI partner before submitting. Confirm this eligibility before review; no backend was added.

## Claude

Use https://claude.ai/directory/manage → Submit new → Plugin bundle. Repository: zhenglimindesign-ing/piano-score-simplifier; plugin path: directory-plugins/score-simplifier; proposed local branch: codex/distribution-prep-20261013. This branch is not pushed. Review and publish the candidate source through the project’s source/distribution workflow first; do not submit the private maintenance repository. Choose the intended owning organization, confirm paid-plan/role eligibility and connect a GitHub account with push access.

The [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy) section 1.F has a broad prohibition on querying/extracting memory, history and user-generated/uploaded files. Its applicability to expressly user-authorized processing in skills-only plugins is unresolved here. This plugin uses supplied material, so obtain directory clarification before marking it ready for review. Section 3.A also requires an accessible privacy policy where user data is collected or a remote service is used; PRIVACY.md is a reviewable draft, not a published URL. Supply your contact, age-audience answer and three examples, run portal Validate, resolve blocking findings, and accept terms yourself. Claude model-level behavior in an authenticated isolated config is NOT VERIFIED; local installation and component discovery do pass.

## skills.sh

The existing public source is already discoverable by repository URL and installs completely with telemetry disabled. Public keyword search/indexing was not available in this run. The FAQ describes telemetry-based indexing; this verification intentionally sent no install telemetry. No official submission form was found for this path. Installation requires no push of this candidate wrapper. Do not mistake a CLI install for a search listing or official approval.
