"""Parse TXT / VTT / JSON transcripts into normalized ParsedSegment objects.

Pure functions, no DB access, so they are trivial to unit test.
"""
import json
import re
from dataclasses import dataclass

from app.core.exceptions import ValidationFailed

MAX_SEGMENTS = 5000
TS = r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?"
RE_TS_SPK_TEXT = re.compile(rf"^\[?\(?({TS})\)?\]?\s*[-–]?\s*([^\W\d][\w .'’-]{{0,48}}?):\s*(.*)$")
RE_TS_ONLY = re.compile(rf"^\[?\(?({TS})\)?\]?$")
RE_SPK_TEXT = re.compile(r"^([A-Z][\w .'’-]{0,40}?):\s*(.*)$")
RE_VTT_TIME = re.compile(rf"^({TS})\s*-->\s*({TS})")
RE_VTT_VOICE = re.compile(r"^<v\s+([^>]+)>(.*)$")


@dataclass
class ParsedSegment:
    speaker: str
    start_time: float
    end_time: float | None
    text: str


def parse_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    secs = 0.0
    for p in parts:
        secs = secs * 60 + float(p)
    return secs


def _estimate_duration(text: str) -> float:
    return max(2.0, round(len(text.split()) / 2.5, 1))  # ~150 wpm


def _finalize(segs: list[ParsedSegment], explicit_times: bool) -> list[ParsedSegment]:
    if not segs:
        raise ValidationFailed("No transcript segments could be found in the provided content.")
    if len(segs) > MAX_SEGMENTS:
        raise ValidationFailed(f"Transcript is too long (max {MAX_SEGMENTS} segments).")
    cursor = 0.0
    for i, s in enumerate(segs):
        if s.start_time is None:
            s.start_time = cursor
        nxt = segs[i + 1].start_time if i + 1 < len(segs) else None
        est = s.start_time + _estimate_duration(s.text)
        if s.end_time is None:
            s.end_time = min(est, nxt) if (explicit_times and nxt and nxt > s.start_time) else est
        if s.end_time < s.start_time:
            s.end_time = s.start_time
        cursor = s.end_time
    return segs


def detect_format(content: str, filename: str | None = None) -> str:
    name = (filename or "").lower()
    stripped = content.lstrip("\ufeff \n\t")
    if name.endswith(".vtt") or stripped.startswith("WEBVTT"):
        return "vtt"
    if name.endswith(".json"):
        return "json"
    if stripped[:1] in ("[", "{"):
        try:
            json.loads(stripped)
            return "json"
        except json.JSONDecodeError:
            pass  # e.g. "[00:02] Speaker: ..." is plain text
    return "txt"


def parse_txt(content: str) -> list[ParsedSegment]:
    segs: list[ParsedSegment] = []
    cur: ParsedSegment | None = None
    pending_ts: float | None = None
    explicit = False

    def flush():
        nonlocal cur
        if cur and cur.text.strip():
            cur.text = cur.text.strip()
            segs.append(cur)
        cur = None

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if m := RE_TS_SPK_TEXT.match(line):
            flush()
            explicit = True
            cur = ParsedSegment(m.group(2).strip(), parse_timestamp(m.group(1)), None, m.group(3))
            pending_ts = None
        elif m := RE_TS_ONLY.match(line):
            flush()
            explicit = True
            pending_ts = parse_timestamp(m.group(1))
        elif m := RE_SPK_TEXT.match(line):
            flush()
            cur = ParsedSegment(m.group(1).strip(), pending_ts, None, m.group(2))  # type: ignore[arg-type]
            pending_ts = None
        elif cur:
            cur.text += " " + line
        else:
            raise ValidationFailed(
                "Could not parse transcript. Use lines like '[00:12] Speaker: text' or 'Speaker: text'.",
                {"line": line[:80]},
            )
    flush()
    return _finalize(segs, explicit)


def parse_vtt(content: str) -> list[ParsedSegment]:
    segs: list[ParsedSegment] = []
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").lstrip("\ufeff"))
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        idx = next((i for i, ln in enumerate(lines) if RE_VTT_TIME.match(ln.strip())), None)
        if idx is None:
            continue
        m = RE_VTT_TIME.match(lines[idx].strip())
        text = " ".join(lines[idx + 1 :]).strip()
        speaker = "Speaker"
        if v := RE_VTT_VOICE.match(text):
            speaker, text = v.group(1).strip(), v.group(2)
        elif s := RE_SPK_TEXT.match(text):
            speaker, text = s.group(1).strip(), s.group(2)
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            segs.append(ParsedSegment(speaker, parse_timestamp(m.group(1)), parse_timestamp(m.group(2)), text))
    return _finalize(segs, True)


def parse_json(content: str) -> tuple[list[ParsedSegment], dict]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValidationFailed(f"Invalid JSON: {e.msg} (line {e.lineno}).") from e
    meta: dict = {}
    if isinstance(data, dict):
        meta = {k: data[k] for k in ("title", "description", "date", "duration_seconds", "tags") if k in data}
        data = data.get("segments") or data.get("transcript") or data.get("sentences")
    if not isinstance(data, list):
        raise ValidationFailed("JSON must be a list of segments or an object with a 'segments' array.")
    segs = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValidationFailed(f"Segment {i + 1} must be an object.")
        text = str(item.get("text") or item.get("content") or "").strip()
        speaker = str(item.get("speaker") or item.get("speaker_name") or item.get("name") or "Speaker").strip()
        start = item.get("start_time", item.get("start"))
        end = item.get("end_time", item.get("end"))
        try:
            start = parse_timestamp(start) if isinstance(start, str) else (float(start) if start is not None else None)
            end = parse_timestamp(end) if isinstance(end, str) else (float(end) if end is not None else None)
        except (TypeError, ValueError) as e:
            raise ValidationFailed(f"Segment {i + 1} has an invalid timestamp.") from e
        if not text:
            raise ValidationFailed(f"Segment {i + 1} is missing 'text'.")
        segs.append(ParsedSegment(speaker, start, end, text))  # type: ignore[arg-type]
    return _finalize(segs, any(s.start_time is not None for s in segs)), meta


def parse_transcript(content: str, fmt: str = "auto", filename: str | None = None) -> tuple[list[ParsedSegment], dict]:
    if not content or not content.strip():
        raise ValidationFailed("Transcript is empty.")
    fmt = detect_format(content, filename) if fmt == "auto" else fmt
    if fmt == "vtt":
        return parse_vtt(content), {}
    if fmt == "json":
        return parse_json(content)
    return parse_txt(content), {}
