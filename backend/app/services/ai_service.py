"""AI abstraction.

`AIService` is the interface the rest of the app depends on. `HeuristicAIService` is a deterministic,
dependency-free implementation (MOCKED intelligence: extractive heuristics) so the app always works.
`GeminiAIService` optionally upgrades summaries and Q&A when GEMINI_API_KEY is set and silently falls
back to the heuristic implementation on any failure.
"""
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger("app.ai")

STOPWORDS = set(
    """a about above after again all also am an and any are as at be because been before being below between both
    but by can could did do does doing down during each few for from further had has have having he her here hers
    him his how i if in into is it its just let's like me more most my no nor not now of off on once only or other
    our out over own really same she should so some such than that the their them then there these they this those
    through to too under until up very was we were what when where which while who whom why will with would yeah
    okay ok yes know think going get got one two make sure need want right actually maybe thing things lot kind
    still it's i'll we'll that's don't i'm we're you're can't also look good great thanks thank""".split()
)
ACTION_PAT = re.compile(
    r"\b(i'll|i will|i can take|we need to|we should|let's make sure|can you|could you|please|action item|"
    r"follow up|will send|will share|will draft|will set up|i'm going to|owner|by (?:monday|tuesday|wednesday|"
    r"thursday|friday|next week|end of (?:the )?(?:week|day|month|sprint)|tomorrow))\b", re.I)
DECISION_PAT = re.compile(r"\b(decided|we agreed|agreed|let's go with|we'll go with|approved|final decision|settled on|we're going with|going with)\b", re.I)
TAKEAWAY_PAT = re.compile(r"\b(important|key|priority|biggest|main|risk|blocker|launch|deadline|budget|goal|metric|milestone)\b", re.I)
DUE_PAT = {
    "tomorrow": 1, "monday": 0, "tuesday": 0, "wednesday": 0, "thursday": 0, "friday": 0,
    "next week": 7, "end of the week": 0, "end of week": 0, "end of the sprint": 10, "end of the month": 20,
}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class Seg:
    """Provider-agnostic transcript segment used by the AI layer."""
    id: int
    speaker: str
    start: float
    end: float
    text: str


@dataclass
class SummaryResult:
    overview: str
    key_takeaways: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)
    provider: str = "heuristic"


@dataclass
class ActionItemDraft:
    title: str
    assignee: str | None
    due_date: date | None
    description: str | None = None


@dataclass
class TopicDraft:
    name: str
    start: float
    end: float
    summary: str = ""


@dataclass
class Answer:
    answer: str
    citations: list[Seg]
    provider: str


def fmt_ts(sec: float) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 3]


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _trim(s: str, n: int = 180) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


class AIService:
    """Interface."""

    name = "abstract"

    def generate_summary(self, transcript: list[Seg]) -> SummaryResult: raise NotImplementedError
    def extract_action_items(self, transcript: list[Seg], base_date: date | None = None) -> list[ActionItemDraft]: raise NotImplementedError
    def extract_topics(self, transcript: list[Seg]) -> list[TopicDraft]: raise NotImplementedError
    def extract_chapters(self, transcript: list[Seg]) -> list[TopicDraft]: raise NotImplementedError
    def answer_question(self, transcript: list[Seg], question: str) -> Answer: raise NotImplementedError


