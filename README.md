# Score Simplifier

[简体中文](README.zh-CN.md)

[Download the experimental release](https://github.com/zhenglimindesign-ing/piano-score-simplifier/releases/tag/v0.3.6) · [Install](docs/INSTALL.en.md) · [Report an issue](https://github.com/zhenglimindesign-ing/piano-score-simplifier/issues)

**Start with the music you love. Work your way toward the original.**

A piece catches your attention, but its chords, leaps or accompaniment put it out of reach. Score Simplifier is an AI skill that creates an easier solo-piano arrangement from a reliable source score, then lets you keep refining it as you practise.

The aim is not simply to remove notes. It is to reduce the **real playing burden** while preserving as much of the piece's musical identity as possible.

**Supported repertoire: solo piano scores.** Use public-domain, original or appropriately authorized scores; repertoire is not restricted to a fixed list.

## Why Score Simplifier?

### Fewer notes do not automatically mean easier playing

A sparse-looking score can still contain an impossible stretch, a large jump or awkward hand coordination.

Score Simplifier checks different kinds of burden separately, including:

- simultaneous reach and note count for each hand;
- consecutive position shifts and jumps;
- conflicts between the hands;
- attack density and coordination;
- polyphony and voicing demands.

A reduction counts as easier only when the actual playing burden is reduced.

### It does not flatten every piece into melody + chords

An inner voice can carry important harmony, voice-leading or character even when it is not the main melody.

The arranging process distinguishes between:

- melody, signature rhythms and critical bass events that should be protected;
- high-value inner voices and harmonic colour;
- chord filling that can be compressed;
- redundant doublings, octaves or technically expensive material that can be reduced first.

A Romantic cantabile piece, Bach counterpoint and an arpeggio-driven work should not receive the same generic simplification.

### A successful PDF export is not the same as a successful arrangement

Source fidelity, technical difficulty, engraving, playback and human playability are separate questions.

The skill keeps these checks separate and reports work that was not actually verified instead of silently treating it as passed.

## Choose an arrangement level

| Level | Arrangement focus | Choose it when |
|---|---|---|
| **L1 · Essential** | Bring the melody forward with basic harmonic support and a substantially lighter texture | You want to play the musical outline first |
| **L2 · Easy Musical** | Keep the melody, main harmony and selected characteristic textures while easing demanding accompaniment | You want more of the original character; the default starting point |
| **L3 · Intermediate Reduction** | Retain more voices and detail, with focused changes to difficult technical passages | You have some experience and want to stay closer to the original |

These levels describe arrangement choices, not official examination grades. Different pieces pose different challenges; trying a short sample is more useful than relying on a level label alone.

## Do I need to tell it my level first?

**No questionnaire or formal exam grade is required.**

If you want the first attempt to fit you more closely, useful optional context includes:

- your approximate current level, or a recent piece you can play comfortably;
- your comfortable hand span;
- whether octaves, chords, jumps, tuplets or polyphony are especially difficult;
- why a particular passage is currently unplayable.

A label such as “ABRSM Grade 4” or “three years of lessons” is only a soft signal. **Concrete physical/technical constraints and real playing feedback matter more than a grade label.**

If you do not provide this information, the skill can start from a general level and refine the arrangement after you try it.

## Try a phrase or work on the whole piece

| Length | What you receive | Useful for |
|---|---|---|
| **Mini · Complete phrase** | One coherent musical idea with a natural beginning and ending, usually around half a page to one page | Trying the difficulty and arrangement direction |
| **Full · Complete arrangement** | The major sections and formal route, with any cuts identified in the notes | Practising a coherent version of the whole piece |

Musical coherence and readable notation take priority over page count. Mini controls length through musical selection and arrangement, not by shrinking the notation.

## Where does the source score come from?

A reliable reduction starts by knowing **which source is actually being reduced**.

The skill can work from:

1. **A score you provide**
   - MusicXML / MXL are preferred structured inputs;
   - clear PDFs can also be used, but need transcription and source comparison first.

2. **A reliable public-domain source**
   - if you provide only a work title and the execution environment can access the web, the agent can locate a trustworthy public-domain or otherwise permitted edition before arranging;
   - scholarly/Urtext editions, first-edition scans or clearly identified historical editions are preferred where their use is permitted.

3. **Openly licensed or reliable digital score data**
   - useful as structured input or cross-check evidence;
   - machine-readable does not automatically mean authoritative, so verified source notation wins when sources disagree.

Uncertain sources or notes are not filled in from memory.

## Your first arrangement

The current verified routes include **Codex local, Claude Code, Claude web and ChatGPT Work**, each with a specific tested boundary. See the [installation guide](docs/INSTALL.en.md) for the exact support matrix.

For local Codex use:

1. Download and extract the release package.
2. Put the complete `piano-score-reduction` folder in your project's `.agents/skills/`.
3. Open that project in Codex and ask it to check Python, dependencies and MuseScore.
4. Provide a score—or a title if you want the agent to locate a permitted source—and describe what you want changed.

> **Naming note:** Score Simplifier is the public project name. The current skill ID and install-folder name remain `piano-score-reduction`.

Example:

~~~text
Use the installed piano-score-reduction skill.
Make an L2 Easy Musical arrangement of the score I provided,
starting with a Mini complete phrase.
Keep the main melody and the character of the piece, with fewer accompaniment leaps.
Give me PDF, MusicXML and MIDI, plus the main changes and remaining difficult passages.
~~~

If you are unsure about levels, simply ask for “an easier short version.”

## What you receive

| Deliverable | Use |
|---|---|
| **PDF** | Read, print and practise |
| **MusicXML** | Continue editing in notation software |
| **MIDI** | Listen to notes, rhythm and differences between versions |
| **Optional audio** | Convenient audition when the environment supports it |
| **Arrangement notes / QA** | Understand retained features, changes, remaining difficulties and unperformed checks |

Read the score, listen, then try it at a comfortable tempo. MIDI is a listening reference; your playing experience determines whether the arrangement actually feels right.

## Refine it as you practise

Point to the bars and describe the problem:

> The accompaniment still jumps too far in bars 8–12. Keep the melody, make the accompaniment steadier, and save a new version while retaining the previous one for comparison.

You can also preserve a favourite accompaniment pattern, reduce chord stretches or extend an accepted Mini into Full. Original scores and earlier versions are retained.

## Boundaries and feedback

Simplification can change accompaniment, register or texture. The arrangement notes identify the main trade-offs. If a passage cannot retain its defining features at the requested difficulty, the conflict should be made explicit rather than hidden.

Unclear photographs and some complex notation may need additional transcription or treatment. Explicit pickups, simple whole-measure repeats and first/second endings have checked playback routes. Some bounded grace-note, mordent and one-hand 2–4-note roll treatments are supported as explicit proposals; more complex navigation, ornaments and notation can remain incomplete and must be reported as such.

A successful PDF export does not prove complete playback, source fidelity or musical acceptance. L1–L3 are arrangement targets, not examination grades or guarantees for every player.

For feedback, name the version and bars, then describe what remains difficult or what has lost the character of the original. For execution problems, include the actual error.

The project's own code and documentation use the [MIT license](LICENSE). Score and third-party rights remain separate; see [NOTICE](NOTICE).
