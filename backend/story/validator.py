"""
Deterministic validation of generated stories against the retrieved passages.

Two outcomes:
  * claim/quiz-level problems -> the offending item is removed (sanitised) and reported
  * story-level problems (wrong article, broken graph, invented legal material in dialogue) -> `errors`,
    which the service turns into a regeneration request.
"""
import re
from dataclasses import dataclass, field

from .text_utils import content_tokens, normalize

MIN_CLAIM_OVERLAP = 0.6
MIN_QUOTE_WORDS = 4

_ARTICLE_REF = re.compile(r"\bart(?:icle|\.)s?\s+(\d+[A-Za-z]{0,2})", re.I)
_QUOTED = re.compile(r'"([^"]{3,})"')

# Legal material the model must not introduce unless the retrieved text itself contains it.
_UNSUPPORTED_PATTERNS = [
    ("case citation", re.compile(r"\b[A-Z][\w.']+(?: [A-Z][\w.']+)* (?:v\.?|vs\.?) [A-Z][\w.']+(?: [A-Z][\w.']+)*")),
    ("judgment reference", re.compile(r"\b(landmark|precedent|(?:supreme|high) court (?:has )?(?:held|ruled|decided|observed))\b", re.I)),
    ("statute reference", re.compile(r"\b(?:sections?\s+\d+[a-z]?|IPC|BNS|BNSS|CrPC|Indian Penal Code|[A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)* Act(?:,)?(?: of)? \d{4})", re.I)),
    ("penalty", re.compile(r"\b(?:imprisonment|jail term|fine of|rs\.?\s?\d|₹\s?\d|\d+\s+(?:years?|months?) (?:in )?(?:jail|prison))", re.I)),
    ("amendment reference", re.compile(r"\b\d{1,3}(?:st|nd|rd|th) amendment\b", re.I)),
]
_ABSOLUTES = re.compile(r"\b(absolute|unlimited|always|never|without exception|under any circumstances|no restrictions?)\b", re.I)
_QUALIFIERS = re.compile(r"\b(except|subject to|provided that|reasonable restrictions?|save as|nothing in this)\b", re.I)


@dataclass
class ValidationReport:
    errors: list = field(default_factory=list)  # story-level failures -> regenerate
    removed: list = field(default_factory=list)  # items dropped as unsupported
    warnings: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


def _source_text(passages, ids):
    return " ".join(passages[i].text for i in ids if i in passages)


def _numbers(text):
    return set(re.findall(r"\d+", text))


def claim_problem(claim, passages):
    """Return a reason string if the claim is not supported by the passages it cites, else None."""
    unknown = [s for s in claim.source_ids if s not in passages]
    if unknown:
        return f"cites unknown source id(s) {unknown}"
    src = _source_text(passages, claim.source_ids)
    src_tokens = set(content_tokens(src)) | set(content_tokens(" ".join(passages[s].article_title for s in claim.source_ids)))
    claim_tokens = set(content_tokens(claim.text))
    if claim_tokens:
        overlap = len(claim_tokens & src_tokens) / len(claim_tokens)
        if overlap < MIN_CLAIM_OVERLAP:
            return f"only {overlap:.0%} of the claim's terms appear in the cited text"
    stray = _numbers(claim.text) - _numbers(src) - _numbers(" ".join(passages[s].article for s in claim.source_ids))
    if stray:
        return f"contains numbers not in the cited text: {sorted(stray)}"
    if claim.quote and normalize(claim.quote) not in normalize(src):
        return "quoted wording does not match the cited text"
    if _ABSOLUTES.search(claim.text) and _QUALIFIERS.search(src):
        absolute = _ABSOLUTES.search(claim.text).group(0).lower()
        if absolute not in src.lower():
            return f"states '{absolute}' although the cited text carries qualifications"
    return None


def text_problems(text, passages, allowed_articles):
    """Checks applicable to any free text (dialogue, summaries, answers): invented law, bad quotes, wrong articles."""
    problems = []
    all_src = normalize(" ".join(p.text + " " + p.article_title for p in passages.values()))
    for label, pattern in _UNSUPPORTED_PATTERNS:
        for m in pattern.finditer(text):
            if normalize(m.group(0)) not in all_src:
                problems.append(f"unsupported {label}: '{m.group(0)}'")
    for m in _ARTICLE_REF.finditer(text):
        if m.group(1).upper() not in allowed_articles:
            problems.append(f"mentions Article {m.group(1)}, which was not retrieved")
    curly = re.sub(r"[“”„]", '"', text)
    for q in _QUOTED.findall(curly):
        if len(q.split()) >= MIN_QUOTE_WORDS and normalize(q) not in all_src:
            problems.append(f"quotation not found in retrieved text: '{q[:60]}'")
    return problems