class HeuristicAIService(AIService):
    name = "heuristic"

    def generate_summary(self, transcript: list[Seg]) -> SummaryResult:
        if not transcript:
            return SummaryResult("No transcript available.")
        speakers = list(dict.fromkeys(s.speaker for s in transcript))
        topics = self.extract_topics(transcript)
        topic_names = ", ".join(t.name for t in topics[:4])
        opening = _trim(next((x for s in transcript[:6] for x in _sentences(s.text) if len(x) > 40), transcript[0].text), 200)
        overview = (
            f"{len(speakers)} participants ({', '.join(speakers[:4])}{'…' if len(speakers) > 4 else ''}) met for about "
            f"{max(1, round(transcript[-1].end / 60))} minutes. Main themes: {topic_names or 'general discussion'}. "
            f"The conversation opened with: \"{opening}\""
        )
        takeaways, decisions, follow_ups = [], [], []
        for s in transcript:
            for sent in _sentences(s.text):
                if DECISION_PAT.search(sent) and len(decisions) < 6:
                    decisions.append(_trim(sent))
                elif TAKEAWAY_PAT.search(sent) and len(sent) > 35 and len(takeaways) < 6:
                    takeaways.append(_trim(sent))
                if sent.endswith("?") and len(sent) > 30 and len(follow_ups) < 5:
                    follow_ups.append(_trim(sent))
        if not takeaways:
            takeaways = [_trim(s.text) for s in sorted(transcript, key=lambda x: -len(x.text))[:4]]
        return SummaryResult(overview, takeaways, decisions, follow_ups, self.name)

    def extract_action_items(self, transcript: list[Seg], base_date: date | None = None) -> list[ActionItemDraft]:
        base = base_date or date.today()
        items: list[ActionItemDraft] = []
        seen: set[str] = set()
        for s in transcript:
            for sent in _sentences(s.text):
                if not ACTION_PAT.search(sent) or len(sent) < 20 or sent.endswith("?"):
                    continue
                key = re.sub(r"\W+", " ", sent.lower())[:60]
                if key in seen:
                    continue
                seen.add(key)
                title = re.sub(r"^(okay|ok|sure|yes|yeah|so|and|great|alright)[, ]+", "", sent, flags=re.I)
                title = _trim(title[0].upper() + title[1:], 120)
                items.append(ActionItemDraft(title, s.speaker, self._due(sent, base), f"Mentioned by {s.speaker} at {fmt_ts(s.start)}."))
                if len(items) >= 8:
                    return items
        return items

    @staticmethod
    def _due(sentence: str, base: date) -> date | None:
        low = sentence.lower()
        for word, offset in DUE_PAT.items():
            if word in low:
                if word in WEEKDAYS:
                    delta = (WEEKDAYS.index(word) - base.weekday()) % 7 or 7
                    return base + timedelta(days=delta)
                if "week" in word and offset == 0:
                    return base + timedelta(days=(4 - base.weekday()) % 7)
                return base + timedelta(days=offset)
        return None

    def _windows(self, transcript: list[Seg]) -> list[list[Seg]]:
        if not transcript:
            return []
        n = 3 if len(transcript) < 14 else 4 if len(transcript) < 26 else 5
        n = max(1, min(n, len(transcript) // 4 or 1))
        size = -(-len(transcript) // n)
        return [transcript[i : i + size] for i in range(0, len(transcript), size)]

    def _label(self, window: list[Seg], used: set[str]) -> str:
        counts = Counter(_keywords(" ".join(s.text for s in window)))
        for word, _ in counts.most_common(8):
            if word not in used:
                used.add(word)
                second = next((w for w, _ in counts.most_common(8) if w not in used and w != word), None)
                if second:
                    used.add(second)
                    return f"{word.title()} & {second.title()}"
                return word.title()
        return "Discussion"

    def extract_topics(self, transcript: list[Seg]) -> list[TopicDraft]:
        used: set[str] = set()
        return [TopicDraft(self._label(w, used), w[0].start, w[-1].end) for w in self._windows(transcript)]

    def extract_chapters(self, transcript: list[Seg]) -> list[TopicDraft]:
        used: set[str] = set()
        out = []
        for w in self._windows(transcript):
            label = self._label(w, used)
            best = max((x for s in w for x in _sentences(s.text)), key=len, default="")
            out.append(TopicDraft(label, w[0].start, w[-1].end, _trim(best, 220)))
        return out

    def answer_question(self, transcript: list[Seg], question: str) -> Answer:
        q_words = {_stem(w) for w in _keywords(question)}
        if not q_words:
            return Answer("Could you rephrase the question with a few specific keywords?", [], self.name)
        scored = []
        for s in transcript:
            words = {_stem(w) for w in _keywords(s.text)}
            overlap = len(q_words & words)
            if overlap:
                scored.append((overlap + min(len(s.text), 200) / 1000, s))
        if not scored:
            return Answer("I couldn't find anything in this meeting that relates to that question.", [], self.name)
        top = [s for _, s in sorted(scored, key=lambda x: -x[0])[:3]]
        top.sort(key=lambda s: s.start)
        lines = [f"{s.speaker} ({fmt_ts(s.start)}): {_trim(s.text, 220)}" for s in top]
        return Answer("Here is what the meeting says about this:\n\n" + "\n".join(f"• {l}" for l in lines), top, self.name)


class GeminiAIService(HeuristicAIService):
    """Optional LLM upgrade; every call falls back to heuristics on error."""

    name = "gemini"

    def __init__(self, settings: Settings):
        self.key, self.model = settings.gemini_api_key, settings.gemini_model

    def _ask(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        r = httpx.post(url, params={"key": self.key}, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def _render(transcript: list[Seg], limit: int = 24000) -> str:
        return "\n".join(f"[{fmt_ts(s.start)}] {s.speaker}: {s.text}" for s in transcript)[:limit]

    def generate_summary(self, transcript: list[Seg]) -> SummaryResult:
        try:
            raw = self._ask(
                "Summarize this meeting transcript. Respond ONLY with JSON: "
                '{"overview": str, "key_takeaways": [str], "decisions": [str], "follow_ups": [str]}.\n\n' + self._render(transcript)
            )
            data = json.loads(re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip())
            return SummaryResult(str(data["overview"]), [str(x) for x in data.get("key_takeaways", [])][:8],
                                 [str(x) for x in data.get("decisions", [])][:8], [str(x) for x in data.get("follow_ups", [])][:8], self.name)
        except Exception:  # noqa: BLE001
            logger.warning("Gemini summary failed; using heuristic fallback")
            return super().generate_summary(transcript)

    def answer_question(self, transcript: list[Seg], question: str) -> Answer:
        base = super().answer_question(transcript, question)
        try:
            text = self._ask(
                "Answer the question using ONLY this meeting transcript. Be concise and mention timestamps.\n\n"
                f"{self._render(transcript)}\n\nQuestion: {question}"
            )
            return Answer(text.strip(), base.citations, self.name)
        except Exception:  # noqa: BLE001
            logger.warning("Gemini Q&A failed; using heuristic fallback")
            return base


def get_ai_service() -> AIService:
    settings = get_settings()
    return GeminiAIService(settings) if settings.gemini_api_key else HeuristicAIService()
