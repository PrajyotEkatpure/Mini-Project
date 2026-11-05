"""Strict schema for model-generated story data. Anything that does not parse is rejected before rendering."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Emotion = Literal["neutral", "happy", "curious", "worried", "surprised", "thoughtful", "determined"]
Pose = Literal["standing", "talking", "pointing", "thinking", "reading"]
Position = Literal["left", "center", "right"]
Background = Literal[
    "village_square", "school_classroom", "courtroom", "city_street", "home_interior",
    "market", "parliament", "office", "railway_station", "library",
]
Audience = Literal["kid", "student", "adult"]
Style = Literal["mystery", "adventure", "everyday", "courtroom"]
Language = Literal["en", "mr"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Character(_Strict):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=120)
    skin: Literal["light", "wheat", "brown", "deep"]
    hair: Literal["black", "brown", "grey", "white"]
    outfit: Literal["saffron", "green", "blue", "maroon", "teal", "mustard", "navy", "plum"]
    accessory: Literal["none", "glasses", "turban", "dupatta", "cap", "robe"] = "none"


class DialogueLine(_Strict):
    speaker: str
    text: str = Field(min_length=1, max_length=800)
    emotion: Emotion = "neutral"
    pose: Pose = "talking"


class Staging(_Strict):
    character: str
    position: Position


class Claim(_Strict):
    id: str = Field(pattern=r"^c\d{1,3}$")
    text: str = Field(min_length=8, max_length=800)
    source_ids: List[str] = Field(min_length=1, max_length=4)
    quote: Optional[str] = Field(default=None, max_length=1000)


class Choice(_Strict):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    text: str = Field(min_length=2, max_length=400)
    next_scene_id: str
    feedback: str = Field(min_length=2, max_length=800)
    is_hypothetical: bool = True


class Scene(_Strict):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=2, max_length=1000)
    background: Background
    background_prompt: str = Field(default="", max_length=600)
    staging: List[Staging] = Field(min_length=1, max_length=3)
    dialogue: List[DialogueLine] = Field(min_length=1, max_length=12)
    learning_objective: str = Field(min_length=2, max_length=500)
    claims: List[Claim] = Field(default_factory=list, max_length=6)
    choices: List[Choice] = Field(default_factory=list, max_length=3)
    next_scene_id: Optional[str] = None
    summary: str = Field(min_length=2, max_length=800)
    is_hypothetical: bool = True


class QuizQuestion(_Strict):
    question: str = Field(min_length=5, max_length=600)
    options: List[str] = Field(min_length=2, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=2, max_length=800)
    source_ids: List[str] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def _answer_in_range(self):
        if self.answer_index >= len(self.options):
            raise ValueError("answer_index out of range")
        return self


class Story(_Strict):
    title: str = Field(min_length=2, max_length=240)
    article: str
    audience: Audience
    style: Style
    language: Language = "en"
    synopsis: str = Field(min_length=2, max_length=800)
    characters: List[Character] = Field(min_length=2, max_length=4)
    start_scene_id: str
    scenes: List[Scene] = Field(min_length=3, max_length=9)
    key_concepts: List[str] = Field(min_length=1, max_length=10)
    final_summary: str = Field(min_length=2, max_length=1600)
    quiz: List[QuizQuestion] = Field(min_length=2, max_length=5)

    @field_validator("article", mode="before")
    @classmethod
    def _article_str(cls, v):
        return str(v).strip().upper()


class FollowUpAnswer(_Strict):
    answer: str = Field(min_length=1, max_length=1800)
    supported: bool
    claims: List[Claim] = Field(default_factory=list, max_length=4)
    emotion: Emotion = "neutral"
