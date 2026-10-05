"""Conservative MusicXML inspection and explicit, hash-bound editing.

No optical transcription, automatic source certification or pedagogical grading.
Time values are exact quarter-note Fractions. Unsupported notation fails closed.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from fractions import Fraction as F
from pathlib import Path
import copy
import hashlib
import json
import math
import zipfile

from lxml import etree as E

VERSION = "0.3.6"
# Gates the scripts must execute and pass; review gates need a person or agent to look.
AUTOMATED_GATES = ("schema", "timeline", "difficulty", "hand_coordination")
PROFILES = {"L1": (7, 2, 7, 3), "L2": (9, 3, 12, 5), "L3": (12, 4, 19, 8)}
TYPES = {"whole": F(4), "half": F(2), "quarter": F(1), "eighth": F(1, 2),
         "16th": F(1, 4), "32nd": F(1, 8), "64th": F(1, 16), "breve": F(8)}
STEPS = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_xml(path):
    data = Path(path).read_bytes()
    if len(data) > 30_000_000:
        raise ValueError("Input exceeds the 30 MB XML/MXL limit")
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if sum(i.file_size for i in z.infolist()) > 30_000_000:
                raise ValueError("Expanded MXL exceeds the limit")
            container = E.fromstring(z.read("META-INF/container.xml"), parser())
            names = container.xpath("//*[local-name()='rootfile']/@full-path")
            if not names or Path(names[0]).is_absolute() or ".." in Path(names[0]).parts:
                raise ValueError("Invalid MXL rootfile path")
            data = z.read(names[0])  # Never extract archive paths onto disk.
    try:
        tree = E.ElementTree(E.fromstring(data, parser()))
    except E.XMLSyntaxError as exc:
        raise ValueError(f"Malformed XML: {exc}") from None
    if tree.getroot().tag != "score-partwise":
        raise ValueError("Only unnamespaced score-partwise MusicXML is supported")
    if any(isinstance(n, E._Entity) for n in tree.iter()):
        raise ValueError("Entity references are unsupported")
    return tree


def parser():
    return E.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)


@dataclass
class Note:
    id: str
    part: str
    measure: str
    index: int
    voice: str
    staff: str
    onset: F
    duration: F
    pitch: int | None
    ties: frozenset
    element: object = field(repr=False)


@dataclass
class Score:
    notes: list
    bars: list
    tempos: list
    errors: list
    unsupported: list
    graces: dict = field(default_factory=dict)  # id -> element; grace notes are not timed events
    play_order: list = field(default_factory=list)  # source measure indices, without changing notation

    @property
    def end(self):
        return max((b["end"] for b in self.bars), default=F(0))


def repeat_order(root):
    """Bounded, non-nested whole-measure repeats, optionally with first/second endings.

    MusicXML repeat times is a total play count. Endings retain their written
    measure numbers; the returned indices describe performance, not new notation.
    Complex navigation stays unsupported rather than guessing a musical route.
    """
    routes, issues = [], []
    for part in root.findall('part'):
        measures = part.findall('measure')
        blocks, spans = [], []
        active_repeat = active_ending = None
        for i, measure in enumerate(measures):
            for barline in measure.findall('barline'):
                location = barline.get('location', 'right')
                if location not in ('left', 'right') and (barline.find('repeat') is not None or barline.find('ending') is not None):
                    issues.append('mid-measure-repeat/ending')
                    continue
                for ending in barline.findall('ending'):
                    try:
                        numbers = frozenset(int(n.strip()) for n in ending.get('number', '').split(','))
                    except ValueError:
                        numbers = frozenset()
                    if numbers not in (frozenset([1]), frozenset([2])):
                        issues.append('ending-numbers-outside-first/second')
                    if ending.get('type') == 'start':
                        if active_ending is not None or location != 'left':
                            issues.append('nested-or-misplaced-ending-start')
                        active_ending = (i, numbers)
                    elif ending.get('type') in ('stop', 'discontinue'):
                        if active_ending is None or active_ending[1] != numbers or location != 'right':
                            issues.append('unpaired-or-misplaced-ending-stop')
                        else:
                            spans.append((active_ending[0], i, numbers))
                        active_ending = None
                    else:
                        issues.append('unknown-ending-type')
                for repeat in barline.findall('repeat'):
                    if repeat.get('after-jump') is not None:
                        issues.append('repeat-after-jump')
                    direction = repeat.get('direction')
                    if direction == 'forward':
                        if active_repeat is not None:
                            issues.append('nested-repeat')
                        active_repeat = i if location == 'left' else i + 1
                    elif direction == 'backward':
                        end = i if location == 'right' else i - 1
                        start = active_repeat if active_repeat is not None else 0
                        if active_repeat is None and blocks:
                            issues.append('ambiguous-implicit-repeat-start')
                        try:
                            count = int(repeat.get('times', '2'))
                        except ValueError:
                            count = 0
                        if not 1 <= count <= 32 or start > end:
                            issues.append('invalid-or-excessive-repeat-count')
                        blocks.append(dict(start=start, end=end, count=count, explicit_times=repeat.get('times') is not None))
                        active_repeat = None
                    else:
                        issues.append('unknown-repeat-direction')
        if active_repeat is not None or active_ending is not None:
            issues.append('unclosed-repeat/ending')
        if any(a['end'] >= b['start'] for a, b in zip(blocks, blocks[1:])):
            issues.append('overlapping-repeat-sections')
        assigned = set()
        for block in blocks:
            first = next((s for s in spans if s[2] == frozenset([1]) and block['start'] <= s[0] <= s[1] == block['end']), None)
            second = next((s for s in spans if s[2] == frozenset([2]) and s[0] == block['end'] + 1), None)
            block.update(first=first, second=second)
            if first is not None or second is not None:
                if first is None or second is None or block['count'] != 2 or block['explicit_times']:
                    issues.append('unsupported-ending-repeat-layout')
                else:
                    assigned.update([first, second])
            if second is not None and any(second[1] >= b['start'] > block['start'] for b in blocks):
                issues.append('repeat-overlaps-second-ending')
        if assigned != set(spans):
            issues.append('ending-without-supported-repeat')
        route, i = [], 0
        by_start = {b['start']: b for b in blocks}
        while i < len(measures) and not issues:
            block = by_start.get(i)
            if block is None:
                route.append(i + 1); i += 1
            else:
                for visit in range(1, block['count'] + 1):
                    for index in range(block['start'], block['end'] + 1):
                        first = block['first']
                        if first and first[0] <= index <= first[1] and visit != 1:
                            continue
                        route.append(index + 1)
                second = block['second']
                if second:
                    route.extend(range(second[0] + 1, second[1] + 2))
                i = (second[1] if second else block['end']) + 1
            if len(route) > 100_000:
                issues.append('performance-route-limit')
        routes.append(route)
    if routes and any(route != routes[0] for route in routes[1:]):
        issues.append('inconsistent-part-repeat-routes')
    return (routes[0] if routes and not issues else []), sorted(set(issues))


def performance_score(score):
    """Project written events onto a validated repeat route; preserve source IDs/elements."""
    if not score.play_order:
        return score
    first_part = score.bars[0]['part']
    source_bars = {b['index']: b for b in score.bars if b['part'] == first_part}
    if score.play_order == list(source_bars):
        return score
    notes, bars, tempos, at = [], [], [], F(0)
    by_bar = defaultdict(list)
    for n in score.notes:
        by_bar[n.index].append(n)
    visits = defaultdict(int)
    for played_index, index in enumerate(score.play_order, 1):
        source = source_bars[index]
        length = source['end'] - source['start']
        visits[index] += 1
        for n in by_bar[index]:
            notes.append(replace(n, onset=at + n.onset - source['start']))
        for b in score.bars:
            if b['index'] == index:
                bars.append(dict(b, start=at, end=at + length, visit=visits[index], played_index=played_index))
        prior = [t for t in score.tempos if t[0] <= source['start']]
        if prior:
            tempos.append((at, prior[-1][1]))  # Restore the written tempo after a repeat jump.
        tempos.extend((at + q - source['start'], bpm) for q, bpm in score.tempos
                      if source['start'] <= q < source['end'])
        at += length
    return Score(notes, bars, sorted(set(tempos)), score.errors, score.unsupported, score.graces)


def parse_score(tree):
    notes, bars, tempos, errors, unsupported, graces = [], [], [], [], [], {}
    root = tree.getroot()
    for tag in ("transpose", "arpeggiate", "ornaments", "unpitched", "cue",
                "tremolo", "measure-repeat", "multiple-rest", "scordatura", "swing"):
        if root.find(".//" + tag) is not None:
            unsupported.append(tag)
    for sound in root.findall(".//sound"):
        if any(k in sound.attrib for k in ("dacapo", "dalsegno", "tocoda", "fine")):
            unsupported.append("playback-navigation")
    for part in root.findall("part"):
        pid, offset, divisions, meter = part.get("id"), F(0), None, None
        for mi, measure in enumerate(part.findall("measure"), 1):
            number = measure.get("number", str(mi))
            cursor, extent, previous = F(0), F(0), None
            ni = 0
            voice_intervals = defaultdict(list)
            if measure.get('non-controlling') == 'yes':
                unsupported.append(f'non-controlling-meter:{pid}:{number}')
            for item in measure:
                if item.tag == "attributes":
                    d = item.findtext("divisions")
                    if d is not None:
                        divisions = F(d)
                        if divisions <= 0:
                            raise ValueError("divisions must be positive")
                    t = item.find("time")
                    if t is not None:
                        if len(t.findall("beats")) != 1 or "+" in (t.findtext("beats") or ""):
                            unsupported.append(f"complex-meter:{pid}:{number}")
                        else:
                            meter = F(t.findtext("beats")) * 4 / F(t.findtext("beat-type"))
                elif item.tag in ("backup", "forward"):
                    if divisions is None:
                        raise ValueError("Missing divisions")
                    cursor += F(item.findtext("duration")) / divisions * (-1 if item.tag == "backup" else 1)
                    if cursor < 0:
                        errors.append(f"negative-cursor:{pid}:{number}")
                    extent = max(extent, cursor)
                    previous = None
                elif item.tag == "direction":
                    sound = item.find("sound")
                    if sound is not None and sound.get("tempo"):
                        shift = F(item.findtext("offset", "0")) / (divisions or 1)
                        tempo = F(sound.get("tempo"))
                        if tempo <= 0:
                            errors.append(f"invalid-tempo:{pid}:{number}")
                        else:
                            tempos.append((offset + cursor + shift, tempo))
                elif item.tag == "note":
                    ni += 1
                    nid = f"{pid}:m{mi}:n{ni}"
                    if item.find("grace") is not None:
                        unsupported.append(f"grace:{nid}")
                        graces[nid] = item
                        continue
                    if divisions is None or item.findtext("duration") is None:
                        raise ValueError(f"Missing duration/divisions at {nid}")
                    duration = F(item.findtext("duration")) / divisions
                    if duration <= 0:
                        errors.append(f"nonpositive-duration:{nid}")
                    voice, staff = item.findtext("voice", "1"), item.findtext("staff", "1")
                    chord = item.find("chord") is not None
                    if chord:
                        if previous is None or previous[1:] != (voice, staff):
                            errors.append(f"invalid-chord-anchor:{nid}")
                        onset = previous[0] if previous else cursor
                    else:
                        onset = cursor
                        previous = (onset, voice, staff)
                        voice_intervals[voice].append((onset, onset + duration, nid))
                        cursor += duration
                    extent = max(extent, onset + duration)
                    p = item.find("pitch")
                    pitch = None
                    if p is not None:
                        alter = F(p.findtext("alter", "0"))
                        if alter.denominator != 1:
                            unsupported.append(f"microtone:{nid}")
                        pitch = 12 * (int(p.findtext("octave")) + 1) + STEPS[p.findtext("step")] + int(alter)
                        if not 0 <= pitch <= 127:
                            errors.append(f"out-of-midi-range:{nid}")
                    ties = frozenset(t.get("type") for t in item.findall("tie"))
                    notation_ties = frozenset(t.get("type") for t in item.findall("notations/tied") if t.get("type") in ("start", "stop"))
                    if ties != notation_ties:
                        errors.append(f"sounding/visual-tie-mismatch:{nid}")
                    typ = item.findtext("type")
                    if typ in TYPES:
                        dots = len(item.findall("dot"))
                        expected = TYPES[typ] * sum((F(1, 2**i) for i in range(dots + 1)), F(0))
                        tm = item.find("time-modification")
                        if tm is not None:
                            try:
                                actual, normal = F(tm.findtext('actual-notes')), F(tm.findtext('normal-notes'))
                            except (TypeError, ValueError, ZeroDivisionError):
                                raise ValueError(f"Malformed time modification at {nid}") from None
                            if actual <= 0 or normal <= 0 or actual.denominator != 1 or normal.denominator != 1:
                                raise ValueError(f"Invalid tuplet counts at {nid}")
                            expected *= normal / actual
                        if expected != duration:
                            errors.append(f"notated-duration-mismatch:{nid}:{duration}!={expected}")
                    elif item.find("rest") is None or item.find("rest").get("measure") != "yes":
                        unsupported.append(f"note-type:{nid}:{typ}")
                    notes.append(Note(nid, pid, number, mi, voice, staff, offset + onset, duration, pitch, ties, item))
            if meter is None:
                errors.append(f"missing-meter:{pid}:{number}")
            elif measure.get('implicit') == 'yes' and not 0 < extent <= meter:
                errors.append(f"implicit-bar-length:{pid}:{number}:{extent}!={meter}")
            elif measure.get('implicit') != 'yes' and extent != meter:
                errors.append(f"bar-length:{pid}:{number}:{extent}!={meter}")
            for intervals in voice_intervals.values():
                for a, b in zip(sorted(intervals), sorted(intervals)[1:]):
                    if b[0] < a[1]:
                        errors.append(f"voice-overlap:{a[2]}:{b[2]}")
            length = extent if measure.get("implicit") == "yes" else (meter or extent)
            bars.append(dict(part=pid, measure=number, index=mi, start=offset, end=offset + length))
            offset += length
    tempos = sorted(set(tempos))
    if any(a[0] == b[0] and a[1] != b[1] for a, b in zip(tempos, tempos[1:])):
        errors.append("conflicting-tempos")
    if len({b["end"] for b in bars if b["index"] == max((x["index"] for x in bars), default=0)}) > 1:
        errors.append("part-duration-mismatch")
    for index in {b['index'] for b in bars}:
        if len({(b['start'], b['end']) for b in bars if b['index'] == index}) > 1:
            errors.append(f'part-bar-grid-mismatch:{index}')
    if not bars:
        errors.append('empty-score')
    order, repeat_issues = repeat_order(root)
    unsupported.extend('repeat-route:' + issue for issue in repeat_issues)
    has_navigation = root.find('.//repeat') is not None or root.find('.//ending') is not None
    return Score(notes, bars, tempos, errors, sorted(set(unsupported)), graces, order if has_navigation else [])


def tied_intervals(score):
    active, result, errors = {}, [], []
    for n in sorted(score.notes, key=lambda n: (n.onset, n.id)):
        if n.pitch is None:
            continue
        key = (n.part, n.voice, n.pitch)
        if "stop" in n.ties:
            prior = active.pop(key, None)
            if prior is None or prior["end"] != n.onset:
                errors.append(f"orphan/nonadjacent-tie-stop:{n.id}")
                prior = dict(start=n.onset, end=n.onset, pitch=n.pitch, ids=[], staff=n.staff, part=n.part, voice=n.voice)
            if prior["staff"] != n.staff:
                errors.append(f"cross-staff-tie-needs-hand-review:{n.id}")
            prior["end"] = n.onset + n.duration
            prior["ids"].append(n.id)
        else:
            prior = dict(start=n.onset, end=n.onset + n.duration, pitch=n.pitch,
                         ids=[n.id], staff=n.staff, part=n.part, voice=n.voice)
        if "start" in n.ties:
            if key in active:
                errors.append(f"overlapping-tie-start:{n.id}")
            active[key] = prior
        else:
            result.append(prior)
    errors += [f"unterminated-tie:{v['ids'][-1]}" for v in active.values()]
    return result, errors


def event_signature(score):
    return [(n.part, n.index, n.voice, n.staff, n.onset, n.duration, n.pitch, sorted(n.ties)) for n in score.notes]


def normalize_order(tree):
    changed = 0
    # Only the known, semantically neutral draft-order faults are repaired.
    for note in tree.findall(".//note"):
        duration = note.find("duration")
        if duration is not None:
            for tie in reversed(note.findall("tie")):
                old = note.index(tie)
                note.remove(tie)
                note.insert(note.index(duration) + 1, tie)
                changed += old != note.index(tie)
        staff = note.find("staff")
        tail = next((child for child in note if child.tag in ("beam", "notations", "lyric", "play", "listen")), None)
        if staff is not None and tail is not None and note.index(staff) > note.index(tail):
            note.remove(staff)
            note.insert(note.index(tail), staff)
            changed += 1
    for direction in tree.findall(".//direction"):
        staff, sound = direction.find("staff"), direction.find("sound")
        if staff is not None and sound is not None and direction.index(staff) > direction.index(sound):
            direction.remove(staff)
            direction.insert(direction.index(sound), staff)
            changed += 1
    return changed


def schema_check(tree, schema_dir):
    if schema_dir is None:
        return dict(status="NOT_RUN", reason="Official MusicXML 4.0 schema directory not supplied")
    class LocalSchema(E.Resolver):
        def resolve(self, url, public_id, context):
            name = url.rsplit("/", 1)[-1]
            if name in ("musicxml.xsd", "xml.xsd", "xlink.xsd"):
                return self.resolve_filename(str(Path(schema_dir).resolve() / name), context)
            raise ValueError("Unexpected schema dependency")
    schema_parser = parser()
    schema_parser.resolvers.add(LocalSchema())
    schema = E.XMLSchema(E.parse(str(Path(schema_dir) / "musicxml.xsd"), schema_parser))
    ok = schema.validate(tree)
    return dict(status="PASS" if ok else "FAIL", errors=[str(e) for e in schema.error_log])


def seconds(at, tempos):
    if not tempos or tempos[0][0] != 0:
        raise ValueError("Explicit initial tempo required")
    total, previous, rate = F(0), F(0), tempos[0][1]
    for position, bpm in tempos[1:]:
        if position > at:
            break
        total += (position - previous) * 60 / rate
        previous, rate = position, bpm
    return total + (at - previous) * 60 / rate


def difficulty(score, hand_map, profile):
    score = performance_score(score)
    intervals, tie_errors = tied_intervals(score)
    if score.errors or score.unsupported or tie_errors:
        return dict(status="NOT_RUN", reason="Timeline must pass first")
    if len({n.part for n in score.notes}) != 1:
        return dict(status="NOT_RUN", reason="Prototype hand map supports one piano part")
    if any(n.staff not in hand_map for n in score.notes if n.pitch is not None):
        return dict(status="NOT_RUN", reason="Explicit complete staff-to-hand declaration required")
    if any(h not in ("R", "L") for h in hand_map.values()):
        raise ValueError("Hand assignments must be R or L")
    if not score.tempos or score.tempos[0][0] != 0:
        return dict(status="NOT_RUN", reason="Explicit initial tempo required")
    limit, count_limit, jump_warn, density_warn = PROFILES[profile]
    violations, hands = [], {}
    for hand in sorted(set(hand_map.values())):
        ns = [n for n in intervals if hand_map[n["staff"]] == hand]
        points = sorted({n[k] for n in ns for k in ("start", "end")})
        slices = []
        for at in points:
            held = [n for n in ns if n["start"] <= at < n["end"]]
            pitches = sorted({n["pitch"] for n in held})
            if not pitches:
                continue
            span = pitches[-1] - pitches[0]
            row = dict(at=str(at), span=span, count=len(pitches), ids=[i for n in held for i in n["ids"]])
            slices.append(row)
            if span > limit or len(pitches) > count_limit:
                violations.append(dict(hand=hand, **row))
        groups = defaultdict(list)
        for n in ns:
            groups[n["start"]].append(n["pitch"])
        starts = sorted(groups)
        # Centroid displacement is an advisory proxy, not a fingering/hand-motion solver.
        jumps = [dict(at=str(b), semitones=abs(float(F(sum(groups[b]), len(groups[b])) - F(sum(groups[a]), len(groups[a])))),
                      seconds=float(seconds(b, score.tempos) - seconds(a, score.tempos))) for a, b in zip(starts, starts[1:])]
        times = [seconds(q, score.tempos) for q in starts]
        density = max((sum(t <= x < t + 1 for x in times) for t in times), default=0)
        values = sorted(j["semitones"] for j in jumps)
        hands[hand] = dict(max_span=max((r["span"] for r in slices), default=0),
                           max_simultaneous_pitches=max((r["count"] for r in slices), default=0),
                           max_centroid_jump=max(values, default=0),
                           p95_centroid_jump=values[max(0, math.ceil(len(values) * .95) - 1)] if values else 0,
                           jump_advisories=[j for j in jumps if j["semitones"] > jump_warn],
                           max_attack_groups_per_second=density, density_advisory=density > density_warn)
    return dict(status="FAIL" if violations else "PASS", profile=profile, profile_version="seed-0.1",
                interpretation="Uncalibrated constraints; notation durations held by fingers; pedal never shortens them",
                hand_map=hand_map, hands=hands, violations=violations)


def analyze(tree, schema_dir=None, hand_map=None, profile="L2"):
    score = parse_score(tree)
    played = performance_score(score)
    intervals, tie_errors = tied_intervals(played)
    errors = score.errors + tie_errors
    schema = schema_check(tree, schema_dir)
    timeline = dict(status="FAIL" if errors else ("NOT_RUN" if score.unsupported else "PASS"),
                    errors=errors, unsupported=score.unsupported)
    ergonomics = difficulty(score, hand_map or {}, profile)
    gates = dict(schema=schema, timeline=timeline, difficulty=ergonomics,
                 hand_coordination=hand_coordination(score, hand_map or {}),
                 source_fidelity=dict(status="NOT_RUN"), musical_review=dict(status="NOT_RUN"),
                 layout=dict(status="NOT_RUN"), human_playing=dict(status="NOT_RUN"))
    status = "FAIL" if any(g["status"] == "FAIL" for g in gates.values()) else "REVIEW_REQUIRED"
    return dict(tool_version=VERSION, overall=status, measures=len(score.bars),
                pitched_notation_events=sum(n.pitch is not None for n in score.notes),
                merged_sounding_events=len(intervals), duration_quarters=str(score.end),
                playback_duration_quarters=str(played.end), playback_order=score.play_order,
                tempos=[dict(at=str(q), quarter_bpm=str(bpm)) for q, bpm in score.tempos], gates=gates)


def hand_coordination(score, hand_map):
    """Check finger-held key collisions separately from advisory register overlap.

    This does not solve fingering. A declared shared/unison realization must first
    be represented as one hand's event; two independent finger holds cannot pass.
    """
    score = performance_score(score)
    ns, errors = tied_intervals(score)
    if score.errors or score.unsupported or errors:
        return dict(status='NOT_RUN', reason='Supported valid timeline required')
    if len({n.part for n in score.notes}) != 1:
        return dict(status='NOT_RUN', reason='One piano part required')
    if any(n['staff'] not in hand_map for n in ns) or any(h not in ('L','R') for h in hand_map.values()):
        return dict(status='NOT_RUN', reason='Explicit complete hand declaration required')
    points = sorted({n[k] for n in ns for k in ('start','end')})
    shared, crossing = [], []
    for at, end in zip(points, points[1:]):
        held = {hand:[n for n in ns if hand_map[n['staff']]==hand and n['start']<=at<n['end']]
                for hand in ('L','R')}
        pitches = {h:sorted({n['pitch'] for n in held[h]}) for h in held}
        if not pitches['L'] or not pitches['R']:
            continue
        bar = next(b for b in score.bars if b['start'] <= at < b['end'])
        row = dict(measure=bar['measure'], at=str(at), end=str(end),
                   beat_quarters=str(at-bar['start']), left=pitches['L'], right=pitches['R'])
        intersection = sorted(set(pitches['L']) & set(pitches['R']))
        if intersection:
            shared.append(dict(**row, pitches=intersection,
                               ids=[i for h in held.values() for n in h if n['pitch'] in intersection for i in n['ids']]))
        if max(pitches['L']) > min(pitches['R']):
            crossing.append(row)
    return dict(status='FAIL' if shared else 'PASS', policy='hand-coordination-0.1',
                shared_key_windows=shared, register_overlap_advisories=crossing,
                interpretation='Finger holds from written durations/ties; shared keys require explicit consolidation; register overlap is advisory, not proof of physical crossing')


def apply_plan(tree, source_hash, plan):
    if plan.get("input_sha256") != source_hash:
        raise ValueError("Plan input SHA-256 does not match")
    score = parse_score(tree)
    notes = {n.id: n for n in score.notes}
    protected = set(plan.get("protected_ids", []))
    if not protected.issubset(set(notes) | set(score.graces)):
        raise ValueError("Unknown protected event IDs")
    # A tied note may only change together with its whole tie chain, by the same operation.
    chains = {}
    links = defaultdict(set)
    for interval in tied_intervals(performance_score(score))[0]:
        for i in interval["ids"]:
            links[i].update(interval['ids'])
    for nid in links:
        pending, group = [nid], set()
        while pending:
            current = pending.pop()
            if current not in group:
                group.add(current)
                pending.extend(links[current] - group)
        chains[nid] = sorted(group)
    planned = {c["id"]: (c["op"], c.get("octaves")) for c in plan.get("edits", [])}
    # Direction IDs part:mN:dK name the K-th <direction> of the N-th measure in this input.
    directions = {f"{part.get('id')}:m{mi}:d{k}": d for part in tree.getroot().findall("part")
                  for mi, measure in enumerate(part.findall("measure"), 1)
                  for k, d in enumerate(measure.findall("direction"), 1)}
    clefs = {f"{part.get('id')}:m{mi}:c{k}": c for part in tree.getroot().findall("part")
             for mi, measure in enumerate(part.findall("measure"), 1)
             for k, c in enumerate(measure.findall("attributes/clef"), 1)}
    seen, changes = set(), []
    for change in plan.get("edits", []):
        nid = change["id"]
        if nid in seen or nid in protected or not change.get("reason"):
            raise ValueError(f"Duplicate, protected or unexplained edit: {nid}")
        seen.add(nid)
        if change["op"] == "set_clef":
            target = clefs.get(nid)
            sign, line = change.get('sign'), change.get('line')
            if target is None or target.find('clef-octave-change') is not None:
                raise ValueError(f"set_clef needs an existing non-transposing clef: {nid}")
            if sign not in ('G','F','C') or type(line) is not int or not 1 <= line <= 5:
                raise ValueError(f"Invalid clef sign/line: {nid}")
            before = dict(sign=target.findtext('sign'), line=target.findtext('line'))
            target.find('sign').text = sign
            line_element = target.find('line')
            if line_element is None:
                line_element = E.SubElement(target, 'line')
            line_element.text = str(line)
            changes.append(dict(**change, before_clef=before, after_clef=dict(sign=sign,line=str(line)),
                                before_midi=None, after_midi=None))
            continue
        if change['op'] == 'realize_grace':
            el = score.graces.get(nid)
            following = el.getnext() if el is not None else None
            principal = next((n for n in score.notes if n.element is following), None)
            next_note = next(following.itersiblings('note'), None) if principal is not None else None
            grace_mark = el.find('grace') if el is not None else None
            grace_slurs = el.findall('notations/slur') if el is not None else []
            main_slurs = following.findall('notations/slur') if principal is not None else []
            paired = (not grace_slurs and not main_slurs or len(grace_slurs)==len(main_slurs)==1
                      and grace_slurs[0].get('type')=='start' and main_slurs[0].get('type')=='stop'
                      and grace_slurs[0].get('number','1')==main_slurs[0].get('number','1'))
            if (el is None or principal is None or principal.pitch is None
                    or change.get('steal') != 'following'
                    or any(k != 'slash' for k in grace_mark.attrib)
                    or el.find('pitch') is None or el.find('chord') is not None
                    or following.find('chord') is not None
                    or el.find('type') is None or following.find('type') is None
                    or next_note is not None and next_note.find('chord') is not None
                    or el.findtext('voice','1') != principal.voice or el.findtext('staff','1') != principal.staff
                    or principal.id in protected or principal.id in planned
                    or principal.ties and (principal.ties != {'start'} or len(chains.get(principal.id,[]))<2)
                    or not paired
                    or any(x.tag!='slur' for x in el.findall('notations/*'))
                    or any(x.tag not in ('tied','slur') for x in following.findall('notations/*'))
                    or any(x.tag not in ('grace','pitch','voice','type','dot','accidental','staff','notations') for x in el)
                    or any(x.tag not in ('pitch','duration','tie','voice','type','dot','accidental','staff','notations') for x in following)):
                raise ValueError(f'realize_grace needs one plain grace and immediate single principal; explicitly steal from following, with at most a valid starting tie or adjacent slur pair: {nid}')
            pulse = edit_pulse(change,nid)
            durations = [pulse,principal.duration-pulse]
            divisions=F(following.findtext('duration'))/principal.duration
            values=[written_value(d,divisions,nid) for d in durations]
            p=el.find('pitch');alter=F(p.findtext('alter','0'))
            grace_pitch=12*(int(p.findtext('octave'))+1)+STEPS[p.findtext('step')]+int(alter)
            if alter.denominator!=1 or not 0<=grace_pitch<=127:
                raise ValueError(f'Grace pitch must be an integer MIDI pitch: {nid}')
            el.remove(grace_mark)
            duration_element=E.Element('duration');duration_element.text=str(int(pulse*divisions))
            el.insert(el.index(p)+1,duration_element)
            for target,d,(typ,dots) in zip([el,following],durations,values):
                target.find('duration').text=str(int(d*divisions))
                target.find('type').text=typ
                for dot in target.findall('dot'):target.remove(dot)
                for _ in range(dots):target.insert(target.index(target.find('type'))+1,E.Element('dot'))
            changes.append(dict(**change,before_midi=None,after_midi=grace_pitch,
                treatment='explicit-onbeat-grace-stealing-from-following',realized_count=1,principal_id=principal.id,
                principal_before=dict(at=str(principal.onset),duration=str(principal.duration)),
                principal_after=dict(at=str(principal.onset+pulse),duration=str(principal.duration-pulse)),
                interpretation='Explicit on-beat quantized proposal, not the source grace performance or certified historical practice'))
            continue
        if change["op"] == "remove_grace":
            # Ornament removal is an arrangement decision recorded like any other edit.
            grace = score.graces.get(nid)
            if grace is None or grace.getparent() is None:
                raise ValueError(f"remove_grace needs an existing grace note: {nid}")
            voice = grace.findtext("voice", "1")
            for slur in grace.findall("notations/slur"):
                if slur.get("type") != "start":
                    raise ValueError(f"Grace note ends a slur; edit the slur explicitly: {nid}")
                # Drop the slur's matching stop on a later note of the same voice in this measure.
                for later in grace.itersiblings("note"):
                    stop = next((x for x in later.findall("notations/slur") if x.get("type") == "stop"
                                 and x.get("number", "1") == slur.get("number", "1")), None)
                    if later.findtext("voice", "1") == voice and stop is not None:
                        strip(later, stop)
                        break
                else:
                    raise ValueError(f"Grace slur has no stop in this measure: {nid}")
            grace.getparent().remove(grace)
            changes.append(dict(**change, before_midi=None, after_midi=None))
            continue
        if change["op"] == "remove_direction":
            # Direction IDs: part:mN:dK = K-th <direction> (1-based) in the N-th measure of the part.
            target = directions.get(nid)
            if target is None or target.getparent() is None or target.find("sound") is not None:
                raise ValueError(f"remove_direction needs an existing direction without playback sound: {nid}")
            text = " ".join(t.strip() for t in target.itertext() if t.strip()) or target.find("direction-type/*").tag
            target.getparent().remove(target)
            changes.append(dict(**change, before_midi=None, after_midi=None, removed=text))
            continue
        if nid not in notes:
            raise ValueError(f"Unknown edit ID: {nid}")
        n = notes[nid]
        if n.pitch is None:
            raise ValueError(f"Only pitched events may be edited: {nid}")
        if change['op'] == 'realize_arpeggio':
            el=n.element;group=[n]
            sibling=el.getnext()
            while sibling is not None and sibling.tag=='note' and sibling.find('chord') is not None:
                member=next((x for x in score.notes if x.element is sibling),None)
                if member is None:break
                group.append(member);sibling=sibling.getnext()
            group_ids={x.id for x in group};order=change.get('order',[])
            marked=[x for x in score.notes if x.onset==n.onset and x.element.find('notations/arpeggiate') is not None]
            directions={x.element.find('notations/arpeggiate').get('direction') for x in marked}
            numbers={x.element.find('notations/arpeggiate').get('number','1') for x in marked}
            if (el.find('chord') is not None or not 2<=len(group)<=4 or len(marked)!=len(group) or len(numbers)!=1
                    or any(x.id not in group_ids for x in marked)
                    or not isinstance(order,list) or len(order)!=len(group)
                    or any(type(i) is not str for i in order) or set(order)!=group_ids
                    or len({x.pitch for x in group})!=len(group)
                    or group_ids & protected or any(x.id in planned for x in group if x.id!=nid)
                    or any(x.staff!=n.staff or x.voice!=n.voice or x.part!=n.part or x.duration!=n.duration
                           or x.pitch is None or x.ties for x in group)
                    or any(any(y.tag!='arpeggiate' for y in x.element.findall('notations/*'))
                           or any(y.tag not in ('chord','pitch','duration','voice','type','dot','accidental','staff','notations') for y in x.element)
                           or len(x.element.findall('notations/arpeggiate'))>1
                           or any(k not in ('direction','number') for y in x.element.findall('notations/arpeggiate') for k in y.attrib)
                           for x in group)):
                raise ValueError(f'realize_arpeggio needs one untied 2-4-note single-voice/staff chord, all source marks in that group, and explicit complete order: {nid}')
            ordered=[notes[x] for x in order];pitches=[x.pitch for x in ordered]
            if (directions- {None,'up','down'} or len(directions-{None})>1
                    or 'up' in directions and pitches!=sorted(pitches)
                    or 'down' in directions and pitches!=sorted(pitches,reverse=True)):
                raise ValueError(f'Explicit order conflicts with the source arpeggio direction: {nid}')
            pulse=edit_pulse(change,nid);divisions=F(el.findtext('duration'))/n.duration
            durations=[pulse]*(len(group)-1)+[n.duration-(len(group)-1)*pulse]
            values=[written_value(d,divisions,nid) for d in durations]
            elements=[];source_ids=[]
            for stage,(duration,(typ,dots)) in enumerate(zip(durations,values)):
                for k,original in enumerate(ordered[:stage+1]):
                    new=E.Element('note')
                    if k:E.SubElement(new,'chord')
                    new.append(copy.deepcopy(original.element.find('pitch')))
                    E.SubElement(new,'duration').text=str(int(duration*divisions))
                    ties=(['stop'] if k<stage else [])+(['start'] if stage<len(group)-1 else [])
                    for kind in ties:E.SubElement(new,'tie',type=kind)
                    E.SubElement(new,'voice').text=n.voice;E.SubElement(new,'type').text=typ
                    for _ in range(dots):E.SubElement(new,'dot')
                    if original.element.find('accidental') is not None:new.append(copy.deepcopy(original.element.find('accidental')))
                    E.SubElement(new,'staff').text=n.staff
                    if ties:
                        holder=E.SubElement(new,'notations')
                        for kind in ties:E.SubElement(holder,'tied',type=kind)
                    elements.append(new);source_ids.append(original.id)
            parent,at=el.getparent(),el.getparent().index(el)
            for original in group[1:]:parent.remove(original.element)
            el[:]=list(elements[0])
            for k,new in enumerate(elements[1:],1):parent.insert(at+k,new)
            changes.append(dict(**change,before_midi=n.pitch,after_midi=pitches[0],
                treatment='explicit-staggered-chord-with-written-ties',realized_count=len(elements),
                output_source_ids=source_ids,
                realized_events=[dict(source_id=x.id,pitch=x.pitch,start=str(x.onset+k*pulse),end=str(x.onset+x.duration)) for k,x in enumerate(ordered)],
                interpretation='Explicit rolled-chord pulse/order proposal; end times and hand/staff retained, not certified expressive/historical performance'))
            continue
        if change["op"] == "realize_ornament":
            # Fully specified principal-neighbour alternation; never infer performance practice.
            # Do not infer the neighbouring accidental or historical performance practice.
            el = n.element
            marks = el.findall('notations/ornaments/*')
            tag = change.get('ornament')
            next_note = next(el.itersiblings('note'), None)
            long = len(marks) == 1 and marks[0].attrib == {'long': 'yes'}
            cycles = change.get('cycles', 1)
            valid_cycles = type(cycles) is int and (2 <= cycles <= 8 if long else cycles == 1)
            valid_ties = not n.ties or (long and n.ties == {'start'} and len(chains.get(nid, [])) > 1)
            notation_tags = ('ornaments','tied') if long else ('ornaments',)
            if (tag not in ('mordent','inverted-mordent') or len(marks) != 1 or marks[0].tag != tag
                    or (bool(marks[0].attrib) and not long) or not valid_cycles or not valid_ties
                    or el.find('chord') is not None
                    or next_note is not None and next_note.find('chord') is not None
                    or el.find('time-modification') is not None
                    or any(x.tag not in notation_tags for x in el.findall('notations/*'))
                    or any(x.tag not in ('pitch','duration','tie','voice','type','dot','accidental','staff','notations') for x in el)):
                raise ValueError(f"realize_ornament needs a plain untied mordent, or long=yes with 2-8 explicit cycles and at most a valid starting tie: {nid}")
            neighbor = change.get('neighbor', {})
            step, alter, octave = neighbor.get('step'), neighbor.get('alter',0), neighbor.get('octave')
            if step not in STEPS or type(alter) is not int or alter not in (-1,0,1) or type(octave) is not int:
                raise ValueError(f"Explicit spelled neighbor pitch required: {nid}")
            pitch = 12*(octave+1)+STEPS[step]+alter
            displacement = pitch-n.pitch
            letters=list(STEPS)
            neighbor_letter=letters[(letters.index(el.findtext('pitch/step'))+(-1 if tag=='mordent' else 1))%7]
            if (step!=neighbor_letter or not 0 <= pitch <= 127
                    or displacement not in ((-2,-1) if tag=='mordent' else (1,2))):
                raise ValueError(f"Neighbor must be a spelled semitone/whole tone in the ornament direction: {nid}")
            try:
                if type(change['pulse_quarters']) not in (str,int):
                    raise ValueError('Pulse must be a rational string or integer')
                pulse = F(change['pulse_quarters'])
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                raise ValueError(f"Explicit rational pulse_quarters required: {nid}") from None
            durations = [pulse]*(2*cycles)+[n.duration-2*cycles*pulse]
            divisions = F(el.findtext('duration'))/n.duration
            notation = []
            for duration in durations:
                value = next(((typ,dots) for typ,base in TYPES.items() for dots in range(4)
                              if base*sum((F(1,2**i) for i in range(dots+1)),F(0))==duration),None)
                if duration<=0 or (duration*divisions).denominator!=1 or value is None:
                    raise ValueError(f"Ornament values must be positive exact representable note values: {nid}")
                notation.append(value)
            elements=[]
            for k,(duration,(typ,dots)) in enumerate(zip(durations,notation)):
                is_neighbor = k % 2 == 1
                new=E.Element('note');p=copy.deepcopy(el.find('pitch')) if not is_neighbor else E.Element('pitch')
                if is_neighbor:
                    E.SubElement(p,'step').text=step
                    if alter: E.SubElement(p,'alter').text=str(alter)
                    E.SubElement(p,'octave').text=str(octave)
                new.append(p)
                E.SubElement(new,'duration').text=str(int(duration*divisions))
                if k == len(durations)-1:
                    for tie in el.findall('tie'): new.append(copy.deepcopy(tie))
                E.SubElement(new,'voice').text=n.voice
                E.SubElement(new,'type').text=typ
                for _ in range(dots): E.SubElement(new,'dot')
                # Explicit accidentals prevent an altered neighbor from leaking into the return.
                accidental = alter if is_neighbor else int(F(p.findtext('alter','0')))
                E.SubElement(new,'accidental').text={-1:'flat',0:'natural',1:'sharp'}.get(accidental,'')
                if accidental not in (-1,0,1):
                    raise ValueError(f"Principal accidental needs separate treatment: {nid}")
                E.SubElement(new,'staff').text=n.staff
                if k == len(durations)-1 and el.findall('notations/tied'):
                    holder=E.SubElement(new,'notations')
                    for tied in el.findall('notations/tied'): holder.append(copy.deepcopy(tied))
                elements.append(new)
            # Keep the original first element identity for version mapping; record expansion.
            parent, at = el.getparent(), el.getparent().index(el)
            el[:] = list(elements[0])
            for k,new in enumerate(elements[1:],1): parent.insert(at+k,new)
            changes.append(dict(**change, before_midi=n.pitch, after_midi=n.pitch,
                treatment='explicit-long-principal-neighbor-alternation' if long else 'explicit-principal-neighbor-principal',
                realized_count=len(elements),
                realized_events=[dict(pitch=pitch if k%2 else n.pitch,duration_quarters=str(d))
                                 for k,d in enumerate(durations)],
                interpretation='Agent-authored exact rhythm/pitch proposal; not certified historical ornament interpretation'))
            continue
        if change["op"] in ("remove_ornament", "remove_arpeggio"):
            # An explicit omission is an arrangement loss, never a playback realization.
            # Remove only the named symbol; keep slurs, ties and other note notation.
            tag = change.get("ornament") if change["op"] == "remove_ornament" else "arpeggiate"
            allowed = {"trill-mark", "mordent", "inverted-mordent", "turn", "inverted-turn",
                       "delayed-turn", "delayed-inverted-turn", "vertical-turn", "shake", "schleifer"}
            if change["op"] == "remove_ornament" and tag not in allowed:
                raise ValueError(f"Unsupported ornament omission: {tag}")
            targets = n.element.findall("notations/" + ("ornaments/" if tag != "arpeggiate" else "") + tag)
            if len(targets) != 1:
                raise ValueError(f"Omission needs exactly one existing {tag}: {nid}")
            target = targets[0]
            # Accidental marks qualify ornaments; leaving an orphan changes their meaning.
            if tag != "arpeggiate" and target.getparent().find("accidental-mark") is not None:
                raise ValueError(f"Ornament has an accidental mark; author an explicit treatment: {nid}")
            strip(n.element, target)
            changes.append(dict(**change, before_midi=n.pitch, after_midi=n.pitch,
                                removed=tag, treatment="explicit-notation-omission"))
            continue
        if n.ties and any(planned.get(i) != planned[nid] for i in chains.get(nid, [nid])):
            raise ValueError(f"Tied event {nid} must be edited together with its whole tie chain {chains.get(nid)}")
        if change["op"] == "octave":
            shift = change["octaves"]
            if type(shift) is not int or not -2 <= shift <= 2 or not 0 <= n.pitch + 12 * shift <= 127:
                raise ValueError(f"Invalid octave edit: {nid}")
            octave = n.element.find("pitch/octave")
            octave.text = str(int(octave.text) + shift)
            changes.append(dict(**change, before_midi=n.pitch, after_midi=n.pitch + 12 * shift))
        elif change["op"] == "remove_chord_doubling":
            peers = [p for p in notes.values() if p.id != nid and p.part == n.part and p.voice == n.voice
                     and p.onset == n.onset and p.duration == n.duration and p.pitch is not None
                     and p.pitch % 12 == n.pitch % 12 and p.element.getparent() is not None]
            if n.element.find("chord") is None or not peers:
                raise ValueError(f"Removal requires a redundant chord member, not its anchor: {nid}")
            n.element.getparent().remove(n.element)
            changes.append(dict(**change, before_midi=n.pitch, after_midi=None))
        elif change["op"] == "remove_chord_member":
            # Thinning a non-doubled chord tone is a musical choice; the reason records it.
            el = n.element
            if el.getparent() is None:
                raise ValueError(f"Event already removed: {nid}")
            if el.find("chord") is not None:
                if el.find("notations/slur") is not None:
                    raise ValueError(f"Chord member carries slur endpoints; edit the slur explicitly: {nid}")
                el.getparent().remove(el)
                changes.append(dict(**change, before_midi=n.pitch, after_midi=None))
                continue
            # Removing the anchor: the next chord member's pitch moves into the anchor element,
            # which keeps anchor-level beams, slurs, tuplets and directions in place.
            member = el.getnext()
            peer = next((p for p in notes.values() if p.element is member), None)
            if member is None or member.tag != "note" or member.find("chord") is None or peer is None:
                raise ValueError(f"Anchor removal needs another chord member to keep: {nid}")
            if peer.ties or member.find("notations") is not None:
                raise ValueError(f"Promoted chord member must be untied and carry no notations: {peer.id}")
            if peer.id in {c["id"] for c in plan.get("edits", [])}:
                raise ValueError(f"Promoted chord member {peer.id} is edited elsewhere in this plan")
            el.replace(el.find("pitch"), copy.deepcopy(member.find("pitch")))
            untie(el)
            for old in el.findall("accidental"):
                el.remove(old)
            if member.find("accidental") is not None:
                anchor_at = max(el.index(x) for x in el if x.tag in ("type", "dot"))
                el.insert(anchor_at + 1, copy.deepcopy(member.find("accidental")))
            el.getparent().remove(member)
            notes[peer.id] = Note(**{**peer.__dict__, "element": el})
            changes.append(dict(**change, before_midi=n.pitch, after_midi=None, kept_event=peer.id,
                                note="Anchor removed; the kept member now occupies the anchor element"))
        elif change["op"] == "rest":
            # Replace a single sounding note with a rest of identical written duration.
            el = n.element
            following = el.getnext()
            while following is not None and following.tag != "note":
                following = following.getnext() if following.tag not in ("backup", "forward") else None
            if el.find("chord") is not None or (following is not None and following.find("chord") is not None):
                raise ValueError(f"Rest replacement needs a single note; remove chord members first: {nid}")
            if el.find("notations/slur") is not None:
                raise ValueError(f"Note carries slur endpoints; edit the slur explicitly: {nid}")
            untie(el)
            for tag in ("pitch", "accidental", "stem", "notehead", "lyric"):
                for old in el.findall(tag):
                    el.remove(old)
            for marks in el.findall("notations"):
                for old in marks.findall("articulations") + marks.findall("ornaments") + marks.findall("technical"):
                    marks.remove(old)
                if len(marks) == 0:
                    el.remove(marks)
            el.insert(0, E.Element("rest"))
            changes.append(dict(**change, before_midi=n.pitch, after_midi=None))
        else:
            raise ValueError(f"Unsupported edit operation: {change['op']}")
    return changes


def edit_pulse(change,nid):
    try:
        value=change['pulse_quarters']
        if type(value) not in (str,int):raise ValueError('Exact pulse required')
        pulse=F(value)
        if pulse<=0:raise ValueError('Positive pulse required')
        return pulse
    except (KeyError,ValueError,TypeError,ZeroDivisionError):
        raise ValueError(f'Explicit positive rational pulse_quarters required: {nid}') from None


def written_value(duration,divisions,nid):
    value=next(((typ,dots) for typ,base in TYPES.items() for dots in range(4)
                if base*sum((F(1,2**i) for i in range(dots+1)),F(0))==duration),None)
    if duration<=0 or (duration*divisions).denominator!=1 or value is None:
        raise ValueError(f'Treatment values must be positive exact representable note values: {nid}')
    return value


def strip(note, mark):
    """Remove one mark and emptied notation containers, preserving sibling symbols."""
    holder = mark.getparent()
    holder.remove(mark)
    while holder is not note and len(holder) == 0:
        parent = holder.getparent()
        parent.remove(holder)
        holder = parent


def untie(note):
    for tie in note.findall("tie"):
        note.remove(tie)
    for tied in note.findall("notations/tied"):
        strip(note, tied)


def write_xml(tree, path):
    path = Path(path)
    if path.exists():
        raise ValueError(f"Output already exists; choose a new version: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding="UTF-8", xml_declaration=True, pretty_print=True)


def export_midi(tree, path):
    import mido
    written = parse_score(tree)
    score = performance_score(written)
    notes, errors = tied_intervals(score)
    if score.errors or score.unsupported or errors:
        raise ValueError("MIDI export requires a supported, valid timeline")
    seconds(score.end, score.tempos)  # Require a tempo starting at zero.
    if len({n.part for n in score.notes}) != 1:
        raise ValueError("MIDI prototype supports one part")
    if Path(path).exists():
        raise ValueError("MIDI output already exists")
    tpq = math.lcm(480, *(n[k].denominator for n in notes for k in ("start", "end")))
    if tpq > 32767:
        raise ValueError("Rhythmic precision exceeds SMF tick limit")
    midi, track = mido.MidiFile(type=1, ticks_per_beat=tpq), mido.MidiTrack()
    midi.tracks.append(track)
    voices = sorted({n['voice'] for n in notes})
    channels = [c for c in range(16) if c != 9]
    if len(voices) > len(channels):
        raise ValueError("Too many voices for distinct piano MIDI channels")
    channel_map = dict(zip(voices, channels))
    events = [(0, 0, mido.Message("program_change", program=0, channel=channel_map[v])) for v in voices]
    for at, bpm in score.tempos:
        if (at * tpq).denominator != 1:
            raise ValueError("Tempo position is not representable")
        events.append((int(at * tpq), 1, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(float(bpm)))))
    for n in notes:
        channel = channel_map[n['voice']]
        events += [(int(n["start"] * tpq), 3, mido.Message("note_on", note=n["pitch"], velocity=64, channel=channel)),
                   (int(n["end"] * tpq), 2, mido.Message("note_off", note=n["pitch"], velocity=0, channel=channel))]
    # Distinct voices get distinct channels; same-voice duplicate pitches are rejected.
    by_pitch = defaultdict(list)
    for n in notes:
        by_pitch[(n['voice'], n["pitch"])].append((n["start"], n["end"]))
    for intervals in by_pitch.values():
        if any(b[0] < a[1] for a, b in zip(sorted(intervals), sorted(intervals)[1:])):
            raise ValueError("Overlapping same-pitch events within one voice")
    previous = 0
    for tick, _, message in sorted(events, key=lambda x: (x[0], x[1])):
        track.append(message.copy(time=tick - previous))
        previous = tick
    track.append(mido.MetaMessage("end_of_track", time=int(score.end * tpq) - previous))
    midi.save(str(path))
    # Independent serialized readback, including tie lengths and simultaneous notes.
    readback, active, tick = [], {}, 0
    for message in mido.MidiFile(str(path)).tracks[0]:
        tick += message.time
        if message.type == "note_on" and message.velocity > 0:
            key = (message.channel, message.note)
            if key in active:
                raise ValueError("Overlapping MIDI note-on")
            active[key] = tick
        elif message.type == "note_off" or message.type == "note_on" and message.velocity == 0:
            key = (message.channel, message.note)
            readback.append((message.channel, message.note, F(active.pop(key), tpq), F(tick, tpq)))
    expected = [(channel_map[n['voice']], n["pitch"], n["start"], n["end"]) for n in notes]
    if active or sorted(readback) != sorted(expected) or F(tick, tpq) != score.end:
        raise ValueError("Serialized MIDI does not match the score")
    return dict(status="PASS", matched_events=len(expected), ticks_per_quarter=tpq,
                voice_channels=channel_map,
                duration_seconds=float(seconds(score.end, score.tempos)),
                playback_order=written.play_order,
                playback="Literal pitch/onset/duration/tempo, uniform velocity; no expressive/pedal rendering",
                listening="NOT_RUN")


def dump(value, path):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
