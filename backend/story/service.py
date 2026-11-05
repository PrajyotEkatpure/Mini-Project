"""Story generation + follow-up dialogue orchestration: retrieve -> generate -> validate -> (retry) -> respond."""
import logging
import time

from pydantic import ValidationError

from . import llm, prompts
from .retriever import ConstitutionRetriever, RetrievalError
from .schema import FollowUpAnswer, Story, Style
from .validator import text_problems, validate_answer, validate_story

log = logging.getLogger("samvidhan.story.service")

AUDIENCE_ALIASES = {"kid": "kid", "child": "kid", "student": "student", "teenager": "student", "teen": "student", "adult": "adult"}
STYLES = ("mystery", "adventure", "everyday", "courtroom")
MAX_ATTEMPTS = 3
CACHE_TTL_S = 3600
MIN_PRIMARY_CHARS = 20

UNSUPPORTED_ANSWER = (
    "I looked through the constitutional text available to me, and it doesn't establish an answer to that. "
    "I'd rather not guess - try asking about what the article itself says."
)


class ServiceError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


_EMOTIONS = {"neutral", "happy", "curious", "worried", "surprised", "thoughtful", "determined"}
_POSES = {"standing", "talking", "pointing", "thinking", "reading"}


def _normalise_raw(raw):
    """Repair cosmetic drift only (unknown emotion/pose) and drop claims/quiz items that cite nothing.
    Nothing here can make an unsupported statement look supported."""
    if not isinstance(raw, dict):
        return raw
    for sc in raw.get("scenes") or []:
        if not isinstance(sc, dict):
            continue
        for line in sc.get("dialogue") or []:
            if isinstance(line, dict):
                if line.get("emotion") not in _EMOTIONS:
                    line["emotion"] = "neutral"
                if line.get("pose") not in _POSES:
                    line["pose"] = "talking"
        if isinstance(sc.get("claims"), list):
            sc["claims"] = [c for c in sc["claims"] if isinstance(c, dict) and c.get("source_ids")]
    if isinstance(raw.get("quiz"), list):
        raw["quiz"] = [q for q in raw["quiz"] if isinstance(q, dict) and q.get("source_ids")]
    return raw


