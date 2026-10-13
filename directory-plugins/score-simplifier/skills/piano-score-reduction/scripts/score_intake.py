"""Read-only PDF intake, declared delivery contracts and bounded work checkpoints.

These checks do not transcribe a score or establish source/musical acceptance.
"""
from pathlib import Path
import hashlib
import math

DELIVERIES = {
    "annotated_pdf": dict(notes_removed=False, editable_full_score=False,
        description="Original notes remain; markings explain proposed omissions.",
        expected=["marked PDF", "change notes"], midi_scope="optional diagnostic excerpts"),
    "reduced_pdf": dict(notes_removed=True, editable_full_score=False,
        description="Selected printed notes are erased; complete systems are repaginated.",
        expected=["reduced PDF", "source/edit map", "QA"], midi_scope="optional diagnostic excerpts"),
    "editable_score": dict(notes_removed=True, editable_full_score=True,
        description="Verified notation is re-engraved from a canonical editable score.",
        expected=["PDF", "complete MusicXML", "verified MIDI", "source/edit map", "QA"],
        midi_scope="declared complete score or coherent phrase"),
}
SCORE_KINDS = ("unknown", "solo_piano", "voice_piano", "ensemble")


def delivery_contract(form):
    if form not in DELIVERIES:
        raise ValueError("Unknown delivery form")
    return dict(form=form, **DELIVERIES[form])


def _image_resources(resources, seen=None):
    """Inspect resource metadata without decoding large score images."""
    seen = set() if seen is None else seen
    if resources is None:
        return []
    resources = resources.get_object()
    result = []
    for reference in resources.get("/XObject", {}).get_object().values() if "/XObject" in resources else []:
        obj = reference.get_object()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        if obj.get("/Subtype") == "/Image":
            result.append(dict(width=int(obj.get("/Width", 0)), height=int(obj.get("/Height", 0))))
        elif obj.get("/Subtype") == "/Form":
            result.extend(_image_resources(obj.get("/Resources"), seen))
    return result


def inspect_pdf(path, score_kind="unknown", form="editable_score"):
    from pypdf import PdfReader
    if score_kind not in SCORE_KINDS:
        raise ValueError("Unknown score kind")
    path = Path(path)
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF needs an accessible copy before intake")
    count = len(reader.pages)
    if not count:
        raise ValueError("PDF has no pages")
    sample = sorted({0, count // 2, count - 1})
    pages = []
    for index in sample:
        page = reader.pages[index]
        images = _image_resources(page.get("/Resources"))
        pages.append(dict(page=index + 1, width_points=float(page.mediabox.width),
            height_points=float(page.mediabox.height), image_resources=images,
            extracted_text_characters=len(page.extract_text() or "")))
    image_candidate = all(p["image_resources"] and p["extracted_text_characters"] < 80 for p in pages)
    return dict(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), format="pdf",
        pages=count, sampled_pages=pages, image_only_candidate=image_candidate,
        image_classification_is_not_readability_evidence=True,
        score_kind=score_kind, score_kind_basis="caller declaration; inspect rendered source to confirm",
        protected_roles=["voice and lyrics"] if score_kind == "voice_piano" else [],
        delivery=delivery_contract(form), canonical_score_available=False, core_ready=False,
        route="TRANSCRIPTION_AND_SOURCE_REVIEW" if form == "editable_score" else "GRAPHICAL_SOURCE_REVIEW",
        source_readability="NOT_RUN", source_fidelity="NOT_RUN", musical_review="NOT_RUN",
        human_listening="NOT_RUN", human_playing="NOT_RUN",
        next_steps=["View representative rendered pages and confirm musical roles",
                    "Check one coherent phrase internally before expanding",
                    "Record source comparison and the chosen delivery form"],
        core_scope="One piano MusicXML part; voice/ensemble material needs a separate mapped workflow")


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid nonnegative measurement: {name}")
    return value


def budget_checkpoint(state):
    """Checkpoint one method/stage, not an account quota or whole-task deadline."""
    if not isinstance(state, dict):
        raise ValueError("Budget state must be a JSON object")
    stage = state.get("stage")
    if not isinstance(stage, str) or not stage.strip():
        raise ValueError("Budget checkpoint needs a named stage/method")
    observed, limits = state.get("observed", {}), state.get("limits", {})
    if not isinstance(observed, dict) or not isinstance(limits, dict):
        raise ValueError("Observed measurements and limits must be JSON objects")
    elapsed = observed.get("elapsed_minutes")
    if elapsed is not None:
        elapsed = _number(elapsed, "elapsed_minutes")
    minute_limit = limits.get("elapsed_minutes", 20 if stage == "pdf_probe" else None)
    if minute_limit is not None:
        _number(minute_limit, "elapsed_minutes limit")
        if minute_limit == 0:
            raise ValueError("Budget limits must be positive")
    tokens = None
    names = ("input_tokens", "cached_input_tokens", "output_tokens")
    values = {k: observed.get(k) for k in names}
    for name, value in values.items():
        if value is not None:
            _number(value, name)
            if type(value) is not int:
                raise ValueError("Token counters must be integers")
    if values["input_tokens"] is not None and values["cached_input_tokens"] is not None:
        if values["cached_input_tokens"] > values["input_tokens"]:
            raise ValueError("Cached input exceeds total input")
    if all(value is not None for value in values.values()):
        tokens = values["input_tokens"] - values["cached_input_tokens"] + values["output_tokens"]
    token_limit = limits.get("uncached_input_plus_output_tokens")
    if token_limit is not None:
        _number(token_limit, "token limit")
        if token_limit == 0:
            raise ValueError("Budget limits must be positive")
    attempts = state.get("repair_attempts", 0)
    if type(attempts) is not int or attempts < 0:
        raise ValueError("Invalid repair attempt count")
    labor = observed.get("human_labor_minutes")
    if labor is not None:
        _number(labor, "human_labor_minutes")
    reasons = []
    if minute_limit is not None and elapsed is not None and elapsed >= minute_limit:
        reasons.append("stage time checkpoint reached")
    if token_limit is not None and tokens is not None and tokens >= token_limit:
        reasons.append("observed token checkpoint reached")
    if attempts >= 2 and state.get("gate_status") in ("FAIL", "INCOMPLETE"):
        reasons.append("two repairs of this method/gate exhausted")
    return dict(stage=stage, action="REPLAN_METHOD" if reasons else "CONTINUE",
        reasons=reasons, measured_elapsed_minutes=elapsed, measured_uncached_input_plus_output_tokens=tokens,
        observed_token_breakdown=values,
        limits=dict(elapsed_minutes=minute_limit, uncached_input_plus_output_tokens=token_limit),
        measurement_status="OBSERVED" if elapsed is not None and tokens is not None else "PARTIAL_OR_UNAVAILABLE",
        actual_cash_charge="UNKNOWN", account_quota_deduction="UNKNOWN",
        human_labor_minutes=labor,
        scope="Preserve the best candidate; change the method or localize this issue; continue independent work")


def _same_head(a, b):
    if a["page"] != b["page"]:
        return False
    ax, ay, aw, ah = a["bounds"]
    bx, by, bw, bh = b["bounds"]
    intersection = max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0, min(ay + ah, by + bh) - max(ay, by))
    return intersection / (aw * ah + bw * bh - intersection) >= 0.8


