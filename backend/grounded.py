"""
Grounded (RAG) answering for the chatbot and the scenario page.

  question (+history, +image) -> analyse (English standalone question, candidate articles, on-topic?, image relevance)
  -> retrieve the REAL article text from the corpus -> generate an answer that may use only that text
  -> deterministic validation (claim-to-source overlap, verbatim quotes, numbers, no invented cases/statutes/penalties,
     no articles outside the retrieved text) -> regenerate with feedback -> otherwise show the verbatim source text.
Nothing is shown as an answer unless it passed validation.
"""
import logging
import re

from pydantic import ValidationError

from story import llm
from story.prompts import format_passages
from story.retriever import ConstitutionRetriever
from story.schema import Claim, FollowUpAnswer
from story.text_utils import normalize
from story.validator import claim_problem, text_problems, validate_answer

log = logging.getLogger("samvidhan.grounded")

MAX_PASSAGES = 7
MIN_BM25 = 0.22
MAX_ATTEMPTS = 2
_DEVANAGARI = str.maketrans("०१२३४५६७८९", "0123456789")
_AMEND_WORDS = re.compile(r"amend|inserted|omitted|substituted|repeal|added by|w\.e\.f|which year|since when|सुधारणा|दुरुस्ती", re.I)
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12}
_SCHEDULE = re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+schedule|\bschedule\s+(\d{1,2})\b", re.I)
_ART_WORDS = r"(?:articles?|art\.?|अनुच्छेद|कलम)"
_ART_MENTION = re.compile(_ART_WORDS + r"\s*(\d+[A-Za-z]{0,2})", re.I)
_ART_LIST = re.compile(_ART_WORDS + r"\s*((?:\d+[A-Za-z]{0,2}\s*(?:,|and|or|और|आणि|,\s*and)?\s*)+)", re.I)

NOT_FOUND = {
    "English": "I could not find text in the Constitution that answers this, so I will not guess. Try naming the article or the right/topic you are asking about.",
    "Hindi": "मुझे संविधान में इसका उत्तर देने वाला पाठ नहीं मिला, इसलिए मैं अनुमान नहीं लगाऊँगा। कृपया अनुच्छेद या विषय का नाम बताकर पूछें।",
    "Marathi": "संविधानात याचे उत्तर देणारा मजकूर मला सापडला नाही, म्हणून मी अंदाज लावणार नाही. कृपया अनुच्छेद किंवा विषयाचे नाव सांगून विचारा.",
}
SOURCE_ONLY = {
    "English": "I could not safely verify a written explanation, so here is the exact text of the most relevant Constitution provisions.",
    "Hindi": "मैं लिखित व्याख्या को सुरक्षित रूप से सत्यापित नहीं कर सका, इसलिए संबंधित संवैधानिक प्रावधानों का सटीक पाठ नीचे है।",
    "Marathi": "लिखित स्पष्टीकरण सुरक्षितपणे पडताळता आले नाही, म्हणून संबंधित तरतुदींचा अचूक मजकूर खाली दिला आहे.",
}
DISCLAIMER = "Educational information drawn from the text of the Constitution. It is not legal advice; consult a lawyer or legal aid authority for your case."

ANALYSE_SYSTEM = """You prepare a user's message for retrieval from the Constitution of India. Reply with one JSON object only:
{
 "on_topic": bool,             // true if the message is about the Indian Constitution, rights, duties, government structure, law that flows from it, or a real situation where constitutional provisions could apply
 "standalone_question": str,   // the user's question in clear English, resolving follow-ups ("explain simpler", "what about that?") using the conversation
 "article_numbers": [str],     // up to 5 Article numbers of the Constitution of India (e.g. "21", "21A", "226") that most directly govern the question; [] if unsure
 "search_terms": str,          // 4-10 English keywords/legal concepts that would appear in the relevant Article text
 "decline_message": str,       // in __LANG__: one or two polite sentences saying you can only help with the Constitution of India and inviting a question (used only when on_topic is false; for a greeting, greet back)
 "image": {"relevant": bool, "description": str, "irrelevant_message": str}  // ONLY if an image is attached: relevant = connected to the Constitution/law/rights/government/legal or civic situation or a legal document; description = what it shows in English (max 60 words, say if text is unreadable, never invent unreadable text); irrelevant_message = in __LANG__, say the image does not appear related to the Constitution, say briefly what it shows, and invite a relevant image or question
}"""

