#!/usr/bin/env python3
"""One reproducible run: inspect -> hash-bound plan -> controlled edit -> QA -> PDF/MIDI -> manifest.

This is a delivery pipeline around the narrow deterministic editor, not an automatic
arranger. Musical decisions arrive as an explicit plan written by the agent. Every
run writes a new version directory; inputs and earlier versions are never modified.

Exit codes: 0 automated gates passed (overall still REVIEW_REQUIRED until reviews are
recorded); 1 ERROR (malformed input, rejected plan, broken lineage); 2 FAIL (a gate
failed); 3 INCOMPLETE (a mandatory automated gate was not executed).
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from lxml import etree as E

from score_core import (AUTOMATED_GATES, VERSION, analyze, apply_plan, dump, event_signature,
                        export_midi, normalize_order, parse_score, performance_score, read_xml, sha,
                        tied_intervals, write_xml)

MANIFEST = "manifest.json"
REVIEW_CHECKS = {
    "page_inspection": "Every PDF page viewed for clefs, accidentals, ties, tuplets, spacing and ending",
    "source_fidelity": "Output compared with the cited source for the declared measure scope",
    "musical_review": "Protected melody/bass/harmony and stated losses reviewed musically",
    "human_listening": "A person listened to the audio or MIDI",
    "human_playing": "A person tried playing it at the stated tempo",
}
HUMAN_ONLY = ("human_listening", "human_playing")
SKILL_ROOT = Path(__file__).resolve().parents[1]


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def find_mscore(explicit=None):
    candidates = [explicit] if explicit else [shutil.which(n) for n in ("mscore", "musescore", "MuseScore4")] + [
        "/Applications/MuseScore 4.app/Contents/MacOS/mscore", shutil.which("mscore3")]
    return next((p for p in candidates if p and Path(p).is_file()), None)


def parse_scope(text, measures):
    """'1-8' or '6' or '3,5-6' -> set of 1-based measure positions; None means all."""
    if not text:
        return None
    chosen = set()
    for part in text.split(","):
        lo, _, hi = part.strip().partition("-")
        chosen.update(range(int(lo), int(hi or lo) + 1))
    if not chosen or min(chosen) < 1 or max(chosen) > measures:
        raise ValueError(f"Measure scope {text!r} is outside 1-{measures}")
    return chosen


def outer_voice_changes(before, after):
    """Where the lowest (bass) or highest (top line) sounding pitch differs after editing.

    Compared at attack and release boundaries, over all staves, using written
    durations and merged ties. An edited silence records the lost pitch as None.
    """
    before, after = performance_score(before), performance_score(after)
    def sounding(score):
        return tied_intervals(score)[0]
    a, b = sounding(before), sounding(after)
    found = []
    boundaries = {point for n in a + b for point in (n["start"], n["end"])}
    for at in sorted(boundaries):
        was = [n["pitch"] for n in a if n["start"] <= at < n["end"]]
        now = [n["pitch"] for n in b if n["start"] <= at < n["end"]]
        if not was:
            continue
        bar = next(x for x in before.bars if x["start"] <= at < x["end"])
        where = dict(measure=bar["index"], beat=float(at - bar["start"]) + 1)
        bass = min(now) if now else None
        top = max(now) if now else None
        if bass != min(was):
            found.append(dict(voice="bass", before=min(was), after=bass, **where))
        if top != max(was):
            found.append(dict(voice="top", before=max(was), after=top, **where))
    return found


def changed_measures(before, after):
    def per_bar(score):
        bars = {}
        for event in event_signature(score):
            bars.setdefault(event[1], []).append(event[2:])
        return {k: sorted(v, key=repr) for k, v in bars.items()}
    a, b = per_bar(before), per_bar(after)
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def artifact(out, path, kind):
    path = Path(path)
    return dict(type=kind, path=path.relative_to(out).as_posix(), sha256=sha(path), bytes=path.stat().st_size)


def gate_check(name, gate, kind="automated"):
    evidence = {k: v for k, v in gate.items() if k in ("reason", "errors", "unsupported", "violations",
                                                         "shared_key_windows", "matched_events", "pages",
                                                         "renderer", "style_sha256", "applied_style_sha256",
                                                         "render_path", "native_format_version", "log_paths",
                                                         "source_musicxml_sha256", "returncode", "stderr_tail", "profile", "audio")}
    return dict(name=name, kind=kind, status=gate["status"], evidence=evidence or None)


def overall_status(checks):
    automated = [c for c in checks if c["kind"] == "automated"]
    review = [c for c in checks if c["kind"] == "review"]
    if any(c["status"] == "FAIL" for c in checks):
        return "FAIL"
    if any(c["status"] != "PASS" for c in automated):
        return "INCOMPLETE"
    if review and all(c["status"] == "PASS" for c in review):
        return "ACCEPTED"
    return "REVIEW_REQUIRED"


EXIT = {"ERROR": 1, "FAIL": 2, "INCOMPLETE": 3, "REVIEW_REQUIRED": 0, "ACCEPTED": 0}


def remaining_difficulties(qa, plan):
    found = []
    diff = qa["gates"]["difficulty"]
    for v in diff.get("violations", []):
        found.append(dict(kind="hard-limit", hand=v["hand"], at_quarters=v["at"], span=v["span"],
                          count=v["count"], ids=v["ids"]))
    for hand, info in diff.get("hands", {}).items():
        for j in info.get("jump_advisories", []):
            found.append(dict(kind="movement-advisory", hand=hand, at_quarters=j["at"],
                              centroid_semitones=round(j["semitones"], 2), seconds=round(j["seconds"], 3)))
        if info.get("density_advisory"):
            found.append(dict(kind="density-advisory", hand=hand,
                              attack_groups_per_second=info["max_attack_groups_per_second"]))
    for w in qa["gates"]["hand_coordination"].get("shared_key_windows", []):
        found.append(dict(kind="shared-key", measure=w["measure"], pitches=w["pitches"], ids=w["ids"]))
    for r in qa["gates"]["hand_coordination"].get("register_overlap_advisories", []):
        found.append(dict(kind="register-overlap-advisory", measure=r["measure"], at_quarters=r["at"]))
    for u in qa["gates"]["timeline"].get("unsupported", []):
        found.append(dict(kind="unsupported-notation-not-executed", feature=u))
    for note in (plan or {}).get("remaining_difficulties", []):
        found.append(dict(kind="agent-note", note=note))
    return found


def render(out, xml, style, mscore, audio):
    gate = dict(status="NOT_RUN", reason="MuseScore not found on this host")
    if not mscore:
        return gate, []
    made = []
    style_hash = None
    if style:
        style_copy = out / 'engraving-style.mss'
        shutil.copy2(style, style_copy)
        style = style_copy
        style_hash = sha(style_copy)
        made.append(artifact(out, style_copy, 'engraving-style'))
    pdf = out / (xml.stem + ".pdf")
    version = subprocess.run([mscore, "--version"], capture_output=True, text=True, timeout=120)
    renderer = (version.stdout or version.stderr).strip()
    source_hash = sha(xml)
    gate = dict(renderer=renderer, style_sha256=style_hash, source_musicxml_sha256=source_hash,
                render_path="direct-musicxml", log_paths=[])

    def execute(cmd):
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        log = out / f"render-step-{len(gate['log_paths']) + 1}.json"
        dump(dict(command=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr), log)
        made.append(artifact(out, log, "render-log"))
        gate['log_paths'].append(log.name)
        gate.update(command=[Path(c).name for c in cmd], returncode=proc.returncode,
                    stderr_tail=proc.stderr.strip().splitlines()[-5:])
        return proc

    render_input = xml
    # MS3 loads -S after importing/layout. Save the applied style into a native
    # score, then reload it before PDF export. Native files are engraving-only;
    # canonical MusicXML and internal MIDI remain the notation/timing authority.
    if style and re.search(r"\bMuseScore(?:3)?\s+(?:version\s+)?3\.", renderer, re.I):
        gate['render_path'] = "ms3-native-style-reload"
        native = out / "engraving-import.mscx"
        proc = execute([mscore, "-o", str(native), str(xml)])
        if native.exists():
            made.append(artifact(out, native, "engraving-import"))
        if proc.returncode != 0 or not native.exists():
            return dict(gate, status="FAIL", reason="Renderer did not produce the native engraving import"), made
        parser = E.XMLParser(resolve_entities=False, no_network=True)
        native_root = E.parse(str(native), parser).getroot()
        native_version = native_root.get('version')
        if native_root.tag != 'museScore' or not native_version or not re.fullmatch(r"3\.\d+", native_version):
            return dict(gate, status="FAIL", reason="Unrecognized MS3 native engraving format"), made
        adapted = E.parse(str(style), parser)
        if adapted.getroot().tag != 'museScore' or adapted.getroot().find('Style') is None:
            return dict(gate, status="FAIL", reason="Invalid engraving style document"), made
        adapted.getroot().set('version', native_version)
        applied_style = out / "engraving-style-applied.mss"
        adapted.write(str(applied_style), encoding="UTF-8", xml_declaration=True)
        made.append(artifact(out, applied_style, "engraving-style-applied"))
        gate.update(native_format_version=native_version, applied_style_sha256=sha(applied_style))
        styled = out / "engraving-styled.mscx"
        proc = execute([mscore, "-S", str(applied_style), "-o", str(styled), str(native)])
        if styled.exists():
            made.append(artifact(out, styled, "engraving-intermediate"))
        if proc.returncode != 0 or not styled.exists():
            return dict(gate, status="FAIL", reason="Renderer did not retain the styled engraving score"), made
        render_input = styled
    cmd = [mscore] + (["-S", str(style)] if style and render_input == xml else []) + ["-o", str(pdf), str(render_input)]
    proc = execute(cmd)
    if sha(xml) != source_hash:
        return dict(gate, status="FAIL", reason="Renderer changed canonical MusicXML"), made
    if proc.returncode != 0 or not pdf.exists():
        return dict(gate, status="FAIL", reason="Renderer did not produce a PDF"), made
    made.append(artifact(out, pdf, "pdf"))
    pages_dir = out / "pages"
    pages_dir.mkdir()
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-r", "110", "-png", str(pdf), str(pages_dir / "page")], check=True, timeout=300)
    images = sorted(pages_dir.glob("page-*.png"))
    made += [artifact(out, p, "page-image") for p in images]
    if not images:
        return dict(gate, status="NOT_RUN", reason="pdftoppm unavailable; pages not rasterized for inspection"), made
    gate.update(status="PASS", pages=len(images),
                interpretation="PDF exported and every page rasterized; page_inspection is a separate review")
    if audio:
        mp3 = out / (xml.stem + ".mp3")
        proc = subprocess.run([mscore, "-o", str(mp3), str(xml)], capture_output=True, text=True, timeout=600)
        gate['audio'] = dict(status="PASS" if proc.returncode == 0 and mp3.exists() else "FAIL",
            source="canonical-musicxml", source_sha256=sha(xml), returncode=proc.returncode,
            timing_model="MuseScore score playback; expressive notation may differ from the internal literal MIDI",
            interpretation="Export evidence only; decoded audio and human listening are separate checks")
        if proc.returncode == 0 and mp3.exists():
            made.append(dict(artifact(out, mp3, "audio-mechanical"), source_musicxml_sha256=sha(xml),
                             timing_model=gate['audio']['timing_model']))
    return gate, made


def run(a):
    out = a.out.resolve()
    if out.exists():
        raise SystemExit("Output directory exists; every run needs a new version directory")
    out.mkdir(parents=True)
    manifest = dict(manifest_version="score-manifest-0.1", tool_version=VERSION, created=now(),
                    title=a.title or "UNKNOWN", version=1, level=a.level,
                    length_mode=a.length_mode or "UNKNOWN", measure_scope=a.measure_scope or "UNKNOWN",
                    source_sha256="UNKNOWN", purpose=a.purpose, request=a.request or "UNKNOWN",
                    repair_round=0, previous=None, params=dict(hands=a.hands, level=a.level,
                    schema_dir=str(a.schema_dir) if a.schema_dir else None, plan=str(a.plan) if a.plan else None,
                    render=a.render, audio=a.audio),
                    changes=[], remaining_difficulties=[], artifacts=[], checks=[], steps=[], overall="ERROR")

    def step(name, status, **info):
        manifest["steps"].append(dict(name=name, status=status, at=now(), **info))

    def finish(status=None):
        if status:
            manifest["overall"] = status
        manifest["exit_code"] = EXIT[manifest["overall"]]
        dump(manifest, out / MANIFEST)
        write_report(out, manifest)
        print(json.dumps(dict(overall=manifest["overall"], version=manifest["version"], out=str(out),
                              checks={c["name"]: c["status"] for c in manifest["checks"]}), ensure_ascii=False))
        return manifest["exit_code"]

    try:
        if a.name and (a.name in ('.', '..') or '/' in a.name or '\\' in a.name
                       or any(ord(c) < 32 for c in a.name)):
            raise ValueError("Artifact name must be a file stem inside this version directory")
        input_hash = sha(a.input)
        manifest["input"] = dict(path=str(a.input.resolve()), sha256=input_hash)
        if a.source:
            manifest["source"] = dict(path=str(a.source.resolve()), sha256=sha(a.source), role=a.source_role)
            manifest["source_sha256"] = manifest["source"]["sha256"]
        if a.previous:
            prev = json.loads((a.previous / MANIFEST).read_text())
            candidate = next((x for x in prev["artifacts"] if x["type"] == "musicxml"), None)
            if candidate is None or candidate["sha256"] != input_hash:
                raise ValueError("Input is not the MusicXML output of --previous; refusing to break the version chain")
            manifest.update(version=prev["version"] + 1, level=a.level or prev["level"],
                            source_sha256=prev["source_sha256"] if not a.source else manifest["source_sha256"],
                            previous=dict(dir=str(a.previous.resolve()), overall=prev["overall"],
                                          manifest_sha256=sha(a.previous / MANIFEST)))
            for key in ("title", "length_mode", "measure_scope"):
                if manifest[key] == "UNKNOWN":
                    manifest[key] = prev.get(key, "UNKNOWN")
            if a.purpose == "repair":
                if prev["overall"] not in ("FAIL", "INCOMPLETE"):
                    raise ValueError("Repair requested but the previous version did not fail")
                manifest["repair_round"] = prev.get("repair_round", 0) + 1
                if manifest["repair_round"] > 2:
                    raise ValueError("Two targeted repairs already ran; keep the best version and report the issue")
        elif a.purpose != "initial":
            raise ValueError(f"--purpose {a.purpose} requires --previous")
        elif not a.source:
            manifest["source_sha256"] = input_hash
        if a.purpose == "revision" and not (a.request and a.edit_scope):
            raise ValueError("A requested revision needs --request (literal user words) and --edit-scope")
        hands = dict(item.split(":") for item in a.hands.split(","))

        tree = read_xml(a.input)
        original = parse_score(tree)
        source_qa = analyze(tree, a.schema_dir, hands, a.level)
        dump(source_qa, out / "input.qa.json")
        step("inspect-input", source_qa["overall"], measures=source_qa["measures"])
        if not a.previous:
            copy = out / "input" / a.input.name
            copy.parent.mkdir()
            shutil.copy2(a.input, copy)
            manifest["artifacts"].append(artifact(out, copy, "input-copy"))
        if manifest["measure_scope"] == "UNKNOWN":
            manifest["measure_scope"] = f"{original.bars[0]['measure']}-{original.bars[-1]['measure']}" if original.bars else "UNKNOWN"

        reordered = normalize_order(tree)
        if event_signature(parse_score(tree)) != event_signature(original):
            raise ValueError("Structural repair altered music events")
        if reordered:
            manifest["changes"].append(dict(op="structural-reorder", count=reordered,
                                            reason="MusicXML element order normalized; music events unchanged"))
        step("structural-repair", "PASS", reordered_elements=reordered)

        plan = None
        mapping_score=parse_score(tree)
        ids_before = {n.element: n.id for n in mapping_score.notes}
        ids_before.update({el:nid for nid,el in mapping_score.graces.items()})
        if a.plan:
            plan = json.loads(a.plan.read_text())
            if plan.get("input_sha256") != input_hash:
                raise ValueError("Plan input_sha256 does not match this input; regenerate the plan for this version")
            changes = apply_plan(tree, input_hash, plan)
            if plan.get("final_barline"):
                last = tree.getroot().find("part").findall("measure")[-1]
                if last.find("barline[@location='right']") is None:
                    bar = E.SubElement(last, "barline", location="right")
                    E.SubElement(bar, "bar-style").text = "light-heavy"
                    changes.append(dict(id=f"{tree.getroot().find('part').get('id')}:m{len(tree.getroot().find('part').findall('measure'))}",
                                        op="final_barline", reason=plan["final_barline"]))
            after = parse_score(tree)
            for c in changes:
                c["measure"] = int(c["id"].split(":m")[1].split(":")[0])
            # Symbol/direction omissions change notation even if timed pitches do not change.
            touched = sorted(set(changed_measures(original, after)) | {c["measure"] for c in changes})
            allowed = parse_scope(a.edit_scope, len(original.bars))
            if allowed is not None and not set(touched) <= allowed:
                raise ValueError(f"Edits changed measures {touched} outside the declared scope {a.edit_scope}")
            # A changed bass or top line is a musical decision the plan must state, not a side effect.
            outer = outer_voice_changes(original, after)
            stated = {(c["measure"], v) for c in changes
                      for v in ([c["outer_voice"]] if isinstance(c.get("outer_voice"), str) else c.get("outer_voice") or [])}
            missing = [o for o in outer if (o["measure"], o["voice"]) not in stated]
            if missing:
                o = missing[0]
                raise ValueError(f"Edits change the {o['voice']} at m{o['measure']} beat {o['beat']:g} "
                                 f"(MIDI {o['before']} -> {o['after']}) and {len(missing) - 1} more place(s); revoice, "
                                 "or mark an edit in that measure with \"outer_voice\": [\"bass\"|\"top\"] and say why")
            manifest["outer_voice_changes"] = outer
            manifest["changes"] += changes
            manifest["edited_measures"] = touched
            if plan.get("source_map"):
                manifest["source_mapping"] = plan["source_map"]
            step("apply-plan", "PASS", edits=len(changes), measures=touched)
        else:
            step("apply-plan", "NOT_RUN", reason="No plan supplied; output is the inspected input")
        if a.title:
            work = tree.getroot().find("work")
            if work is None:
                work = E.Element("work")
                tree.getroot().insert(0, work)
                E.SubElement(work, "work-title")
            if work.find("work-title") is None:
                E.SubElement(work, "work-title")
            work.find("work-title").text = a.title
        if manifest["title"] == "UNKNOWN":
            manifest["title"] = tree.findtext("work/work-title") or tree.findtext("movement-title") or a.input.stem

        stem = a.name or f"score-v{manifest['version']}"
        xml = out / f"{stem}.musicxml"
        write_xml(tree, xml)
        manifest["artifacts"].append(artifact(out, xml, "musicxml"))
        ids_after = {n.element: n.id for n in parse_score(tree).notes}
        event_map = {old: ids_after.get(el) for el, old in ids_before.items()}
        expansions = {}
        for c in manifest["changes"]:
            if c.get("kept_event"):  # Anchor removal: the kept pitch lives in the anchor element.
                event_map[c["kept_event"]], event_map[c["id"]] = event_map[c["id"]], None
            if c.get('realized_count'):
                first = next(el for el,old in ids_before.items() if old==c['id'])
                created = [first]+list(first.itersiblings('note'))[:c['realized_count']-1]
                c['output_event_ids'] = [ids_after[el] for el in created]
                expansions[c['id']] = c['output_event_ids']
                if c.get('output_source_ids'):
                    for original in set(c['output_source_ids']):
                        mapped=[new for old,new in zip(c['output_source_ids'],c['output_event_ids']) if old==original]
                        expansions[original]=mapped
                        event_map[original]=mapped[0]
        dump(dict(input_sha256=input_hash, output_sha256=sha(xml), map=event_map, expansions=expansions), out / "event-map.json")
        manifest["artifacts"].append(artifact(out, out / "event-map.json", "event-map"))

        qa = analyze(tree, a.schema_dir, hands, a.level)
        qa.update(input_sha256=input_hash, output_sha256=sha(xml),
                  original_difficulty=source_qa["gates"]["difficulty"])
        for name in AUTOMATED_GATES:
            manifest["checks"].append(gate_check(name, qa["gates"][name]))
        step("qa", "FAIL" if any(qa["gates"][g]["status"] == "FAIL" for g in AUTOMATED_GATES) else "DONE")

        if qa["gates"]["timeline"]["status"] == "PASS":
            midi_gate = export_midi(tree, out / f"{stem}.mid")
            manifest["artifacts"].append(artifact(out, out / f"{stem}.mid", "midi"))
        else:
            midi_gate = dict(status="NOT_RUN", reason="MIDI export needs a supported, valid timeline")
            mscore = find_mscore(a.mscore) if a.render != "skip" else None
            fallback = out / f"{stem}.musescore-unverified.mid"
            if mscore and subprocess.run([mscore, "-o", str(fallback), str(xml)], capture_output=True,
                                         timeout=600).returncode == 0 and fallback.exists():
                # Listening aid only: MuseScore's own playback realization, not read back or checked.
                manifest["artifacts"].append(artifact(out, fallback, "midi-musescore-unverified"))
                midi_gate["fallback"] = "MuseScore MIDI exported for listening; readback NOT_RUN"
        qa["gates"]["midi_readback"] = midi_gate
        manifest["checks"].append(gate_check("midi_readback", midi_gate))
        step("midi", midi_gate["status"])

        if a.render == "skip":
            render_gate, made = dict(status="NOT_RUN", reason="Rendering skipped by request"), []
        else:
            style = a.style or SKILL_ROOT / "assets" / "readable-a4.mss"
            render_gate, made = render(out, xml, style if Path(style).exists() else None, find_mscore(a.mscore), a.audio)
        qa["gates"]["render"] = render_gate
        manifest["artifacts"] += made
        manifest["checks"].append(gate_check("render", render_gate))
        step("render", render_gate["status"])

        for name, what in REVIEW_CHECKS.items():
            manifest["checks"].append(dict(name=name, kind="review", status="NOT_RUN", evidence=None, requires=what))
        dump(qa, out / f"{stem}.qa.json")
        manifest["artifacts"].append(artifact(out, out / f"{stem}.qa.json", "qa"))
        manifest["remaining_difficulties"] = remaining_difficulties(qa, plan)
        if plan and plan.get("musical_losses"):
            manifest["musical_losses"] = plan["musical_losses"]
        if sha(a.input) != input_hash:
            raise ValueError("Input changed during processing")
        manifest["input"]["preserved"] = True
        return finish(overall_status(manifest["checks"]))
    except (ValueError, KeyError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        step("error", "ERROR", message=manifest["error"])
        if "input" in manifest:
            manifest["input"]["preserved"] = sha(a.input) == manifest["input"]["sha256"]
        return finish("ERROR")


def annotate(a):
    path = a.manifest
    manifest = json.loads(path.read_text())
    if a.check == "musical_review" and a.status == "PASS" and a.by != "human":
        raise SystemExit("An arranger cannot pass its own musical review; record notes with NOT_RUN or FAIL")
    if a.check in HUMAN_ONLY and a.by != "human":
        raise SystemExit(f"{a.check} records a person's experience; it cannot be marked by an agent")
    check = next((c for c in manifest["checks"] if c["name"] == a.check), None)
    if check is None or check["kind"] != "review":
        raise SystemExit(f"Unknown review check: {a.check}")
    manifest.setdefault("history", []).append(dict(at=now(), check=a.check, before=check["status"],
                                                   after=a.status, by=a.by))
    check.update(status=a.status, evidence=a.evidence, by=a.by, recorded=now())
    if manifest["overall"] != "ERROR":
        manifest["overall"] = overall_status(manifest["checks"])
        manifest["exit_code"] = EXIT[manifest["overall"]]
    dump(manifest, path)
    write_report(path.parent, manifest)
    print(json.dumps(dict(overall=manifest["overall"], check=a.check, status=a.status)))
    return 0


def write_report(out, m):
    """Short bilingual delivery note derived only from the manifest."""
    status_zh = dict(ERROR="执行错误", FAIL="检查未通过", INCOMPLETE="必查项未执行", REVIEW_REQUIRED="技术检查通过，仍需复核",
                     ACCEPTED="全部复核通过")
    lines = [f"# {m['title']} — v{m['version']} ({m['level']})", "",
             f"- 状态 / Status: **{m['overall']}** — {status_zh[m['overall']]}",
             f"- 范围 / Scope: {m['measure_scope']} · {m['length_mode']}",
             f"- 来源哈希 / Source SHA-256: `{m['source_sha256']}`"]
    if m.get("previous"):
        lines.append(f"- 上一版 / Previous: `{m['previous']['dir']}` ({m['previous']['overall']})")
    if m.get("error"):
        lines.append(f"- 错误 / Error: `{m['error']}`")
    lines += ["", "## 检查 / Checks", "", "| check | kind | status |", "|---|---|---|"]
    lines += [f"| {c['name']} | {c['kind']} | {c['status']} |" for c in m["checks"]]
    lines += ["", f"## 修改 / Changes ({len(m['changes'])})", ""]
    lines += [f"- m{c.get('measure', '?')} `{c.get('id', '')}` {c['op']}: {c['reason']}" for c in m["changes"]] or ["- none"]
    lines += ["", f"## 剩余难点 / Remaining difficulties ({len(m['remaining_difficulties'])})", ""]
    lines += [f"- {json.dumps(d, ensure_ascii=False)}" for d in m["remaining_difficulties"][:40]] or ["- none recorded"]
    lines += ["", "## 文件 / Artifacts", ""]
    lines += [f"- {x['type']}: `{x['path']}`" for x in m["artifacts"]]
    lines += ["", "退出码 0 只表示自动检查通过；来源、音乐、试听和试弹需另行记录。",
              "Exit 0 means only the automated gates passed; source, musical, listening and playing reviews are separate."]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--input", required=True, type=Path)
    r.add_argument("--out", required=True, type=Path, help="New version directory")
    r.add_argument("--hands", required=True, help="Explicit staff map such as 1:R,2:L; never inferred")
    r.add_argument("--level", choices=["L1", "L2", "L3"], default="L2")
    r.add_argument("--plan", type=Path, help="Hash-bound edit plan JSON")
    r.add_argument("--previous", type=Path, help="Previous version directory (its MusicXML must be --input)")
    r.add_argument("--purpose", choices=["initial", "repair", "revision"], default="initial")
    r.add_argument("--request", help="The user's literal request for this version")
    r.add_argument("--edit-scope", help="Measures the plan may change, e.g. 6 or 5-7 (1-based positions)")
    r.add_argument("--source", type=Path, help="Original source file (e.g. the scan PDF) for the lineage hash")
    r.add_argument("--source-role", default="cited source")
    r.add_argument("--title")
    r.add_argument("--name", help="Artifact file stem")
    r.add_argument("--length-mode", choices=["Mini", "Full"])
    r.add_argument("--measure-scope", help="Source measures covered, e.g. 1-9")
    r.add_argument("--schema-dir", type=Path)
    r.add_argument("--render", choices=["auto", "skip"], default="auto")
    r.add_argument("--style", type=Path)
    r.add_argument("--mscore")
    r.add_argument("--audio", action="store_true", help="Also export a mechanical MP3 through MuseScore")
    n = sub.add_parser("annotate", help="Record a review result; artifacts are not changed")
    n.add_argument("--manifest", required=True, type=Path)
    n.add_argument("--check", required=True, choices=sorted(REVIEW_CHECKS))
    n.add_argument("--status", required=True, choices=["PASS", "FAIL", "NOT_RUN"])
    n.add_argument("--evidence", required=True)
    n.add_argument("--by", required=True, choices=["agent", "human"])
    a = p.parse_args()
    return run(a) if a.cmd == "run" else annotate(a)


if __name__ == "__main__":
    sys.exit(main())
