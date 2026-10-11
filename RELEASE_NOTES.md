# Score Simplifier v0.3.8

PDF-only work can reach full-score processing before source reconstruction and delivery scope are clear, causing costly retries and confusing graphical PDFs with complete editable scores. This revision adds read-only PDF intake, explicit delivery contracts, measured stage checkpoints and regression guards for known reduction errors.

- PDF intake reports source hashes, representative page metadata and declared roles; source preparation remains agent-owned.
- Choose annotations, graphical note removal or editable re-engraving. Complete MusicXML and MIDI from PDF require verified transcription of the requested scope; diagnostic excerpts are labelled.
- Stage checkpoints distinguish observed use, cash charges and human labor. Two failed repairs prompt a method change and continued independent work.
- Normalized graphical edit records guard shared noteheads, ties and accidental inheritance. New notation cases cover tuplet rests and sustained shared-key reattacks.
- No OMR engine, audio-analysis capability or calibrated L3 system is added. Unperformed musical and human checks remain NOT_RUN.

Validation: 79 relevant regressions passed for the revision, including 17 new cases. The release-specific installed-package and rendering results are recorded in the release verification receipt. The existing October showcase and previous versions remain unchanged; no Strauss score is included.

## 中文

扫描 PDF 的来源转录和交付范围没有提前明确，容易导致全曲返工，也容易把图像减音 PDF 与完整可编辑谱混淆。本版增加只读 PDF 预检、交付约定、已测量的阶段检查点及已知减音错误的回归检查。

- 报告原件哈希、代表页信息与声明的声部角色；来源准备仍由 agent 负责。
- 按需求选择标注、图像减音或可编辑重新刻谱。PDF 的完整 MusicXML／MIDI 需要可靠转录相应范围；诊断样段明确标注。
- 区分已观察用量、现金扣费和人工工时；同一方法修复两次仍失败时换方法，继续独立工作。
- 规范图像记录检查共用音头、延音与变音继承；新增记谱案例覆盖连音组休止及持续共键音的重复触键。
- 未增加 OMR 引擎、音频分析能力或经校准的 L3 系统。未完成的音乐／真人检查保持 NOT_RUN。

验证：本次修订已有 79 项相关回归通过，其中新增 17 项。正式安装包与排谱检查结果另记在发布验收回执。既有《十月》公开示例和旧版本保留；本包不包含 Strauss 乐谱。
