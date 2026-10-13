# score-simplifier 提交准备

[English](SUBMISSION.md)

这是 `codex/distribution-prep-20261013` 上的 0.3.8-distribution.3 审查候选包。现有 Release 和 Tag 未改动，发布前需维护者审查。生成式公开分发项目在下一次 Release 前应同步回 canonical 源码；本次不改写历史发布清单哈希。

## OpenAI

完整 ZIP 包含通用、Codex、Claude manifest、方形图标、三个启动提示、依赖与隐私说明。产品范围由 `skills/*/agents/openai.yaml` 声明。

执行路径限定为 CODEX。Codex 与已登录 Claude Code 使用声明的 Python 依赖及已安装 MuseScore 渲染器，对两小节自创测试谱生成 XML、PDF 和 MIDI；独立事件比对通过。人工聆听、演奏、等级校准及 ChatGPT/Work 执行为 NOT VERIFIED。本地执行的 partner 准入仍是外部条件。

提交账号须完成开发者身份验证并具备写权限。操作路径为 https://platform.openai.com/plugins → 上传新插件 → skills-only ZIP，检查转换和自动扫描结果并修复阻断项。当前草稿与扫描结果另见任务交接，本地包校验不构成这些状态的证明。正式送审和具有约束力的声明需账号持有人授权。

## Claude

来源：`zhenglimindesign-ing/piano-score-simplifier`；路径：`directory-plugins/score-simplifier`；分支：`codex/distribution-prep-20261013`。操作路径为 https://claude.ai/directory/manage → Submit new → Plugin bundle → Validate。GitHub 写权限已确认，最终任务交接记录平台校验及保存草稿是否实际成功。本地 Claude 安装／发现及已登录小任务通过；目录内原生运行仍为 NOT VERIFIED。

manifest 指向[分支隐私说明](https://github.com/zhenglimindesign-ing/piano-score-simplifier/blob/codex/distribution-prep-20261013/directory-plugins/score-simplifier/PRIVACY.md)。政策咨询由另一路处理，本次不因政策推测删除核心功能，也不把校验通过当作政策批准。联系邮箱、年龄范围、具有约束力的合规确认与正式送审仍需账号持有人决定。本任务未获正式送审或公开发布授权。

## skills.sh

仓库发现、完整复制和新会话加载已在关闭遥测下通过；双语公开 README 已补充验证过的命令。默认分支安装仍使用当前公开源码，提议的文档和指令修复经维护者审查后才进入默认分支。关键词／搜索收录是独立事项且为 NOT VERIFIED；本次未添加排行榜功能或发送安装遥测。
