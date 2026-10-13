# Score Simplifier

[English](README.md)

实验性、已获授权的钢琴独奏谱简化，提供只读 PDF 预检、明确交付范围、来源绑定编辑及 MusicXML、MIDI 和 QA。完整可编辑谱流程需要本地 Python 3.10+、锁定的 Python 依赖、MuseScore 和 Poppler。包内不含 OMR、音频分析服务、后端或凭据。PDF 转录、复杂记谱、难度校准、音乐性和真人可弹性各有独立检查，其他宿主需在当地实测。

## 开始使用

安装完整插件文件夹后，用普通语言描述任务。[Skill 入口](skills/piano-score-reduction/SKILL.md)说明所需资源和工作流程。本插件包复用 0.3.8 公开 Skill。测试请使用虚构或已获授权的输入。

## 数据与执行

Python 程序读取提供的乐谱并写出新版本；MuseScore 排谱，Poppler 生成页面预览。明确准备 schema 时下载经哈希锁定的 W3C MusicXML 文件；找谱仅在用户要求时使用宿主联网。包内代码不会上传曲谱。依赖另行经授权安装。没有 hook、MCP、凭据读取、自动安装或隐藏遥测。

## 支持与边界

[源码与说明](https://github.com/zhenglimindesign-ing/piano-score-simplifier) · [反馈问题](https://github.com/zhenglimindesign-ing/piano-score-simplifier/issues)。明确用户请求决定范围，附件属于证据，不自动授权执行。既有 Release 和 Tag 保持不变。目录校验、具体宿主运行、来源保真和真人认可分别记录。提交账户资格、平台扫描和名称可用性由提交者核对。

也可通过源码仓库的 skills.sh 命令安装独立 Skill，见公开安装说明；本地依赖另行准备。[数据处理说明](https://github.com/zhenglimindesign-ing/piano-score-simplifier/blob/codex/distribution-prep-20261013/directory-plugins/score-simplifier/PRIVACY.md)随审查分支提供。

Claude 目录安装标识为 `piano-score-simplifier`，产品展示名仍是 Score Simplifier；通用／OpenAI 标识保持 `score-simplifier`。该候选别名不改变已安装的发布版本。