def check_pdf_edit_records(record, source_sha256):
    """Reject dangerous normalized edit records; never certify OMR/source accuracy."""
    errors = []
    if record.get("source_sha256") != source_sha256:
        errors.append("source hash mismatch")
    glyphs = record.get("heads", [])
    heads = {g["id"]: g for g in glyphs}
    if len(heads) != len(glyphs):
        errors.append("duplicate source head IDs")
    for g in glyphs:
        if type(g["page"]) is not int or g["page"] < 1 or len(g["bounds"]) != 4:
            raise ValueError("Invalid head page/bounds")
        for value in g["bounds"]:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Invalid head geometry")
        if min(g["bounds"][2:]) <= 0:
            raise ValueError("Head dimensions must be positive")
    edits = record.get("edits", [])
    removed = {e["id"] for e in edits}
    if len(removed) != len(edits):
        errors.append("duplicate edit IDs")
    if not removed.issubset(heads):
        errors.append("unknown edited head")
    for identifier in removed & heads.keys():
        for other in glyphs:
            if other["id"] != identifier and _same_head(heads[identifier], other):
                errors.append(f"shared physical head needs source review, not independent erasure/rest: {identifier}, {other['id']}")
    deleted_ties = set(record.get("removed_tie_ids", []))
    ties = record.get("ties", [])
    if not deleted_ties.issubset({t["id"] for t in ties}):
        errors.append("unknown removed tie")
    for tie in ties:
        ends = {tie["start"], tie["stop"]}
        if not ends.issubset(heads):
            errors.append(f"unknown tie endpoint: {tie['id']}")
            continue
        a, b = heads[tie["start"]], heads[tie["stop"]]
        if a.get("pitch") is None or a.get("pitch") != b.get("pitch"):
            errors.append(f"tie endpoints need source verification: {tie['id']}")
        if ends & removed and tie["id"] not in deleted_ties:
            errors.append(f"orphan tie after omission: {tie['id']}")
        if not ends & removed and tie["id"] in deleted_ties:
            errors.append(f"retained tie scheduled for deletion: {tie['id']}")
    transfers = {(x["from"], x["to"], x["sign"]) for x in record.get("accidental_transfers", [])}
    for dependency in record.get("accidental_dependencies", []):
        key = dependency["from"], dependency["to"], dependency["sign"]
        if key[0] not in heads or key[1] not in heads:
            errors.append("unknown accidental dependency")
        elif key[0] in removed and key[1] not in removed and key not in transfers:
            errors.append(f"accidental inheritance not preserved: {key[1]}")
    return dict(status="FAIL" if errors else "PASS" if glyphs else "NOT_RUN", errors=sorted(set(errors)),
        heads_checked=len(glyphs), edits_checked=len(edits), ties_checked=len(ties),
        scope="Supplied normalized head/tie/accidental records only; no pixel editing or OMR performed",
        source_fidelity="NOT_RUN", musical_acceptance="NOT_RUN")
