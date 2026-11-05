"""
Embedding index over the Constitution passages (Gemini embeddings), used for hybrid retrieval.

English passage text and, when available, the official Marathi text are embedded separately, so a Marathi, Hindi or
English question can land on the right provision by meaning. Vectors are stored in backend/data/embeddings.npz;
no vector database server is needed for ~1,000 passages (a normalised matrix and a dot product are exact and instant).

    python embeddings.py build        # (re)build the index from data/constitution.json
    python embeddings.py query "can police arrest me without telling me why"
"""
import logging
import os
import sys
import time

import numpy as np

log = logging.getLogger("samvidhan.embeddings")

MODEL = os.environ.get("EMBED_MODEL", "models/gemini-embedding-001")
DIM = 768
INDEX_PATH = os.path.join(os.path.dirname(__file__), "data", "embeddings.npz")


def _configure():
    import google.generativeai as genai
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    key = os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("No Gemini API key configured (GENAI_API_KEY).")
    genai.configure(api_key=key)
    return genai


def _norm(m):
    m = np.asarray(m, dtype=np.float32)
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.maximum(n, 1e-9)


def embed(texts, task_type, timeout=30):
    """List[str] -> normalised float32 matrix (len(texts), DIM). Retries transient failures."""
    genai = _configure()
    last = None
    for attempt in range(7):
        try:
            r = genai.embed_content(model=MODEL, content=texts, task_type=task_type, output_dimensionality=DIM, request_options={"timeout": timeout})
            return _norm(r["embedding"])
        except Exception as e:  # noqa: BLE001
            last = e
            # a spent per-minute quota needs a real pause; other errors a short one
            time.sleep(20 * (attempt + 1) if type(e).__name__ == "ResourceExhausted" else 2 * (attempt + 1))
    raise RuntimeError(f"embedding failed: {type(last).__name__}")


def passage_inputs(passages):
    """-> list of (chunk_id, lang, text) to embed."""
    out = []
    for p in passages:
        head = f"{p.display_label} - {p.article_title}. "
        out.append((p.chunk_id, "en", (head + p.text)[:6000]))
        if p.text_mr:
            out.append((p.chunk_id, "mr", (head + p.text_mr)[:6000]))
    return out


def build(passages, path=INDEX_PATH, batch=12):
    items = passage_inputs(passages)
    vecs = []
    for i in range(0, len(items), batch):
        vecs.append(embed([t for _, _, t in items[i:i + batch]], "retrieval_document", timeout=90))
        print(f"embedded {min(i + batch, len(items))}/{len(items)}", flush=True)
        time.sleep(1.5)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, ids=np.array([c for c, _, _ in items]), langs=np.array([l for _, l, _ in items]), vecs=np.vstack(vecs), model=np.array(MODEL))
    print("saved", path, "vectors:", sum(len(v) for v in vecs))


class EmbeddingIndex:
    def __init__(self, path=INDEX_PATH):
        z = np.load(path, allow_pickle=False)
        self.ids = [str(x) for x in z["ids"]]
        self.langs = [str(x) for x in z["langs"]]
        self.vecs = z["vecs"].astype(np.float32)
        self.model = str(z["model"]) if "model" in z else MODEL
        self._cache = {}

    @classmethod
    def load_if_present(cls, path=INDEX_PATH):
        try:
            if os.path.exists(path):
                return cls(path)
        except Exception as e:  # noqa: BLE001
            log.warning("could not load embedding index: %s", e)
        return None

    def query_vectors(self, texts):
        key = tuple(texts)
        if key not in self._cache:
            if len(self._cache) > 200:
                self._cache.clear()
            self._cache[key] = embed(list(texts), "retrieval_query", timeout=15)
        return self._cache[key]

    def search(self, texts, k=8, exclude_ids=()):
        """Best cosine similarity per passage over the English and Marathi vectors and over all query texts."""
        q = self.query_vectors([t for t in texts if t and t.strip()])
        sims = (q @ self.vecs.T).max(axis=0)  # best over the query texts
        best = {}
        for i, s in enumerate(sims):
            cid = self.ids[i]
            if cid in exclude_ids:
                continue
            if s > best.get(cid, -1):
                best[cid] = float(s)
        return sorted(best.items(), key=lambda x: -x[1])[:k]


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    from story.corpus import load_passages

    if sys.argv[1] == "build":
        build(load_passages())
    elif sys.argv[1] == "query":
        idx = EmbeddingIndex()
        by_id = {p.chunk_id: p for p in load_passages()}
        for cid, s in idx.search([sys.argv[2]], k=6):
            print(round(s, 3), cid, by_id[cid].display_label, "-", by_id[cid].article_title[:70])
