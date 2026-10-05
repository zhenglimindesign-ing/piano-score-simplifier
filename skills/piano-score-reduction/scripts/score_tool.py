#!/usr/bin/env python3
"""CLI used by the skill; review the JSON gates, not just successful execution."""
import argparse
import json
from pathlib import Path
import sys

from score_core import (AUTOMATED_GATES, analyze, apply_plan, dump, event_signature, export_midi,
                        normalize_order, parse_score, read_xml, sha, write_xml)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["inspect", "repair", "apply", "midi"])
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--schema-dir", type=Path)
    p.add_argument("--hands", help="Explicit one-part staff map, e.g. 1:R,2:L; never inferred")
    p.add_argument("--level", choices=["L1", "L2", "L3"], default="L2")
    p.add_argument("--plan", type=Path)
    args = p.parse_args()
    destinations = [x.resolve() for x in (args.output, args.report) if x]
    if len(destinations) != len(set(destinations)) or args.input.resolve() in destinations:
        p.error("Input, output and report paths must be distinct")
    if any(x.exists() for x in (args.output, args.report) if x):
        p.error("Output exists; use a new version")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    before = sha(args.input)
    tree = read_xml(args.input)
    extra = {}
    if args.command == "repair":
        original = event_signature(parse_score(tree))
        extra["reordered_elements"] = normalize_order(tree)
        if event_signature(parse_score(tree)) != original:
            raise ValueError("Structural repair altered music events")
        extra["music_events_unchanged"] = True
    elif args.command == "apply":
        if args.plan is None:
            p.error("apply requires --plan")
        extra["changes"] = apply_plan(tree, before, json.loads(args.plan.read_text()))
    if args.command != "inspect" and args.output is None:
        p.error("This command requires --output")
    if args.command in ("repair", "apply"):
        write_xml(tree, args.output)
    if args.command == "midi":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        extra["midi"] = export_midi(tree, args.output)
    hands = dict(item.split(":") for item in args.hands.split(",")) if args.hands else {}
    report = analyze(tree, args.schema_dir, hands, args.level)
    if sha(args.input) != before:
        raise ValueError("Input changed during processing")
    report.update(input_sha256=before, input_preserved=True, command=args.command, **extra)
    if args.output:
        report["output_sha256"] = sha(args.output)
    dump(report, args.report)
    print(json.dumps(dict(overall=report["overall"], report=str(args.report),
                          gates={k: v["status"] for k, v in report["gates"].items()})))
    if report["overall"] == "FAIL":
        return 2
    # A mandatory automated gate that did not run is not a success.
    return 3 if any(report["gates"][g]["status"] == "NOT_RUN" for g in AUTOMATED_GATES) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
