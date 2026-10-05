# 执行参考

使用 Python 3.10+，在 `work/` 下建立隔离环境并安装本 skill 的 `requirements.txt`。先运行 `preflight.py`；允许访问网络时再运行 `fetch_schema.py work/schema`。后者只下载固定版本的 W3C 格式文件并核对 SHA-256，不上传乐谱。未提供格式文件时，schema 检查为 NOT_RUN。

以下命令由 agent 执行，用户只需描述音乐需求。脚本路径以 skill 目录为基准，路径加引号；临时文件放 work/，交付件放 outputs/。每次输出使用新版本，不能覆盖输入或已有结果。

```sh
python scripts/score_pipeline.py run --input INPUT.musicxml --out outputs/NAME-v1 --hands 1:R,2:L --level L2 --schema-dir work/schema --audio
python scripts/score_pipeline.py run --input outputs/NAME-v1/score-v1.musicxml --previous outputs/NAME-v1 --purpose repair --plan work/plan-v2.json --out outputs/NAME-v2 --hands 1:R,2:L --schema-dir work/schema
python scripts/score_pipeline.py run --input outputs/NAME-v2/score-v2.musicxml --previous outputs/NAME-v2 --purpose revision --request "用户原话" --edit-scope 6 --plan work/plan-v3.json --out outputs/NAME-v3 --hands 1:R,2:L --schema-dir work/schema
python scripts/score_pipeline.py annotate --manifest outputs/NAME-v2/manifest.json --check page_inspection --status PASS --by agent --evidence "已查看第 1–2 页……"
```

每次 `run` 写入一个新版本目录：输入副本（首版）、MusicXML、经过读回核对的 MIDI、PDF 及每页图片、QA、事件对应表（输入 ID → 输出 ID）、`manifest.json` 和简短的中英文 `REPORT.md`。之后每一版都用 `--previous`，且新输入必须是上一版的 MusicXML。`--purpose repair` 用于失败版本之后，两轮针对性修复后拒绝第三轮。`--purpose revision` 记录用户原话和 `--edit-scope`，范围外的改动会被拒绝。单步操作仍可使用 `score_tool.py`。

退出码：0 表示自动必查项通过（记录复核前仍是 REVIEW_REQUIRED）；1 为 ERROR（畸形输入、计划被拒、版本链断开、超出范围的修改、第三轮修复）；2 为 FAIL（有检查失败）；3 为 INCOMPLETE（自动必查项未执行，例如不支持的记谱、缺 schema 或排谱器）。失败运行保留 manifest 与错误；输入和旧版本不会被修改。`--hands` 是明确的编配决定，不是推测默认值。跨手时先调整谱表或实现逐事件用手映射。

计划格式：`{"input_sha256":"...","protected_ids":["P1:m1:n2"],"edits":[{"id":"P1:m1:n4","op":"octave","octaves":1,"reason":"..."}]}`，可选 `request`、`musical_losses`、`remaining_difficulties`、`source_map` 与 `final_barline`。ID 由 part ID、从 1 开始的小节位置、从 1 开始的 note 元素位置组成，只对应该输入；装饰音也计入位置。印刷小节号与 `--edit-scope` 不一定相同：所有 `mN`／范围数字均是从 1 开始的输入小节位置，不受 `number` 属性、弱起或带字母小节号影响。修改前将用户说的印刷小节映射到该位置，并报告两者（例如弱起后印刷第 15 小节 → 输入位置 16）。每项操作都要写理由：

- `octave`（±1 或 ±2）与 `remove_chord_doubling`（同起点、同音级的重复音）；
- `remove_chord_member`：可删除任一和弦音；删除首音时，把下一个和弦音的音高移入首音元素，保留符杠、连奏线和连音组，并在事件对应表中记录；
- `rest`：没有剩余和弦音、也不是连奏线端点的单音，换成同时值休止；
- `remove_grace`：明确省略装饰音，同时删除该装饰音自己的连奏线；
- `realize_grace`：同一 voice／staff 中紧接一个主音之前的普通单倚音，明确提供 `steal="following"` 与精确正值 `pulse_quarters`。写在拍点上，从后续主音借时值，保持主音原结束位置。支持有效延音链的起点主音或精确配对的倚音到主音连奏线。多个／和弦倚音、已有延音的承接点、限定的时间解释、其他受保护记谱或另行修改的主音会被拒绝。这是明确节奏提案，不自动推断拍前或历史演奏法；
- `realize_arpeggio`：同一 voice／staff 中无延音线的 2–4 音和弦，全部成员具有同组琶音符号。提供全部成员 ID 的唯一完整 `order` 与精确正值 `pulse_quarters`，符合已有向上／向下方向。以延音连接的连续和弦组每个脉冲加入一个音，全部音在原和弦结束位置释放。限定／缺失符号、混合声部／谱表、其他记谱、延音线、受保护或另行修改的成员会被拒绝。event map 记录各来源音的重复延音片段；
- `realize_ornament`：把一个普通、无延音线的 `mordent` 或 `inverted-mordent` 写成主音—邻音—主音。明确提供 `neighbor`（`step`、整数 `alter` -1/0/1、整数 `octave`）与精确 `pulse_quarters`（如 `"1/8"`）。邻音必须是符号方向上相邻音名字母，距离半音／全音。仅带 `long="yes"` 的长符号还须提供整数 `cycles` 2–8：先写 `2*cycles` 个交替脉冲音，再由返回的主音占满原剩余时值；这类长符号可以是有效延音链的起点，声音／视觉延音起点移到最后返回的主音，后续延音保持。已有延音的承接点、和弦、连音组、其他限定／记谱和受保护音需要另行处理。输入 divisions 必须精确表示每个数值。音高与节奏属于明确提案，不自动推断历史演奏法。event map 的 `expansions` 记录全部输出 ID，外声部与范围检查继续适用；
- `remove_ornament` 加指定 `ornament`（如 `trill-mark`、`mordent`、`turn`），或 `remove_arpeggio`：仅省略一个已有符号，保留音高、时值、延音线与其他记谱。带临时记号限定的装饰音需要另行编写处理。省略必须写理由并列为音乐损失，不能当作装饰音播放实现；
- `set_clef`：`P1:m1:c2` 指第 1 小节中的第二个已有 `<clef>`；设置 `sign` 为 G/F/C、整数 `line` 为 1–5。用于修正来源／排版记谱，不改变音高、谱表或手分配；移调谱号需要另行处理；
- `remove_direction`：`P1:m9:d2` 指第 9 小节的第二个 `<direction>`（不能是速度／播放指令）。

