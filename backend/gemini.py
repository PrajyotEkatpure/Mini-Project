import json
import os
import re

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# One place to change the model. "gemini-flash-latest" is an alias Google keeps pointing at a live Flash model,
# so the app does not break the next time a specific version is retired.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
API_KEY = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")

SECTIONS = [
    "Applicable Laws and Regulations",
    "Common Scenarios and Their Legal Implications",
    "Relevant Constitutional Articles",
    "Simplified Explanations of Legal Concepts",
    "Articles",
]

_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You advise users on scenarios related to the Indian Constitution. Answer ONLY constitution-related scenarios.
Reply with a single JSON object and nothing else (no markdown, no ``` fences, no ** characters). Keys:
  "scenario": a short simplified restatement of the user's scenario (string)
  "Relevant Constitutional Articles": array of {{"title": "", "answer": ""}} - articles that apply and why
  "Applicable Laws and Regulations": array of {{"title": "", "answer": ""}} - laws and regulations based on the Constitution
  "Simplified Explanations of Legal Concepts": array of {{"title": "", "answer": ""}} - plain-language explanations
  "Common Scenarios and Their Legal Implications": array of {{"title": "", "answer": ""}} - how similar cases are handled
  "Articles": array of {{"title": "", "answer": ""}} - how the articles can be used here, with a real reading link in "answer" where you are certain of one
If the input is not related to the Indian Constitution, return the same keys with empty arrays and put a short polite explanation in "scenario".""",
        ),
        ("human", "{scenario}"),
    ]
)


def _extract_json(text):
    """Pull the JSON object out of a model reply, tolerating code fences and surrounding prose."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.DOTALL)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def _content_to_text(content):
    # Newer Gemini models may return a list of content parts instead of a plain string.
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return content


def _normalise(data):
    """Guarantee every key the UI reads exists and every section is a list of {title, answer}."""
    if not isinstance(data, dict):
        raise ValueError("Model did not return a JSON object")
    out = {"scenario": str(data.get("scenario", ""))}
    for key in SECTIONS:
        items = data.get(key, [])
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            items = []
        out[key] = [
            {"title": str(i.get("title", "")), "answer": str(i.get("answer", ""))}
            for i in items if isinstance(i, dict)
        ]
    return out


def GiveGeminiOutput(scenario):
    if not API_KEY:
        raise RuntimeError("GENAI_API_KEY is not set in backend/.env")
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=API_KEY,
        temperature=0,
        max_retries=2,
        timeout=60,
    )
    last_error = None
    for _ in range(2):  # one retry if the model returns malformed JSON
        reply = (_prompt | llm).invoke({"scenario": scenario})
        try:
            return _normalise(_extract_json(_content_to_text(reply.content)))
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
    raise ValueError(f"Could not parse the model's answer: {last_error}")
