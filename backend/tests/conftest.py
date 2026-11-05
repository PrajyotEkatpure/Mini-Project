import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from story.retriever import ConstitutionRetriever  # noqa: E402
from story.service import StoryService  # noqa: E402


def good_story(article="21"):
    """A valid story about Article 21 whose claims paraphrase the real corpus text."""
    claim = {
        "id": "c1",
        "text": "No person can be deprived of life or personal liberty except according to procedure established by law.",
        "source_ids": ["A21-0"],
        "quote": "procedure established by law",
    }

    def line(who, text, emotion="neutral"):
        return {"speaker": who, "text": text, "emotion": emotion, "pose": "talking"}

    def scene(sid, title, nxt=None, choices=None, claims=None):
        return {
            "id": sid, "title": title, "description": "A made-up scene for learning.", "background": "school_classroom",
            "background_prompt": "a classroom", "staging": [{"character": "asha", "position": "left"}, {"character": "ravi", "position": "right"}],
            "dialogue": [line("asha", "Why does this article matter, Ravi?", "curious"), line("ravi", "It protects life and personal liberty.", "happy")],
            "learning_objective": "Understand Article 21.", "claims": claims if claims is not None else [dict(claim)],
            "choices": choices or [], "next_scene_id": nxt, "summary": "Life and liberty are protected.", "is_hypothetical": True,
        }

    return {
        "title": "The Library Key", "article": article, "audience": "student", "style": "everyday",
        "synopsis": "Two friends discuss Article 21.",
        "characters": [
            {"id": "asha", "name": "Asha", "role": "student", "skin": "wheat", "hair": "black", "outfit": "teal", "accessory": "none"},
            {"id": "ravi", "name": "Ravi", "role": "teacher", "skin": "brown", "hair": "grey", "outfit": "navy", "accessory": "glasses"},
        ],
        "start_scene_id": "s1",
        "scenes": [
            scene("s1", "Question", choices=[
                {"id": "ask", "text": "Ask what it means", "next_scene_id": "s2", "feedback": "Good: asking helps.", "is_hypothetical": True},
                {"id": "skip", "text": "Skip ahead", "next_scene_id": "s3", "feedback": "You can always come back.", "is_hypothetical": True}]),
            scene("s2", "Explanation", nxt="s3"),
            scene("s3", "Wrap up", claims=[dict(claim, id="c2")]),
        ],
        "key_concepts": ["life", "personal liberty", "procedure established by law"],
        "final_summary": "Article 21 says no person is deprived of life or personal liberty except by procedure established by law.",
        "quiz": [
            {"question": "What can't be taken away except by procedure established by law?", "options": ["Life and personal liberty", "Taxes"], "answer_index": 0,
             "explanation": "Article 21 protects life and personal liberty.", "source_ids": ["A21-0"]},
            {"question": "Which article is this story about?", "options": ["Article 21", "Article 1"], "answer_index": 0,
             "explanation": "It is about Article 21.", "source_ids": ["A21-0"]},
        ],
    }


class FakeLLM:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def __call__(self, system, prompt, temperature=0.7):
        self.calls.append({"system": system, "prompt": prompt})
        r = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(r, Exception):
            raise r
        return copy.deepcopy(r)


@pytest.fixture(scope="session")
def retriever():
    return ConstitutionRetriever()


@pytest.fixture
def make_service(retriever):
    def _make(*responses):
        llm = FakeLLM(*responses)
        return StoryService(retriever=retriever, generate=llm), llm

    return _make