def _graph_errors(story):
    errors = []
    ids = [s.id for s in story.scenes]
    if len(set(ids)) != len(ids):
        errors.append("duplicate scene ids")
        return errors
    by_id = {s.id: s for s in story.scenes}
    if story.start_scene_id not in by_id:
        errors.append(f"start_scene_id '{story.start_scene_id}' does not exist")
        return errors

    def targets(s):
        t = [c.next_scene_id for c in s.choices]
        if s.next_scene_id:
            t.append(s.next_scene_id)
        return t

    for s in story.scenes:
        for t in targets(s):
            if t not in by_id:
                errors.append(f"scene '{s.id}' points to missing scene '{t}'")
        if s.choices and s.next_scene_id:
            errors.append(f"scene '{s.id}' has both choices and next_scene_id")
    if errors:
        return errors
    seen, stack = set(), [story.start_scene_id]
    while stack:
        cur = stack.pop()
        if cur not in seen:
            seen.add(cur)
            stack.extend(targets(by_id[cur]))
    for sid in ids:
        if sid not in seen:
            errors.append(f"scene '{sid}' is unreachable")
    terminals = {s.id for s in story.scenes if not targets(s)}
    if not terminals:
        errors.append("story has no ending scene")
        return errors
    # every scene must be able to reach an ending (no inescapable loops)
    can_end = set(terminals)
    changed = True
    while changed:
        changed = False
        for s in story.scenes:
            if s.id not in can_end and any(t in can_end for t in targets(s)):
                can_end.add(s.id)
                changed = True
    for sid in ids:
        if sid not in can_end:
            errors.append(f"scene '{sid}' cannot reach an ending")
    return errors


def validate_story(story, primary, related, expected_article):
    """
    Validate and sanitise `story` in place (unsupported claims/quiz items are removed).
    `primary`/`related` are the Passage lists actually returned by the retriever.
    """
    report = ValidationReport()
    passages = {p.chunk_id: p for p in [*primary, *related]}
    primary_ids = {p.chunk_id for p in primary}
    allowed_articles = {p.article for p in passages.values()}

    if story.article != str(expected_article).upper():
        report.errors.append(f"story explains Article {story.article}, expected Article {expected_article}")
    report.errors.extend(_graph_errors(story))

    char_ids = {c.id for c in story.characters}
    if len(char_ids) != len(story.characters):
        report.errors.append("duplicate character ids")
    for s in story.scenes:
        for st in s.staging:
            if st.character not in char_ids:
                report.errors.append(f"scene '{s.id}' stages unknown character '{st.character}'")
        staged = {st.character for st in s.staging}
        for line in s.dialogue:
            if line.speaker not in char_ids:
                report.errors.append(f"scene '{s.id}' has unknown speaker '{line.speaker}'")
            elif line.speaker not in staged:
                report.errors.append(f"scene '{s.id}': speaker '{line.speaker}' is not on stage")
    if len({line.speaker for s in story.scenes for line in s.dialogue}) < 2:
        report.errors.append("fewer than two characters speak")

    # claims: drop the unsupported ones
    for s in story.scenes:
        kept = []
        for c in s.claims:
            why = claim_problem(c, passages)
            if why:
                report.removed.append({"scene": s.id, "claim": c.text, "reason": why})
            else:
                kept.append(c)
        s.claims = kept
    cited = {sid for s in story.scenes for c in s.claims for sid in c.source_ids}
    if not cited & primary_ids:
        report.errors.append("no validated claim cites the selected article's own text")

    # quiz: drop items whose citations do not resolve or whose explanation is unsupported
    kept_quiz = []
    for q in story.quiz:
        if any(sid not in passages for sid in q.source_ids):
            report.removed.append({"scene": "quiz", "claim": q.question, "reason": "cites unknown source id"})
            continue
        # options are deliberately not checked: wrong answers (distractors) may name other articles
        probs = text_problems(f"{q.question} {q.explanation}", passages, allowed_articles)
        if probs:
            report.removed.append({"scene": "quiz", "claim": q.question, "reason": probs[0]})
            continue
        kept_quiz.append(q)
    story.quiz = kept_quiz
    if len(kept_quiz) < 2:
        report.errors.append("fewer than two valid quiz questions remain")

    # free text: any invented law/judgment/penalty, bad quote, or wrong article is a story-level failure
    for s in story.scenes:
        blobs = [s.description, s.summary, s.learning_objective]
        blobs += [line.text for line in s.dialogue] + [c.feedback for c in s.choices]
        for b in blobs:
            for p in text_problems(b, passages, allowed_articles):
                report.errors.append(f"scene '{s.id}': {p}")
    for b in (story.synopsis, story.final_summary, *story.key_concepts):
        for p in text_problems(b, passages, allowed_articles):
            report.errors.append(f"story text: {p}")
    return report


def validate_answer(answer, primary, related):
    """Validate a follow-up answer. Returns (ok, reason). Claims that fail make the whole answer unusable."""
    passages = {p.chunk_id: p for p in [*primary, *related]}
    allowed_articles = {p.article for p in passages.values()}
    if not answer.supported:
        return True, "model reported the sources do not establish an answer"
    if not answer.claims:
        return False, "answer made no citable claim"
    for c in answer.claims:
        why = claim_problem(c, passages)
        if why:
            return False, why
    probs = text_problems(answer.answer, passages, allowed_articles)
    if probs:
        return False, probs[0]
    return True, ""