def _pydantic_feedback(e):
    return [f"schema: {'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()[:10]]


class StoryService:
    def __init__(self, retriever=None, generate=None, clock=time.time):
        self.retriever = retriever or ConstitutionRetriever()
        self.generate = generate or llm.generate_json
        self._cache = {}
        self._clock = clock

    # ---- story ---------------------------------------------------------------------------------
    def generate_story(self, article, audience, style, fresh=False, language="en"):
        article = str(article or "").strip().upper()
        audience = AUDIENCE_ALIASES.get(str(audience).lower())
        language = "mr" if str(language).lower() in ("mr", "marathi") else "en"
        if not article or not audience or style not in STYLES:
            raise ServiceError("bad_request", "Provide a valid article, audience (kid/student/adult) and style.", 400)

        key = (article, audience, style, language)
        hit = self._cache.get(key)
        if hit and not fresh and self._clock() - hit[0] < CACHE_TTL_S:
            return {**hit[1], "cached": True}

        objective = f"Help a {audience} understand what Article {article} provides and why it matters."
        try:
            primary, related = self.retriever.retrieve_for_story(article, objective=objective)
        except RetrievalError as e:
            raise ServiceError("insufficient_source", f"{e} Please retry or choose another article.", 422)
        if sum(len(p.text) for p in primary) < MIN_PRIMARY_CHARS:
            raise ServiceError("insufficient_source", "The authoritative text for this article is too short to build a story safely.", 422)
        title = primary[0].article_title

        feedback, last_report = None, None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                raw = self.generate(
                    prompts.STORY_SYSTEM,
                    prompts.story_prompt(article, title, audience, style, objective, primary, related, feedback, language),
                )
            except llm.LLMError as e:
                raise ServiceError("ai_unavailable", f"The story engine is unavailable right now. {e}", 503)
            raw = _normalise_raw(raw)
            if isinstance(raw, dict):
                raw["article"], raw["audience"], raw["style"], raw["language"] = article, audience, style, language
            try:
                story = Story.model_validate(raw)
            except ValidationError as e:
                feedback = _pydantic_feedback(e)
                log.info("attempt %d failed schema validation: %s", attempt, feedback[:3])
                continue
            report = validate_story(story, primary, related, article)
            last_report = report
            if report.ok:
                payload = self._payload(story, primary, related, report, attempt)
                self._cache[key] = (self._clock(), payload)
                return payload
            feedback = report.errors
            if report.removed:
                log.info("removed claims: %s", [(r["reason"]) for r in report.removed][:5])
            log.info("attempt %d failed validation: %s", attempt, report.errors[:6])
        raise ServiceError(
            "validation_failed",
            "We couldn't produce a story we could verify against the Constitution, so we're not showing one. Please retry.",
            502,
        )

    @staticmethod
    def _payload(story, primary, related, report, attempts):
        cited = {sid for s in story.scenes for c in s.claims for sid in c.source_ids} | {sid for q in story.quiz for sid in q.source_ids}
        sources = [{**p.to_public(), "cited": p.chunk_id in cited} for p in [*primary, *related]]
        return {
            "story": story.model_dump(),
            "sources": sources,
            "validation": {
                "passed": True,
                "attempts": attempts,
                "claims_verified": sum(len(s.claims) for s in story.scenes),
                "claims_removed": len(report.removed),
                "checks": ["schema", "article match", "citations resolve", "claim-to-source support",
                           "quotations verbatim", "no invented cases/statutes/penalties", "branch graph"],
            },
            "cached": False,
        }

    # ---- follow-up -----------------------------------------------------------------------------
    def ask(self, article, audience, question, character, scene_summary="", history=None, language="en"):
        article = str(article or "").strip().upper()
        audience = AUDIENCE_ALIASES.get(str(audience).lower())
        question = (question or "").strip()
        language = "mr" if str(language).lower() in ("mr", "marathi") else "en"
        if not article or not audience or not question or len(question) > 500:
            raise ServiceError("bad_request", "Provide an article, audience and a question (max 500 characters).", 400)
        character = {"name": str((character or {}).get("name", "Guide"))[:40], "role": str((character or {}).get("role", "guide"))[:60]}

        try:
            primary, extra = self.retriever.retrieve_for_question(question, article)
        except Exception:
            raise ServiceError("insufficient_source", "Could not retrieve source text. Please retry.", 422)
        if not primary:
            raise ServiceError("insufficient_source", f"Article {article} is not in the indexed text.", 422)
        title = primary[0].article_title

        feedback = None
        for _attempt in range(2):
            try:
                raw = self.generate(
                    prompts.FOLLOWUP_SYSTEM,
                    prompts.followup_prompt(article, title, audience, character, str(scene_summary)[:400], history, question, primary, extra, feedback, language),
                    temperature=0.4,
                )
            except llm.LLMError as e:
                raise ServiceError("ai_unavailable", f"The story engine is unavailable right now. {e}", 503)
            try:
                ans = FollowUpAnswer.model_validate(raw)
            except ValidationError:
                feedback = "response did not match the required JSON shape"
                continue
            ok, why = validate_answer(ans, primary, extra)
            if ok:
                return self._answer_payload(ans, primary, extra)
            feedback = why
        return {"answer": UNSUPPORTED_ANSWER, "supported": False, "emotion": "thoughtful", "sources": [], "validated": False}

    @staticmethod
    def _answer_payload(ans, primary, extra):
        passages = {p.chunk_id: p for p in [*primary, *extra]}
        if not ans.supported:
            allowed = {p.article for p in passages.values()}
            clean = not text_problems(ans.answer, passages, allowed)
            return {"answer": ans.answer if clean else UNSUPPORTED_ANSWER, "supported": False, "emotion": "thoughtful", "sources": [], "validated": True}
        ids = []
        for c in ans.claims:
            ids.extend(i for i in c.source_ids if i not in ids)
        return {
            "answer": ans.answer,
            "supported": True,
            "emotion": ans.emotion,
            "sources": [passages[i].to_public() for i in ids],
            "validated": True,
        }

