import copy

import pytest
from flask import Flask
from pydantic import ValidationError

from conftest import good_story
from story import llm as llm_mod
from story.retriever import RetrievalError
from story.routes import create_blueprint
from story.schema import Story
from story.service import ServiceError, UNSUPPORTED_ANSWER
from story.validator import validate_story


# ---------------- retrieval ----------------
def test_exact_article_lookup_returns_authoritative_text(retriever):
    primary, _ = retriever.retrieve_for_story("21")
    assert [p.chunk_id for p in primary] == ["A21-0"]
    assert "procedure established by law" in primary[0].text
    assert primary[0].score == 1.0 and primary[0].source and primary[0].part == "Part III"


def test_alphanumeric_article_and_case_insensitive(retriever):
    primary, _ = retriever.retrieve_for_story("21a")
    assert primary[0].article == "21A"


def test_cross_references_are_retrieved(retriever):
    primary, related = retriever.retrieve_for_story("15")
    assert {"19", "29", "30"} <= set(primary[0].cross_refs)
    assert "19" in {r.article for r in related}


def test_unknown_article_raises(retriever):
    with pytest.raises(RetrievalError):
        retriever.retrieve_for_story("9999")


def test_topical_search_ranks_relevant_article(retriever):
    hits = retriever.search("arrested without being informed of the grounds of arrest", k=3)
    assert hits[0].article == "22"


def test_followup_retrieval_threshold_filters_noise(retriever):
    _, extra = retriever.retrieve_for_question("zxqv blorp", "21")
    assert extra == []


# ---------------- schema ----------------
def test_schema_accepts_good_story():
    Story.model_validate(good_story())


def test_schema_rejects_extra_keys_and_bad_enums():
    bad = good_story()
    bad["scenes"][0]["background"] = "moon_base"
    with pytest.raises(ValidationError):
        Story.model_validate(bad)
    bad = good_story()
    bad["surprise"] = 1
    with pytest.raises(ValidationError):
        Story.model_validate(bad)


# ---------------- validator ----------------
def _validate(raw, retriever, article="21"):
    story = Story.model_validate(raw)
    primary, related = retriever.retrieve_for_story(article)
    return story, validate_story(story, primary, related, article)


def test_valid_story_passes(retriever):
    story, report = _validate(good_story(), retriever)
    assert report.ok, report.errors
    assert sum(len(s.claims) for s in story.scenes) == 3


def test_unknown_source_id_claim_removed(retriever):
    raw = good_story()
    raw["scenes"][0]["claims"].append({"id": "c9", "text": "Every citizen has a right to a job under this article.", "source_ids": ["A99-0"]})
    story, report = _validate(raw, retriever)
    assert report.ok
    assert any("unknown source" in r["reason"] for r in report.removed)
    assert all("job" not in c.text for s in story.scenes for c in s.claims)


def test_unsupported_claim_content_removed(retriever):
    raw = good_story()
    raw["scenes"][0]["claims"].append({"id": "c9", "text": "Violators receive five years of imprisonment automatically.", "source_ids": ["A21-0"]})
    story, report = _validate(raw, retriever)
    assert report.removed and report.ok


def test_fabricated_quote_in_claim_removed(retriever):
    raw = good_story()
    raw["scenes"][0]["claims"][0]["quote"] = "life shall be sacred and absolutely inviolable"
    story, report = _validate(raw, retriever)
    assert any("quoted wording" in r["reason"] for r in report.removed)


def test_fabricated_quote_in_dialogue_is_error(retriever):
    raw = good_story()
    raw["scenes"][1]["dialogue"][1]["text"] = 'The Constitution says "every person shall enjoy unlimited freedom everywhere".'
    _, report = _validate(raw, retriever)
    assert not report.ok and any("quotation" in e for e in report.errors)


def test_verbatim_quote_in_dialogue_is_fine(retriever):
    raw = good_story()
    raw["scenes"][1]["dialogue"][1]["text"] = 'It says "except according to procedure established by law".'
    _, report = _validate(raw, retriever)
    assert report.ok, report.errors


