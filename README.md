# Score Simplifier · 钢琴谱简化

[中文](#中文) · [English](#english)

## 中文

[下载实验版](https://github.com/zhenglimindesign-ing/piano-score-simplifier/releases/tag/v0.3.6) · [安装说明](docs/INSTALL.zh-CN.md) · [反馈问题](https://github.com/zhenglimindesign-ing/piano-score-simplifier/issues)

**先弹喜欢的音乐，再逐步接近原版。**

喜欢一首曲子，却被原谱的和弦、跳跃或复杂伴奏挡住？Score Simplifier 根据原谱制作更容易演奏的版本：保留旋律与关键音乐特点，调整技术负担，让你从一个更容易开始的版本练起。

它是一个 AI skill。你用日常语言提出需求，得到可以打印、编辑和试听的曲谱，再根据实际练习继续调整。适合刚开始挑战完整作品、正在恢复练习，或希望先抓住音乐主线的演奏者。

**支持范围：钢琴独奏曲谱。**

可使用公版、自创或已获相应授权的乐谱；曲目不限于固定清单。

### 选择适合这次练习的档位

| 档位 | 改编重点 | 什么时候选 |
|---|---|---|
| **L1 · 核心版** | 突出旋律，保留基本和声支撑，明显减轻织体负担 | 想先完整地奏出音乐主线 |
| **L2 · 易弹音乐版** | 保留旋律、主要和声和精选的特色织体，减少难以执行的伴奏 | 希望保留更多原曲感觉；默认从这一档开始 |
| **L3 · 中级简化版** | 保留更多声部与细节，集中调整较难的技巧段落 | 已有一定基础，希望更接近原谱 |

档位描述的是改编取向，不对应官方考级。不同曲目的难点并不相同；先试一个小样，比只看等级名称更容易判断是否合适。

你也可以直接说“和弦太大”“伴奏跳得太远”或“这段双手配合很难”。不需要先填写能力问卷。

### 选一个短版本，还是整首？

| 篇幅 | 得到什么 | 适合做什么 |
|---|---|---|
| **Mini · 乐句版** | 一个完整的音乐想法，有自然的起点和结尾；通常约半页到一页 | 先试难度和改编方向 |
| **Full · 完整版** | 保留主要段落与曲式路线；若有删节，会在说明中列出 | 用一个连贯版本练习整首 |

页数服从乐句完整和谱面可读性。Mini 会通过选段与编配控制篇幅。

### 第一次使用

以 Codex 本地使用为例：

1. 按[安装说明](docs/INSTALL.zh-CN.md)解压 skill 包，将完整的 `piano-score-reduction` 文件夹放入项目的 `.agents/skills/`，再在 Codex 打开该项目。请 Codex 检查 Python、依赖和 MuseScore，并实际生成一次可打开的文件。
2. 提供曲谱。优先使用 MusicXML（.musicxml、.xml、.mxl）；PDF 需要先转录并核对，识谱有疑问的地方会明确指出。你无需自己先制作 MusicXML。
3. 描述想怎样简化。可以直接发送：

~~~text
请使用已安装的 piano-score-reduction 曲谱简化 skill。
把我提供的曲谱做成 L2 易弹音乐版，先生成一个 Mini 乐句版。
保留主旋律和原曲的感觉，让伴奏少一些跳跃。
请给我 PDF、MusicXML、MIDI，并说明主要改动和仍需注意的难点。
~~~

拿不准档位时，可以只说“先做一个更容易的短版本”。也可以提供曲名；生成前需要找到并核对可用原谱，无法确认的来源或音符不会凭记忆补齐。

### 你会收到什么

| 内容 | 用法 |
|---|---|
| **PDF** | 看谱、打印和练习 |
| **MusicXML** | 在制谱软件中继续编辑 |
| **MIDI** | 试听音符、节奏和版本差异；环境允许时可附音频 |
| **改编说明** | 查看保留了什么、调整了什么、哪些小节仍有难点 |

先看谱、听一遍，再按适合自己的速度试弹。MIDI 是试听参考，实际弹奏感受仍以练习为准。

### 练起来还不合适？继续改

告诉它具体小节和困难，例如：

> 第 8–12 小节的伴奏还是跳得太远。请保留旋律，让伴奏更稳，保存一个新版本，并保留上一版供我比较。

也可以要求保留某个伴奏型、减小和弦跨度，或在认可 Mini 后继续 Full。原始曲谱和已有版本会保留。

### 使用边界与反馈

简化会改变部分伴奏、音区或织体，改编说明会列出主要取舍。若某段无法兼顾音乐特点与目标难度，会说明冲突，再比较可行的方案。

不清晰的照片和部分复杂记谱可能需要额外转录或处理。明确标记的弱起、普通整小节反复与一二房子已有播放顺序检查。普通／指定循环长波音、单倚音与单手 2–4 音滚奏可按明确的邻音、顺序和时值提案写开；音乐解释另行确认。复杂反复导航、未实现的装饰音等会保留，并明确报告未完成的检查；成功生成 PDF 不代表播放与音乐已经完整核验。L1–L3 也不能替代对个人演奏能力的判断。

反馈时，给出所用版本、具体小节，以及“哪里仍难”或“哪里失去了原曲感觉”。遇到运行问题，附实际错误信息。

项目自有代码与说明采用 [MIT 许可](LICENSE)；输入乐谱与第三方工具的权利另行处理，见 [NOTICE](NOTICE)。

## English

[Download the experimental release](https://github.com/zhenglimindesign-ing/piano-score-simplifier/releases/tag/v0.3.6) · [Install](docs/INSTALL.en.md) · [Report an issue](https://github.com/zhenglimindesign-ing/piano-score-simplifier/issues)

**Start with the music you love. Work your way toward the original.**

A piece catches your attention, but its chords, leaps or accompaniment put it out of reach. Score Simplifier creates an easier arrangement from the source score, keeping its melody and defining musical features while reducing the technical demands.

It works as an AI skill: describe what you need, receive notation you can print, edit and listen to, then refine it as you practise. It is for players approaching complete pieces, returning to an instrument or looking for a clearer starting point.

**Supported repertoire: solo piano scores.**

Use public-domain, original or appropriately authorized scores. Repertoire is not restricted to a fixed list.

### Choose an arrangement level

| Level | Arrangement focus | Choose it when |
|---|---|---|
| **L1 · Essential** | Bring the melody forward with basic harmonic support and a substantially lighter texture | You want to play the musical outline first |
| **L2 · Easy Musical** | Keep the melody, main harmony and selected characteristic textures while easing demanding accompaniment | You want more of the original character; the default starting point |
| **L3 · Intermediate Reduction** | Retain more voices and detail, with focused changes to difficult technical passages | You have some experience and want to stay closer to the original |

These levels describe arrangement choices, not official examination grades. Different pieces pose different challenges; trying a short sample is more useful than relying on a level label alone.

You can simply say “the chords are too wide,” “the accompaniment jumps too far” or “coordinating both hands is difficult here.” No ability questionnaire is required first.

### Try a phrase or work on the whole piece

| Length | What you receive | Useful for |
|---|---|---|
| **Mini · Complete phrase** | One coherent musical idea with a natural beginning and ending, usually around half a page to one page | Trying the difficulty and arrangement direction |
| **Full · Complete arrangement** | The major sections and formal route, with any cuts identified in the notes | Practising a coherent version of the whole piece |

Musical coherence and readable notation take priority over page count. Mini controls length through selection and arrangement.

### Your first arrangement

For local use in Codex:

1. Follow the [installation guide](docs/INSTALL.en.md): extract the skill package, put the complete `piano-score-reduction` folder in your project's `.agents/skills/`, then open that project in Codex. Ask Codex to check Python, dependencies and MuseScore, and produce an actual file you can open.
2. Provide your score. MusicXML (.musicxml, .xml or .mxl) is preferred. A PDF needs transcription and comparison first, with uncertain passages identified. You do not have to prepare MusicXML yourself.
3. Explain what you want changed. For example:

~~~text
Use the installed piano-score-reduction score simplification skill.
Make an L2 Easy Musical arrangement of the score I provided,
starting with a Mini complete phrase.
Keep the main melody and the character of the piece, with fewer accompaniment leaps.
Give me PDF, MusicXML and MIDI, plus the main changes and remaining difficult passages.
~~~

If you are unsure about levels, ask for “an easier short version.” You can also provide a title: a usable source must be located and checked before generation. Uncertain sources or notes will not be filled in from memory.

### What you receive

| Deliverable | Use |
|---|---|
| **PDF** | Read, print and practise |
| **MusicXML** | Continue editing in notation software |
| **MIDI** | Listen to notes, rhythm and differences between versions; audio may also be provided when available |
| **Arrangement notes** | Understand retained features, changes and remaining difficult bars |

Read the score, listen, then try playing at a comfortable tempo. MIDI is a listening reference; your playing experience determines whether the arrangement feels right.

### Refine it as you practise

Point to the bars and describe the problem:

> The accompaniment still jumps too far in bars 8–12. Keep the melody, make the accompaniment steadier, and save a new version while retaining the previous one for comparison.

You can also preserve a favourite accompaniment pattern, reduce chord stretches or extend an accepted Mini into Full. Original scores and existing versions are retained.

### Boundaries and feedback

Simplification can change accompaniment, register or texture. The notes explain the main trade-offs. If a passage cannot retain its defining features at the requested difficulty, the conflict is explained and workable alternatives can be compared.

Unclear photographs and some complex notation may need additional transcription or processing. Explicit pickups, simple whole-measure repeats and first/second endings have checked playback routes. Plain/explicit-cycle long mordents, a single grace and a one-hand 2–4-note roll can be written out with explicit pitch/order/rhythm proposals; musical interpretation needs separate acceptance. Complex navigation and unrealized ornaments are retained, with unperformed checks identified; a successful PDF export does not establish complete playback or musical verification. L1–L3 cannot replace a judgement of an individual player's abilities.

For feedback, name the version and bars, then describe what is still difficult or what has lost the character of the original. For execution problems, include the actual error.

The project's own code and documentation use the [MIT license](LICENSE). Score and third-party rights remain separate; see [NOTICE](NOTICE).
