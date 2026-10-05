# Distribution content and publication state

[中文](DISTRIBUTION.zh-CN.md) · [Host evidence](SUPPORT.en.md)

`DISTRIBUTION.json` is an immutable **CONTENT_SNAPSHOT**: implementation version, explicit public file inventory, byte counts, SHA-256 hashes and an inventory digest. It describes the current listed content, not whether a release was published or accepted. Regenerate it when any listed file changes. It must not carry stale file hashes or a false unpublished claim.

`PUBLICATION.json` is a separate receipt written after remote verification. It records the public repository, immutable release/tag commit, release assets and verified hashes. The receipt is excluded from the content inventory and source ZIP, as is the inventory's own JSON, to avoid circular hashes and post-publication mutation. A receipt-only commit after the release tag may change main without changing any inventoried byte; the tag and uploaded assets stay immutable. The release asset manifest is byte-identical to the tagged root manifest.

The portable ZIP contains only the complete compatible skill folder and project LICENSE/NOTICE. The source ZIP contains the explicit public source, paired documentation and the public October example, plus its manifest. Private scans, repository history, acceptance logs, credentials and unrelated local outputs are excluded. The October reference is our own transcription/render; rights and embedded-font notices accompany it. This workflow preserves the separate private maintenance repository and never changes an existing release's assets.

A valid hash proves content identity, not human playing, musical acceptance, calibrated grading or full host support. See each example QA and the route-specific host evidence.
