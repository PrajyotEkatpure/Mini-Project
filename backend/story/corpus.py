"""Loads the authoritative constitutional text already shipped with the app (frontend/data/data.json)."""
import json
import os
import re
from dataclasses import dataclass, field

SOURCE_NAME = "Constitution of India (Samvidhan article dataset)"
BUILT_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "constitution.json")  # built from the official PDFs
LEGACY_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "data", "data.json")
DEFAULT_CORPUS_PATH = os.environ.get("SAMVIDHAN_CORPUS_PATH") or (BUILT_CORPUS_PATH if os.path.exists(BUILT_CORPUS_PATH) else LEGACY_CORPUS_PATH)
MAX_CHUNK_CHARS = 1500


@dataclass(frozen=True)
class Passage:
    chunk_id: str
    article: str
    article_title: str
    part: str
    part_title: str
    text: str
    source: str = SOURCE_NAME
    score: float = 0.0
    cross_refs: tuple = field(default_factory=tuple)
    text_mr: str = ""  # official Marathi text of the same provision, when available
    kind: str = "article"  # article | preamble | schedule | appendix | notes
    label: str = ""  # human label: "Article 21", "Preamble", "Seventh Schedule"

    @property
    def display_label(self):
        return self.label or f"Article {self.article}"

    def to_public(self):
        return {
            "id": self.chunk_id,
            "label": self.display_label,
            "kind": self.kind,
            "text_mr": self.text_mr,
            "article": self.article,
            "article_title": self.article_title,
            "part": self.part,
            "source": self.source,
            "text": self.text,
            "score": round(self.score, 3),
        }


_REF_LIST_RE = re.compile(r"\barticles?\s+((?:\d+[A-Z]{0,2}(?:\s*\([^)]*\))*(?:\s*,\s*|\s+and\s+|\s+or\s+)?)+)", re.I)


def extract_cross_refs(text):
    """Article numbers this passage explicitly refers to (e.g. 'article 16', 'articles 14 and 15')."""
    refs = set()
    for m in _REF_LIST_RE.finditer(text):
        body = re.sub(r"\([^)]*\)", " ", m.group(1))
        refs.update(r.upper() for r in re.findall(r"\b(\d+[A-Za-z]{0,2})\b", body))
    return tuple(sorted(refs))


def _split_text(text):
    """Split long articles on paragraph boundaries so each chunk stays citable and small."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > MAX_CHUNK_CHARS:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks or [text.strip()]


def _load_built(items):
    return [
        Passage(
            chunk_id=i["chunk_id"], article=str(i["article"]).upper(), article_title=i.get("article_title", ""), part=i.get("part", ""),
            part_title=i.get("part_title", ""), text=i["text"], cross_refs=extract_cross_refs(i["text"]), text_mr=i.get("text_mr", ""),
            kind=i.get("kind", "article"), label=i.get("label", ""),
        )
        for i in items
    ]


def load_passages(path=None):
    path = path or DEFAULT_CORPUS_PATH
    with open(path, encoding="utf-8") as f:
        parts = json.load(f)
    if parts and isinstance(parts[0], dict) and "chunk_id" in parts[0]:  # built from the PDFs (backend/build_corpus.py)
        return _load_built(parts)
    passages = []
    for part in parts:
        for art in part.get("articles", []):
            number = str(art["article"]).strip().upper()
            text = (art.get("description") or "").replace(" ", " ").strip()
            if not text:
                continue
            for i, chunk in enumerate(_split_text(text)):
                passages.append(
                    Passage(
                        chunk_id=f"A{number}-{i}",
                        article=number,
                        article_title=art.get("title", "").strip(),
                        part=part.get("part", ""),
                        part_title=part.get("title", ""),
                        text=chunk,
                        cross_refs=extract_cross_refs(chunk),
                    )
                )
    return passages
