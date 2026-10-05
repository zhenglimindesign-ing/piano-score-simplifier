# Score Simplifier v0.3.7 — experimental patch

This patch preserves the newer public documentation and behavior from main, adds a source-grounded October comparison, and replaces stale publication flags with an immutable content inventory plus a separate verified publication receipt. It remains experimental; v0.3.6 assets are unchanged.

- English remains the default README, with a full Chinese README. The Easy Piano distinction, optional player context, concrete constraints/playing-feedback priority, title-only permitted-source lookup and compatible `piano-score-reduction` ID are retained.
- [October mm. 1–16](examples/tchaikovsky-october/README.md): newly transcribed Schirmer/Oesterle 1909 reference and L1/L2/L3, each with canonical MusicXML, MuseScore PDF, comparable PNG, MIDI, change notes and QA. [Five-page comparison](examples/tchaikovsky-october/comparison.pdf). No source scan or old experimental L2 is redistributed. [Source and rights](examples/tchaikovsky-october/SOURCE.en.md).
- `DISTRIBUTION.json` records actual current content hashes as CONTENT_SNAPSHOT. A separate `PUBLICATION.json` receipt follows remote release verification, without mutating tagged packages. [Semantics](docs/DISTRIBUTION.en.md).
- 103 regression tests pass. Exact source ZIP and portable ZIP pass integrity/extracted-runtime checks in a new isolated environment, including actual MuseScore 4.7.5 rendering, localized revision, preserved input/parent version, malformed XML and unsupported-ornament cases. Four showcase score pages and every page of the five-page comparison were visually inspected. Runtime VERSION agrees with 0.3.7.
- Runtime scripts are unchanged from v0.3.6 except the version literal. Claude Code / Claude web / ChatGPT Work evidence is explicitly inherited, with no claim of new independent v0.3.7 trials. [Route-specific evidence](docs/SUPPORT.en.md).

**Limits:** all reductions remain REVIEW_REQUIRED for musical acceptance. Human listening, playing, source review and pedagogical calibration are NOT_RUN. Original retains grace/roll notation and is INCOMPLETE for internal playback verification; its MuseScore MIDI is an unverified audition aid. The reductions omit five graces and flatten two rolled chords, preserving the timed main melody and LH response but losing that ornamented attack. No guarantee of real playability or examination level is made.

## 中文

本补丁保留最新公开 main 的产品说明与行为，新增依据原谱的《十月》对照，并以内容哈希清单及单独发布回执取代过期发布状态。仍为实验版，v0.3.6 资产不变。

- 英文默认 README 和完整中文 README 保留；普通 Easy Piano 的差异说明、可选演奏者信息、具体限制／试弹反馈优先、只提供曲名时查找允许使用的来源，以及兼容 ID `piano-score-reduction` 均保留。
- [《十月》第 1–16 小节](examples/tchaikovsky-october/README.zh-CN.md)：Schirmer/Oesterle 1909 年版重新转录的参考版与 L1/L2/L3，附 MusicXML、MuseScore PDF、可比 PNG、MIDI、改动说明及 QA。[五页对照](examples/tchaikovsky-october/comparison.pdf)。不分发来源扫描或旧实验 L2；见[来源与权利](examples/tchaikovsky-october/SOURCE.zh-CN.md)。
- `DISTRIBUTION.json` 为当前字节的 CONTENT_SNAPSHOT；远端核验后单独提供 `PUBLICATION.json`，不改动标签包。见[状态语义](docs/DISTRIBUTION.zh-CN.md)。
- 103 项回归通过；精确 source ZIP 和便携 ZIP 在新隔离环境完成完整性及解压运行检查，包含真实 MuseScore 4.7.5 排版、局部修订、输入／旧版保留、错误 XML 和不支持装饰音。四张乐谱页与五页对照均逐页看图检查；运行版本与 0.3.7 一致。
- 运行脚本仅版本常量改变。Claude Code／Claude 网页／ChatGPT Work 的证据明确继承自 v0.3.6，未重新独立试验 v0.3.7。见[具体路径矩阵](docs/SUPPORT.zh-CN.md)。

**边界：**三档音乐性验收仍为 REVIEW_REQUIRED。人工试听、实弹、来源审核与教学等级校准均为 NOT_RUN。Original 保留倚音和滚奏，内部播放核验 INCOMPLETE，MuseScore MIDI 仅供未完整核验试听。三档省略 5 个倚音、平化 2 个滚奏和弦；有时值主旋律与左手回应保留，但装饰性起音损失。不保证真人可弹或考级水平。
