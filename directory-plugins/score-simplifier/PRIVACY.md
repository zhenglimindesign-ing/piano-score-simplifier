# Data handling for score-simplifier

[中文](PRIVACY.zh-CN.md)

This package has no developer-operated backend, account database or bundled telemetry. The user’s chosen AI host processes conversation and supplied material under that host’s terms and settings. This document describes the bundled code; it does not promise how a host retains prompts or handles accounts.

**Inputs:** Authorized user-provided scores and declared arrangement instructions; new score outputs and QA records.

**Local storage:** Files are kept in the user-selected workspace or the host’s execution environment. The publisher does not receive them through the bundled code. Local records remain until the user removes them; host or cloud records follow the host’s own retention controls. A downloaded artifact is an export, not proof of persistent storage.

**Network:** The host may use requested public-source browsing. Reflection’s optional catalog refresh and explicit upgrade helper use GitHub; Score’s explicit schema preparation downloads hash-pinned W3C schema files. These helpers do not send candidate data, personal answers or score contents. No background refresh, automatic upgrade or outbound message is configured by this plugin. Installing Python dependencies contacts the package registry only when explicitly carried out.

**Control:** The user controls source scope, saving, exports and external actions. Do not attach private candidate, diary or score material to public issue reports. For support, use the public repository’s issue tracker with redacted or fictional examples. The publisher must separately confirm a reachable review contact and intended age audience before directory submission.