ANSWER_SYSTEM = """You are RashtraGuru, an accurate assistant on the Constitution of India. You answer ONLY from the SOURCE PASSAGES provided.

RULES (non-negotiable):
- Every statement about what the Constitution says must be supported by the SOURCE PASSAGES. Cite them by exact passage id in "claims".
- Do NOT mention court cases, judgments, statutes/Acts/sections, penalties, amendment numbers, dates, or Articles that are not in the SOURCE PASSAGES.
- Keep qualifications ('subject to', 'reasonable restrictions', 'except'). Do not use 'absolute', 'always', 'never' unless the text does.
- If the passages do not contain the answer, set "supported": false and say plainly (in the reply language) that the available constitutional text does not establish it. Never guess.
- Reply in __LANG__ (native script; keep Article numbers as digits like 'Article 21'). Plain text, no markdown. Explain in simple, friendly words, with a short everyday example when it helps, but the example must not claim a legal outcome.
- If an IMAGE DESCRIPTION is given, connect it to the passages; it is context from the user, not a source of law.
- CLAIMS are machine-checked against the passage text. Write each claim as ONE short English sentence (max 30 words) that REUSES the passage's own words and phrases; do not add outside facts. For a long Article, write 2-4 separate short claims, each citing the passage that contains it. Omit "quote" unless you copy it character-for-character.
OUTPUT JSON only: {"answer": str, "supported": bool, "claims": [ {"id": "c1", "text": str, "source_ids": [passage ids]} ]}   // 1-4 claims when supported"""

SCENARIO_SYSTEM = """You explain how the Constitution of India applies to a real-life situation, using ONLY the SOURCE PASSAGES provided.

RULES (non-negotiable):
- Only discuss Articles that appear in the SOURCE PASSAGES. Do NOT cite court cases, Acts, sections, penalties, amendments or any law not in the passages.
- Do not give a verdict ("you won't win", "this is illegal"). Say what the provisions provide and how they relate to the situation, using careful wording like 'may apply' or 'the Article provides'.
- Preserve qualifications ('reasonable restrictions', 'subject to', 'except').
- Write in English, simple words. Each item must carry one claim citing passage ids. CLAIMS are machine-checked: write each as ONE short sentence (max 30 words) REUSING the passage's own words, adding no outside facts. Omit "quote" unless copied character-for-character.
- If the passages do not fit the situation, set "supported": false and leave the lists empty.
OUTPUT JSON only:
{"supported": bool, "summary": str (simple restatement of the situation),
 "applicable_articles": [ {"article": str, "how_it_applies": str, "claim": {"id": "c1", "text": str, "source_ids": [ids], "quote": optional verbatim excerpt}} ],   // 1-4
 "concepts": [ {"term": str, "explanation": str, "claim": {...}} ],   // 0-3 plain-language explanations of terms in those Articles
 "what_you_can_do": [ {"text": str, "claim": {...}} ]   // 0-3; ONLY constitutional remedies/ways stated in the passages (e.g. approaching courts under the Articles provided), never invented procedures
}"""


def _lang_prompt(system, language):
    return system.replace("__LANG__", language)


def _digits(text):
    return str(text).translate(_DEVANAGARI)


def _drop_bad_quotes(claim, passages_by_id):
    """A 'quote' is optional decoration. If it is not verbatim in the cited text, drop the quote
    (the claim itself is still fully checked) instead of throwing away a correct claim."""
    if not isinstance(claim, dict) or not claim.get("quote"):
        return claim
    src = " ".join(passages_by_id[i].text for i in (claim.get("source_ids") or []) if i in passages_by_id)
    if normalize(str(claim["quote"])) not in normalize(src):
        claim = {k: v for k, v in claim.items() if k != "quote"}
    return claim


def _dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