延音音符只能与整条延音链在同一计划中、以同一操作一起修改。不得为通过跨度检查把音移到低音之下或旋律之上；优先删除重复音和内声部，并逐项列出损失。每个起音或音符结束边界的最低或最高发声音高发生变化时，计划会被拒绝，整段变成休止也包括在内；除非该小节有修改项写明 `"outer_voice": ["bass"]` 或 `["top"]`，并在理由中说明。manifest 会列出每一处此类变化（`after: null` 表示休止）。`annotate` 只接受真人记录的 `musical_review` 通过。受保护或没有理由的修改会被拒绝。没有隐藏的自动编配器或八度优化器。

明确标记 implicit 的短小节按实际时长处理，不补空拍。非嵌套整小节反复（总播放次数 1–32）与配对的一二房子保留书写记谱，并核对实际播放顺序。QA 分别记录书写与播放时长，按播放顺序检查延音线和双手，反复跳回时恢复原位置速度。小节内／嵌套反复、其他跳房子布局和 D.C.／D.S.／Coda 仍为 NOT_RUN；未实现的装饰音、琶音、震音、移调、复杂拍号和跨谱表延音线也是如此，运行结果为 INCOMPLETE。明确省略符号属于记录的损失，即使定时音高不变，也必须位于修改范围内。不得在计划之外手改 XML 以通过检查。确有音乐需要（例如写出反复）时，先提出方案，再作为新记谱并附来源对应，执行同样检查。内置 MIDI 无法运行时，可以产生 `midi-musescore-unverified`，仅供试听，没有读回核对。

seed-0.1 参数：L1 跨度≤7 半音／同时音高数≤2；L2≤9／≤3；L3≤12／≤4。用户自述的考级／水平或最近舒服演奏的曲目只作软参考；明确的跨度、八度、跳跃、协调限制和真实试弹反馈优先。检查最大同时手指保持负担，包含延音线。移动提示用相邻起音组音高均值的位移（>7／12／19 半音），不是经过验证的指法距离。滑动一秒的起音组阈值 >3／5／8，绑定乐谱四分音符速度。这些是试验工程目标，须报告超标、最大／95 分位移动与速度，不能转述为官方考级。踏板不会缩短手指保持时长；节奏、声部与读谱负担另做音乐审核。

PDF 使用当前环境实际存在的 MuseScore。MuseScore 4 按参数列表执行 `[mscore, '-S', style, '-o', output.pdf, canonical.musicxml]`。MuseScore 3 使用样式时，先把规范 XML 导入仅供排版的 MSCX，读取其原生格式版本，把版本匹配的样式保存进另一个 MSCX，再重新加载该文件输出 PDF，以解决 MS3 拒绝样式版本及 `-S` 后未重新布局的问题。保留两个原生中间文件、原样式／实际样式哈希以及每条命令的 stdout/stderr。MSCX 不替代规范 MusicXML，也不用于内置 MIDI。流水线默认使用 `assets/readable-a4.mss`，也可用 `--style` 指定；无论哪种都要看真实页面；样式与乐谱一起版本化。用 `pdftoppm` 转换全部页面，逐页检查标题、谱号、变音、延音线、连音组、间距与结尾。不能缩小音符来伪装满足页数目标。排版和实际翻页分别记录。macOS 沙箱下的 XPC／剪贴板启动错误需要本地进程权限，不应误诊为没装软件。

MIDI 导出按 voice 分配钢琴通道，合并相邻延音线，并核对序列化后的音高、起点和终点。它使用固定力度与明确速度，不模拟踏板、自由速度或力度表情。可选 MuseScore 音频由规范 MusicXML 导出，记录来源哈希和播放引擎。MuseScore 对延长记号、奏法和力度的处理可能与内置直译 MIDI 不同，不能声称播放时间一致。成功解码不等于真人试听。真正发生前，试听／试弹保持 NOT_RUN。

每个宿主分别验证发现 skill、自然语言请求、保留输入、同一小样、PDF 实际页面、下载／打开、后续修改与不支持输入。中英文请求均实测后才能声称双语行为验证通过。未经任务授权，不为模拟平台测试而安装或启动另一个 AI agent。

从 v0.2.0 起，`hand_coordination` 是独立必查项：明确分给双手、同时用手指保持同一个键的事件，在记谱落实可演奏的合并／分配前判失败；包括保持过程中另一手再起音。前一手释放后可以交接。同键冲突与只有音区交叠的提示分开。存在双手冲突的谱仍可能成功序列化为 MIDI，因此必须看全部检查。历史 v1 文件不改写，新检查可以拒绝旧候选。
