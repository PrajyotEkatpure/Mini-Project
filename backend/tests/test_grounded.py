"""The grounded chatbot/scenario pipeline: nothing unverified may reach the user."""
import copy

import pytest

from grounded import GroundedService, NOT_FOUND


class Seq:
    """Fake LLM returning queued responses in order (analysis first, then answers)."""
    def __init__(self, *r):
        self.r, self.calls = list(r), []

    def __call__(self, system, prompt, temperature=0.7, images=None):
        self.calls.append({"system": system, "prompt": prompt, "images": images})
        x = self.r.pop(0) if len(self.r) > 1 else self.r[0]
        return copy.deepcopy(x)


def analysis(**kw):
    d = {"on_topic": True, "standalone_question": "What is Article 21?", "article_numbers": ["21"], "search_terms": "life personal liberty",
         "decline_message": "I can only help with the Constitution of India.", "image": None}
    d.update(kw)
    return d


GOOD = {"answer": "Article 21 says no person can lose life or personal liberty except by procedure established by law.", "supported": True,
        "claims": [{"id": "c1", "text": "No person shall be deprived of life or personal liberty except according to procedure established by law.", "source_ids": ["A21-0"]}]}


def svc(retriever, *responses):
    return GroundedService(retriever=retriever, generate=Seq(*responses))


def test_good_answer_is_returned_with_verbatim_source(retriever):
    out = svc(retriever, analysis(), GOOD).chat("What is Article 21?", [], "English")
    assert out["mode"] == "answer" and out["verified"]
    assert out["sources"][0]["id"] == "A21-0" and "procedure established by law" in out["sources"][0]["text"]


def test_off_topic_is_declined_without_retrieval(retriever):
    s = svc(retriever, analysis(on_topic=False, decline_message="Only the Constitution, please."))
    out = s.chat("Who won the cricket world cup?", [], "English")
    assert out["mode"] == "declined" and out["sources"] == []
    assert len(s.generate.calls) == 1  # never reached the answering step


def test_invented_case_law_is_rejected_then_falls_back_to_source_text(retriever):
    bad = dict(GOOD, answer="In Maneka Gandhi v. Union of India the Supreme Court held that Article 21 is wide.")
    out = svc(retriever, analysis(), bad).chat("What is Article 21?", [], "English")
    assert out["mode"] == "source_only"
    assert "Maneka" not in out["response"] and out["sources"][0]["id"] == "A21-0"


def test_unsupported_claim_is_rejected(retriever):
    bad = dict(GOOD, claims=[{"id": "c1", "text": "Every citizen gets a free pension of Rs 5000 after sixty years of age.", "source_ids": ["A21-0"]}])
    out = svc(retriever, analysis(), bad).chat("What is Article 21?", [], "English")
    assert out["mode"] == "source_only"


def test_article_not_in_retrieved_text_is_rejected(retriever):
    bad = dict(GOOD, answer="Article 370 also protects life and personal liberty.")
    out = svc(retriever, analysis(), bad).chat("What is Article 21?", [], "English")
    assert out["mode"] == "source_only"


def test_rejected_answer_is_retried_with_feedback(retriever):
    bad = dict(GOOD, answer="See Article 370.")
    s = svc(retriever, analysis(), bad, GOOD)
    out = s.chat("What is Article 21?", [], "English")
    assert out["mode"] == "answer" and "REJECTED" in s.generate.calls[2]["prompt"]


def test_model_saying_unsupported_never_shows_its_text(retriever):
    out = svc(retriever, analysis(), {"answer": "Probably yes, courts usually allow this.", "supported": False, "claims": []}).chat("q", [], "English")
    assert out["mode"] == "not_found" and out["response"] == NOT_FOUND["English"]


def test_bad_quote_is_dropped_but_correct_claim_kept(retriever):
    g = dict(GOOD)
    g["claims"] = [dict(GOOD["claims"][0], quote="this wording is not in the article at all")]
    assert svc(retriever, analysis(), g).chat("What is Article 21?", [], "English")["mode"] == "answer"


def test_irrelevant_image_is_reported(retriever):
    a = analysis(image={"relevant": False, "description": "a plate of food", "irrelevant_message": "This image shows food and is not related to the Constitution."})
    out = svc(retriever, a).chat("", [], "English", image={"mime_type": "image/png", "data": b"x"})
    assert out["mode"] == "image_irrelevant" and "not related" in out["response"]


def test_relevant_image_description_is_passed_to_the_answer_step(retriever):
    a = analysis(image={"relevant": True, "description": "a police arrest memo", "irrelevant_message": ""})
    s = svc(retriever, a, GOOD)
    out = s.chat("what does this mean", [], "English", image={"mime_type": "image/png", "data": b"x"})
    assert out["mode"] == "answer" and "a police arrest memo" in s.generate.calls[1]["prompt"]
    assert s.generate.calls[0]["images"]  # the image goes to the analysis step only


def test_explicit_article_number_in_question_is_always_retrieved(retriever):
    s = svc(retriever, analysis(article_numbers=[]), GOOD)
    s.chat("explain Article 21 please", [], "English")
    assert "A21-0" in s.generate.calls[1]["prompt"]


def test_scenario_keeps_only_validated_items(retriever):
    raw = {"supported": True, "summary": "A person is arrested.", "applicable_articles": [
        {"article": "Article 22", "how_it_applies": "Article 22 requires telling the arrested person the grounds.",
         "claim": {"id": "c1", "text": "No person who is arrested shall be detained in custody without being informed of the grounds for such arrest.", "source_ids": ["A22-0"]}},
        {"article": "21", "how_it_applies": "Article 21 gives a guaranteed pension.",
         "claim": {"id": "c2", "text": "Every person is guaranteed a monthly pension of Rs 9000 under this Article.", "source_ids": ["A21-0"]}}],
        "concepts": [], "what_you_can_do": []}
    out = svc(retriever, analysis(article_numbers=["22", "21"]), raw).scenario("Police arrested me and gave no reason.")
    titles = [i["title"] for i in out["Relevant Constitutional Articles"]]
    assert len(titles) == 1 and titles[0].startswith("Article 22") and out["mode"] == "answer"
    assert any("exact text" in t["title"] for t in out["Articles"])


def test_scenario_with_nothing_valid_shows_source_text_only(retriever):
    raw = {"supported": True, "summary": "x", "applicable_articles": [
        {"article": "22", "how_it_applies": "Made up.", "claim": {"id": "c1", "text": "Arrested people receive a million rupees compensation.", "source_ids": ["A22-0"]}}]}
    out = svc(retriever, analysis(article_numbers=["22"]), raw).scenario("Police arrested me.")
    assert out["mode"] == "source_only" and "million" not in str(out)