class GroundedService:
    def __init__(self, retriever=None, generate=None):
        self.retriever = retriever or ConstitutionRetriever()
        self.generate = generate or llm.generate_json

    # ---------------------------------------------------------------- shared steps
    def _call(self, system, prompt, temperature, images=None):
        kwargs = {"temperature": temperature}
        if images:
            kwargs["images"] = images
        return self.generate(system, prompt, **kwargs)

    def analyse(self, message, history, language, image=None):
        hist = "\n".join(f"{h['role']}: {h['content'][:300]}" for h in history[-6:])
        prompt = f"Conversation so far:\n{hist or '(none)'}\n\nUser message: {message or '(no text, image only)'}"
        raw = self._call(_lang_prompt(ANALYSE_SYSTEM, language), prompt, 0.0, [image] if image else None)
        if not isinstance(raw, dict):
            raw = {}
        nums = [str(n).strip().upper() for n in (raw.get("article_numbers") or []) if str(n).strip()]
        return {
            "on_topic": bool(raw.get("on_topic", True)),
            "standalone": str(raw.get("standalone_question") or message or "")[:600],
            "articles": nums[:5],
            "terms": str(raw.get("search_terms") or "")[:300],
            "decline": str(raw.get("decline_message") or "").strip(),
            "image": raw.get("image") if isinstance(raw.get("image"), dict) else None,
        }

    def retrieve(self, raw_text, analysis, always=()):
        """
        Passages for the answer, most trustworthy first:
          1. Article numbers written in the user's text, then the model's candidate Articles (exact lookup)
          2. the Preamble / a named Schedule when asked for
          3. hybrid search (BM25 on the English form + vector search on the original and English text)
          4. `always` Articles (e.g. the constitutional remedies for scenarios)
        Amendment footnotes are included only when the question is about amendments.
        """
        text = _digits(raw_text or "")
        explicit = []
        for m in _ART_LIST.finditer(text):
            explicit += [x.upper() for x in re.findall(r"\d+[A-Za-z]{0,2}", m.group(1))]
        order = _dedupe(explicit + analysis["articles"])
        want_notes = bool(_AMEND_WORDS.search(text + " " + analysis["standalone"]))
        picked = []
        for a in order:
            picked += [p for p in self.retriever.get_article(a) if p.kind != "notes"][:2]
            if want_notes:
                picked += [p for p in self.retriever.get_article(a) if p.kind == "notes"][:1]
        if re.search(r"preamble|\u092a\u094d\u0930\u0938\u094d\u0924\u093e\u0935\u0928\u093e", text + " " + analysis["standalone"], re.I):
            picked += [p for p in self.retriever.get_article("PREAMBLE") if p.kind != "notes"]
        for m in _SCHEDULE.finditer(analysis["standalone"] + " " + text):
            n = _ORDINALS.get(m.group(1).lower()) or (int(m.group(2)) if m.group(2) else None)
            if n:
                picked += self.retriever.get_article(f"SCH{n}")[:2]
        query = f"{analysis['standalone']} {analysis['terms']}".strip()
        have = {p.article for p in picked}
        picked += self.retriever.hybrid_search(query, [raw_text or "", analysis["standalone"]], k=4, exclude_articles=have, include_notes=want_notes)
        for a in always:
            if a not in {p.article for p in picked}:
                picked += [p for p in self.retriever.get_article(a) if p.kind != "notes"][:1]
        out, seen = [], set()
        for p in picked:
            if p.chunk_id not in seen:
                seen.add(p.chunk_id)
                out.append(p)
        return out[:MAX_PASSAGES]

    @staticmethod
    def _article_mentions_ok(text, passages):
        allowed = {p.article for p in passages}
        t = _digits(text)
        bad = []
        for m in _ART_LIST.finditer(t):
            for n in re.findall(r"\d+[A-Za-z]{0,2}", m.group(1)):
                if n.upper() not in allowed:
                    bad.append(n)
        return [f"mentions Article {n}, which was not in the retrieved text" for n in bad]

    # ---------------------------------------------------------------- chatbot
    def chat(self, message, history, language, image=None):
        """image: {"mime_type":..., "data": bytes} or None. Returns a dict for the API."""
        analysis = self.analyse(message, history, language, image)
        img = analysis["image"] if image else None
        prefix = ""
        if image and img and not img.get("relevant", True):
            notice = str(img.get("irrelevant_message") or "").strip() or "This image does not appear to be related to the Constitution."
            if not message.strip() or not analysis["on_topic"]:
                return {"mode": "image_irrelevant", "response": notice, "sources": [], "verified": True}
            prefix = notice + "\n\n"
        if not analysis["on_topic"]:
            return {"mode": "declined", "response": analysis["decline"] or NOT_FOUND.get(language, NOT_FOUND["English"]), "sources": [], "verified": True}

        passages = self.retrieve(f"{message} {analysis['standalone']}", analysis)
        if not passages:
            return {"mode": "not_found", "response": prefix + NOT_FOUND.get(language, NOT_FOUND["English"]), "sources": [], "verified": True}

        desc = f"\nIMAGE DESCRIPTION (user context, not a source): {img.get('description', '')}\n" if img else ""
        if language == "Marathi":
            mr = [f"[{p.chunk_id}] {p.text_mr[:1200]}" for p in passages if p.text_mr]
            if mr:
                desc += "\nOFFICIAL MARATHI TEXT of these passages (use its exact terminology in your Marathi reply; claims stay in English):\n" + "\n".join(mr) + "\n"
        base = f"{format_passages(passages, [])}\n{desc}\nUser's question (English form): {analysis['standalone']}\nUser's original message: {message}\nReply language: {language}\n"
        feedback = None
        for attempt in range(MAX_ATTEMPTS):
            prompt = base + (f"\nYour previous answer was REJECTED by the validator: {feedback}. Fix it using only the passages, or set supported=false.\n" if feedback else "")
            raw = self._call(_lang_prompt(ANSWER_SYSTEM, language), prompt, 0.2)
            try:
                by_pid = {p.chunk_id: p for p in passages}
                data = {k: raw.get(k) for k in ("answer", "supported", "claims") if isinstance(raw, dict) and k in raw}
                data["claims"] = [_drop_bad_quotes(c, by_pid) for c in (data.get("claims") or []) if isinstance(c, dict)]
                ans = FollowUpAnswer.model_validate(data)
            except (ValidationError, AttributeError):
                feedback = "response did not match the required JSON shape"
                continue
            ok, why = validate_answer(ans, passages, [])
            probs = self._article_mentions_ok(ans.answer, passages)
            if ok and not probs:
                if not ans.supported:
                    # The model says the text does not establish an answer: say so plainly and show the closest provisions
                    # verbatim, instead of letting unverified statements through.
                    return {"mode": "not_found", "response": prefix + NOT_FOUND.get(language, NOT_FOUND["English"]),
                            "sources": [p.to_public() for p in passages[:2]], "verified": True}
                ids = _dedupe([i for c in ans.claims for i in c.source_ids])
                by_id = {p.chunk_id: p for p in passages}
                return {
                    "mode": "answer", "response": prefix + ans.answer, "verified": True,
                    "sources": [by_id[i].to_public() for i in ids if i in by_id],
                    "claims": [c.model_dump() for c in ans.claims],
                }
            feedback = why or probs[0]
            log.info("chat attempt %d rejected: %s", attempt + 1, feedback)
        # Could not verify a written explanation: show the verbatim text rather than an unverified answer.
        return {
            "mode": "source_only", "response": prefix + SOURCE_ONLY.get(language, SOURCE_ONLY["English"]), "verified": True,
            "sources": [p.to_public() for p in passages[:3]],
        }

    # ---------------------------------------------------------------- scenario
    def scenario(self, message):
        analysis = self.analyse(message, [], "English")
        if not analysis["on_topic"]:
            return self._scenario_empty(analysis["decline"] or "This does not look like a situation the Constitution of India covers. Please describe a legal or rights-related situation.")
        passages = self.retrieve(message, analysis, always=("32", "226"))
        if not passages:
            return self._scenario_empty("The indexed constitutional text does not contain a provision that clearly fits this situation.")
        base = f"{format_passages(passages, [])}\n\nThe user's situation: {message}\n"
        by_id = {p.chunk_id: p for p in passages}
        feedback = None
        for attempt in range(MAX_ATTEMPTS):
            prompt = base + (f"\nYour previous answer was REJECTED: {feedback}. Fix it using only the passages.\n" if feedback else "")
            raw = self._call(SCENARIO_SYSTEM, prompt, 0.2)
            result, why = self._build_scenario(raw, passages, by_id)
            if result:
                return result
            feedback = why
            log.info("scenario attempt %d rejected: %s", attempt + 1, why)
        # verbatim fallback
        top, seen_a = [], set()
        for p in passages:
            if p.article not in ("32", "226") and p.article not in seen_a:
                seen_a.add(p.article)
                top.append(p)
        top = top[:3] or passages[:3]
        return {
            "scenario": message[:300],
            "Relevant Constitutional Articles": [{"title": f"{p.display_label} - {p.article_title}", "answer": "Closest provision found in the Constitution text. See the exact wording below."} for p in top],
            "Articles": [{"title": f"{p.display_label} (exact text)", "answer": p.text} for p in top],
            "verified": True, "mode": "source_only", "disclaimer": DISCLAIMER,
        }

    @staticmethod
    def _scenario_empty(text):
        return {"scenario": text, "verified": True, "mode": "declined", "disclaimer": DISCLAIMER}

    def _build_scenario(self, raw, passages, by_id):
        if not isinstance(raw, dict):
            return None, "not a JSON object"
        if not raw.get("supported", True):
            return self._scenario_empty(str(raw.get("summary") or "The available constitutional text does not clearly cover this situation.")), ""
        allowed = {p.article for p in passages}
        pdict = {p.chunk_id: p for p in passages}

        def good(item, textkeys):
            try:
                claim = Claim.model_validate(_drop_bad_quotes(item.get("claim"), pdict))
            except (ValidationError, AttributeError, TypeError):
                return None
            if claim_problem(claim, pdict):
                return None
            blob = " ".join(str(item.get(k, "")) for k in textkeys)
            if text_problems(blob, pdict, allowed) or self._article_mentions_ok(blob, passages):
                return None
            return claim

        arts, concepts, todo, cited = [], [], [], []
        for it in raw.get("applicable_articles") or []:
            c = good(it, ("how_it_applies",)) if isinstance(it, dict) else None
            m_art = re.search(r"\d+[A-Za-z]{0,2}", _digits(it.get("article", ""))) if isinstance(it, dict) else None
            art = m_art.group(0).upper() if m_art else ""
            if c and art in allowed:
                arts.append({"title": f"{next((p.display_label for p in passages if p.article == art), 'Article ' + art)} - {next((p.article_title for p in passages if p.article == art), '')}", "answer": str(it["how_it_applies"])})
                cited += c.source_ids
        for it in raw.get("concepts") or []:
            c = good(it, ("term", "explanation")) if isinstance(it, dict) else None
            if c:
                concepts.append({"title": str(it["term"]), "answer": str(it["explanation"])})
                cited += c.source_ids
        for it in raw.get("what_you_can_do") or []:
            c = good(it, ("text",)) if isinstance(it, dict) else None
            if c:
                todo.append({"title": "", "answer": str(it["text"])})
                cited += c.source_ids
        if not arts:
            return None, "no applicable article survived validation (claims must be supported by the cited passage)"
        summary = str(raw.get("summary") or "")
        if text_problems(summary, pdict, allowed):
            summary = ""
        cited_ids = _dedupe(cited)
        texts = [{"title": f"{by_id[i].display_label} - {by_id[i].article_title} (exact text)", "answer": by_id[i].text} for i in cited_ids if i in by_id]
        return {
            "scenario": summary or "Your situation, mapped to the Constitution.",
            "Relevant Constitutional Articles": arts,
            "Simplified Explanations of Legal Concepts": concepts,
            "What the Constitution lets you do": todo,
            "Articles": texts,
            "verified": True, "mode": "answer", "disclaimer": DISCLAIMER,
        }, ""


_service = None


def get_service():
    global _service
    if _service is None:
        _service = GroundedService()
    return _service
