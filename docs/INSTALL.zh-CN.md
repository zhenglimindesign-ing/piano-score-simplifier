# 安装 skill，并验证第一次运行

[English](INSTALL.en.md) · [使用说明](../README.zh-CN.md)

Score Simplifier 处理来源与使用权限明确的钢琴独奏谱。先用短而清楚的曲谱，确认所选宿主确实能交付文件。MusicXML／MXL 可以直接检查；PDF 先转录并核对来源。

## 1. 取得完整 skill 文件夹

Score Simplifier 是公开项目名；当前 skill ID 和安装目录名为了兼容仍保留为 `piano-score-reduction`。

从[v0.3.7 发布页](https://github.com/zhenglimindesign-ing/piano-score-simplifier/releases/tag/v0.3.7)下载 `piano-score-reduction-<version>.zip` 并解压，使用其中完整的 `piano-score-reduction` 文件夹。如果拿到的是仓库压缩包，使用 `skills/piano-score-reduction`，并将根目录的 `LICENSE` 与 `NOTICE` 复制到安装后的文件夹。保持以下内容完整：

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

只复制 `SKILL.md` 会缺少脚本与排谱样式。更新时保留旧安装和曲谱输出；不确定当前版本时，可以另建测试项目。

## 2. 放到对应宿主，或在宿主中加载
**证据版本：**下表的宿主试验继承自 v0.3.6（较早的完整流程证据另行注明）。v0.3.7 新做了本地包／运行检查；Claude Code、Claude 网页和 ChatGPT Work 的独立 v0.3.7 试验均为 NOT_RUN。见[本次证据矩阵](SUPPORT.zh-CN.md)。


| 宿主 | 安装／使用入口 | 已验证边界 |
|---|---|---|
| Codex 本地项目 | 放到 `.agents/skills/piano-score-reduction/`，打开项目，在请求中说明 skill 名称 | Codex CLI 0.145.0 在记录的 macOS 配置通过双语首次生成、局部修订、旧版保留与异常输入流程 |
| Claude Code 本地项目 | 放到 `.claude/skills/piano-score-reduction/`，打开项目并请求使用 skill | Claude Code 2.1.218 在记录的 macOS 配置通过固定双语流程，并从实际加载的项目 skill 完成 v0.3.6 受影响检查，使用 MuseScore 4.7.5 |
| Claude 网页 | Customize → Skills → Add skill → Upload skill，选择便携 ZIP 并启用；在专用聊天附上曲谱 | 固定 v0.3.4 原生安装与双语流程已验证，使用明确记录的适配器；最终 v0.3.6 精确临时源码使用 MuseScore3 3.2.3、无外部适配器，通过实际排版／修订／保留／不支持输入检查及独立核对。既有原生安装保留 |
| ChatGPT Work 执行环境 | 在专用 Work 聊天附上完整便携 ZIP 与已授权曲谱，明确请求解压和实际执行 | 固定 v0.3.4 双语流程与最终 v0.3.6 精确源码受影响检查，已在临时 Work 环境独立通过，实际配置为 Ubuntu 24.04.3／Python 3.12.14／MuseScore 4.3.2 AppImage，包含已下载实物、限定修订、旧版保留和不支持输入。未测试原生持久插件安装或其他 ChatGPT 模式 |

路径相对于你打开的项目，而非解压后的 skill 文件夹。账号功能与权限由具体宿主提供；一个本地 CLI 配置通过，不能推定所有桌面沙箱或云端入口都可用。

## 3. 让 agent 检查依赖

在已加载 skill 的位置发送：

```text
请使用已安装的 piano-score-reduction skill。
通过 preflight 检查实际执行环境，包括 Python、固定依赖、
MuseScore 和 PDF 页面检查工具，在隔离环境处理普通缺失依赖。
保留我的输入和旧版；需要我处理的访问问题请具体说明。
不要仅凭程序路径存在就认定能够成功排谱。
```

运行需要 Python 3.10+、skill 中固定的 Python 依赖、生成 PDF 的 MuseScore，以及检查页面的 `pdftoppm`。音频导出可选。普通环境工作由 agent 处理；你提供曲谱和音乐目标。

完整本地测试使用 Python 3.14.0、lxml 6.1.3、mido 1.3.3、MuseScore 4.7.5 和 Poppler。Claude 网页使用 Python 3.12.3 与 Ubuntu 官方 MuseScore3 3.2.3。检测器现已包含 `mscore3`。v0.3.6 内置 MS3 原生谱／样式／重新加载 PDF 路径，自动匹配样式版本并保留日志及中间文件；规范 XML 与内置 MIDI 仍是权威。实际解压后的 macOS MuseScore 4.7.5 检查及 Claude Code 已加载 skill 检查通过。Claude 网页已无外部适配器通过内置 MS3 路径；实际 PDF、XML、MIDI 与保留的父版本已独立核对。ChatGPT Work 最终检查也通过，使用明确指定的 MuseScore 4.3.2 AppImage 启动器。固定 v0.3.4 完整双语宿主接受与最终版本受影响检查分别记录。

macOS 工作区沙箱可能阻止 MuseScore 的 PasteBoard／XPC 访问。保留实际错误，解决宿主的排谱权限。本地测试使用允许排谱的调用配置；Claude Code 工具许可只作用于单次调用，未改变全局设置。

Codex 安装后，从项目根目录运行的可选 macOS 命令：

```sh
python3 -m venv work/venv
work/venv/bin/python -m pip install -r .agents/skills/piano-score-reduction/requirements.txt
work/venv/bin/python .agents/skills/piano-score-reduction/scripts/preflight.py
```

Claude Code 改用 `.claude/skills/`；直接从仓库执行时改用 `skills/`。这些命令检查依赖，不证明排谱与文件交付已成功。

## 4. 生成、打开，再修改一份谱

提供短的自创或已获相应授权的钢琴独奏谱。首次环境检查优先用 MusicXML，然后发送：

```text
请使用已安装的 piano-score-reduction skill 处理这份谱。
制作有连贯结尾的 L2 Mini，保留主旋律，减轻伴奏负担，保留原件。
给我可下载的 PDF、MusicXML、MIDI、改编说明和 QA。
请实际排谱并检查每一页，明确记录尚未执行的检查。
```

打开下载的 PDF，将 XML 导入制谱软件，并打开 MIDI。随后要求具体修订，例如：

> 第 6 小节左手和弦跨度太大，请减小跨度，保持旋律和其他小节不变。保存新版本，并保留上一版。

核对两版都还在、改动限定在请求的小节、说明列出了音乐损失。畸形或不支持的记谱无法完整处理时，也应留下准确的错误报告。

## 看懂结果，处理问题

| 结果／现象 | 如何推进 |
|---|---|
| `REVIEW_REQUIRED` | 技术检查通过；核对改编并试用，不等于音乐质量或官方考级认证 |
| `FAIL` | 明确检查失败，包括排版不清楚；要求修复并保留失败版本 |
| `INCOMPLETE` | 必需检查未能执行，或记谱尚不支持；查看缺少哪项检查并保留来源 |
| `ERROR` | 执行、输入或计划校验失败；提供实际错误，由 agent 修正 |
| 只有指导文字，没有可下载文件 | 加载指令不代表已执行；检查宿主运行环境、排谱器和文件交付路径 |

真人听／弹与等级校准独立于文件检查，尚未验证；实验首版不以它们为阻塞项。不保证任何曲谱、记谱形式、个人手型或宿主配置都能直接完成。

[AI 指令](../skills/piano-score-reduction/SKILL.md)和[执行参考](../skills/piano-score-reduction/references/workflow.zh-CN.md)说明来源处理、支持的记谱与版本保留。直接描述哪里困难即可，无需填写能力问卷或提供工程阈值。