@pytest.mark.parametrize("text", [
    "In Maneka Gandhi v. Union of India the court expanded it.",
    "A landmark judgment made this stronger.",
    "Under Section 302 of the IPC the punishment is severe.",
    "The fine of Rs 5000 applies.",
    "The 44th Amendment changed this.",
    "Article 370 also applies here.",
])
def test_invented_legal_material_is_error(retriever, text):
    raw = good_story()
    raw["scenes"][1]["dialogue"][1]["text"] = text
    _, report = _validate(raw, retriever)
    assert not report.ok


def test_wrong_article_is_error(retriever):
    story = Story.model_validate(good_story(article="14"))
    primary, related = retriever.retrieve_for_story("21")
    assert not validate_story(story, primary, related, "21").ok


def test_no_claim_cites_selected_article_is_error(retriever):
    raw = good_story()
    for s in raw["scenes"]:
        s["claims"] = []
    _, report = _validate(raw, retriever)
    assert not report.ok


def test_quiz_with_bad_citation_dropped_then_story_rejected(retriever):
    raw = good_story()
    raw["quiz"][0]["source_ids"] = ["A77-0"]
    story, report = _validate(raw, retriever)
    assert len(story.quiz) == 1 and not report.ok


# ---------------- branching ----------------
def test_branch_to_missing_scene_is_error(retriever):
    raw = good_story()
    raw["scenes"][0]["choices"][0]["next_scene_id"] = "nowhere"
    _, report = _validate(raw, retriever)
    assert any("missing scene" in e for e in report.errors)


def test_unreachable_scene_is_error(retriever):
    raw = good_story()
    raw["scenes"][0]["choices"] = []
    raw["scenes"][0]["next_scene_id"] = "s3"
    _, report = _validate(raw, retriever)
    assert any("unreachable" in e for e in report.errors)


def test_inescapable_loop_is_error(retriever):
    raw = good_story()
    raw["scenes"][2]["next_scene_id"] = "s1"
    _, report = _validate(raw, retriever)
    assert any("ending" in e for e in report.errors)


def test_unstaged_speaker_is_error(retriever):
    raw = good_story()
    raw["scenes"][0]["staging"] = raw["scenes"][0]["staging"][:1]
    _, report = _validate(raw, retriever)
    assert any("not on stage" in e for e in report.errors)


# ---------------- service ----------------
def test_generate_passes_retrieved_text_into_prompt_and_returns_sources(make_service):
    svc, llm = make_service(good_story())
    out = svc.generate_story("21", "student", "everyday")
    prompt = llm.calls[0]["prompt"]
    assert "[A21-0]" in prompt and "procedure established by law" in prompt
    assert out["validation"]["passed"] and out["validation"]["attempts"] == 1
    cited = [s for s in out["sources"] if s["cited"]]
    assert cited and cited[0]["id"] == "A21-0" and cited[0]["source"]
    assert len(out["story"]["characters"]) >= 2


def test_teenager_alias_and_cache(make_service):
    svc, llm = make_service(good_story())
    svc.generate_story("21", "teenager", "everyday")
    again = svc.generate_story("21", "student", "everyday")
    assert again["cached"] and len(llm.calls) == 1


def test_retry_with_validator_feedback_then_success(make_service):
    bad = good_story()
    bad["scenes"][1]["dialogue"][1]["text"] = "In Foo v. Bar the court decided otherwise."
    svc, llm = make_service(bad, good_story())
    out = svc.generate_story("21", "adult", "mystery")
    assert out["validation"]["attempts"] == 2
    assert "REJECTED" in llm.calls[1]["prompt"] and "unsupported case citation" in llm.calls[1]["prompt"]


def test_persistent_invalid_output_is_not_shown(make_service):
    bad = good_story()
    bad["scenes"][1]["dialogue"][1]["text"] = "In Foo v. Bar the court decided otherwise."
    svc, llm = make_service(bad)
    with pytest.raises(ServiceError) as e:
        svc.generate_story("21", "kid", "adventure")
    assert e.value.code == "validation_failed" and len(llm.calls) == 3


def test_garbage_model_output_is_handled(make_service):
    svc, _ = make_service({"nonsense": True})
    with pytest.raises(ServiceError) as e:
        svc.generate_story("21", "kid", "adventure")
    assert e.value.code == "validation_failed"


def test_llm_outage_is_graceful(make_service):
    svc, _ = make_service(llm_mod.LLMError("quota"))
    with pytest.raises(ServiceError) as e:
        svc.generate_story("21", "kid", "adventure")
    assert e.value.code == "ai_unavailable" and e.value.status == 503


def test_unknown_article_never_reaches_model(make_service):
    svc, llm = make_service(good_story())
    with pytest.raises(ServiceError) as e:
        svc.generate_story("9999", "kid", "adventure")
    assert e.value.code == "insufficient_source" and llm.calls == []


def test_bad_inputs(make_service):
    svc, _ = make_service(good_story())
    for args in [("21", "robot", "everyday"), ("21", "kid", "horror"), ("", "kid", "everyday")]:
        with pytest.raises(ServiceError) as e:
            svc.generate_story(*args)
        assert e.value.code == "bad_request"


# ---------------- follow-up ----------------
def _answer(supported=True, text="It means life and liberty can only be limited by a procedure set by law.", ids=("A21-0",)):
    return {"answer": text, "supported": supported, "emotion": "thoughtful",
            "claims": [{"id": "c1", "text": "No person is deprived of life or personal liberty except according to procedure established by law.", "source_ids": list(ids)}] if supported else []}


def test_followup_supported_uses_retrieval_and_returns_sources(make_service):
    svc, llm = make_service(_answer())
    out = svc.ask("21", "student", "Which part of the Constitution supports that?", {"name": "Ravi", "role": "teacher"}, "scene")
    assert out["supported"] and out["validated"] and out["sources"][0]["id"] == "A21-0"
    assert "procedure established by law" in llm.calls[0]["prompt"]


def test_followup_unsupported_is_transparent(make_service):
    svc, _ = make_service(_answer(supported=False, text="The text I have does not say what the fee is."))
    out = svc.ask("21", "kid", "How much is the fee?", {"name": "A", "role": "b"})
    assert out["supported"] is False and out["sources"] == []


def test_followup_hallucination_rejected_then_falls_back(make_service):
    bad = _answer(text="As the Supreme Court held in Foo v. Bar, this is absolute.")
    svc, llm = make_service(bad)
    out = svc.ask("21", "adult", "Any case law?", {"name": "A", "role": "b"})
    assert out["answer"] == UNSUPPORTED_ANSWER and not out["validated"] and len(llm.calls) == 2


def test_followup_unresolvable_citation_rejected(make_service):
    svc, _ = make_service(_answer(ids=("A55-0",)))
    out = svc.ask("21", "kid", "why?", {"name": "A", "role": "b"})
    assert out["answer"] == UNSUPPORTED_ANSWER


# ---------------- HTTP ----------------
@pytest.fixture
def client(make_service):
    svc, _ = make_service(good_story())
    app = Flask(__name__)
    app.register_blueprint(create_blueprint(svc))
    return app.test_client()


def test_http_generate_ok(client):
    r = client.post("/api/story/generate", json={"article": 21, "audience": "kid", "style": "everyday"})
    assert r.status_code == 200 and r.json["story"]["start_scene_id"] == "s1"


def test_http_errors_are_structured(client):
    r = client.post("/api/story/generate", json={"article": 9999, "audience": "kid", "style": "everyday"})
    assert r.status_code == 422 and r.json["code"] == "insufficient_source"
    r = client.post("/api/story/ask", json={"article": 21})
    assert r.status_code == 400 and "error" in r.json
