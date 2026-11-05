"""Retriever over the Constitution corpus: exact article lookup + BM25 + cross-reference expansion."""
import logging
import math
from collections import Counter, defaultdict
from dataclasses import replace

from .corpus import load_passages
from .text_utils import content_tokens

log = logging.getLogger("samvidhan.story.retriever")


class RetrievalError(Exception):
    """Authoritative text for the request could not be retrieved with enough confidence."""


class ConstitutionRetriever:
    K1, B = 1.5, 0.75

    def __init__(self, passages=None, corpus_path=None, index="auto"):
        self.passages = passages if passages is not None else load_passages(corpus_path)
        self.index = None
        if index == "auto":
            try:
                from embeddings import EmbeddingIndex  # optional: vector search when an index has been built

                self.index = EmbeddingIndex.load_if_present()
            except Exception as e:  # noqa: BLE001
                log.warning("vector index unavailable: %s", e)
        elif index is not None:
            self.index = index
        self.by_id = {p.chunk_id: p for p in self.passages}
        self.by_article = defaultdict(list)
        for p in self.passages:
            self.by_article[p.article].append(p)
        # title is indexed twice so topical queries ("equality before law") favour the right article
        self._tokens = [content_tokens(f"{p.article_title} {p.article_title} {p.text}") for p in self.passages]
        self._tf = [Counter(t) for t in self._tokens]
        self._avg = sum(len(t) for t in self._tokens) / max(len(self._tokens), 1)
        df = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(self.passages)
        self._idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def get_article(self, article):
        return list(self.by_article.get(str(article).strip().upper(), []))

    def search(self, query, k=4, exclude_articles=(), articles=None, include_notes=True):
        """BM25 search. Scores are divided by the query's best-case score, giving a rough 0..1 relevance."""
        q = content_tokens(query)
        if not q:
            return []
        exclude = {str(a).upper() for a in exclude_articles}
        allowed = {str(a).upper() for a in articles} if articles else None
        scored = []
        for i, p in enumerate(self.passages):
            if p.article in exclude or (allowed is not None and p.article not in allowed) or (p.kind == "notes" and not include_notes):
                continue
            tf, dl = self._tf[i], len(self._tokens[i])
            s = 0.0
            for w in set(q):
                f = tf.get(w)
                if f:
                    s += self._idf[w] * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * dl / self._avg))
            if s > 0:
                scored.append((s, p))
        scored.sort(key=lambda x: -x[0])
        ceiling = sum(self._idf.get(w, 0) * (self.K1 + 1) for w in set(q)) or 1.0
        return [replace(p, score=min(s / ceiling, 1.0)) for s, p in scored[:k]]

    MIN_COSINE = 0.62  # below this a vector hit is treated as unrelated (calibrated on in-domain vs off-topic questions)
    RRF_K = 60

    def hybrid_search(self, bm25_query, raw_texts, k=5, exclude_articles=(), include_notes=False):
        """
        Keyword (BM25 on the English form of the question) + vector search (the original text and its English form, so
        Marathi/Hindi questions match by meaning), merged by reciprocal-rank fusion. Falls back to BM25 alone if the
        vector index or the embedding call is unavailable. Returns passages with score = fused relevance (0..1).
        """
        exclude = {str(a).upper() for a in exclude_articles}
        ok = lambda p: p.article not in exclude and (include_notes or p.kind != "notes")  # noqa: E731
        bm = [p for p in self.search(bm25_query, k=12, exclude_articles=exclude, include_notes=include_notes) if ok(p) and p.score >= 0.2]
        vec = []
        if self.index is not None:
            try:
                for cid, cos in self.index.search(raw_texts, k=12):
                    p = self.by_id.get(cid)
                    if p is not None and ok(p) and cos >= self.MIN_COSINE:
                        vec.append(replace(p, score=cos))
            except Exception as e:  # noqa: BLE001
                log.warning("vector search failed, using keyword search only: %s", e)
        fused = {}
        for lst in (bm, vec):
            for rank, p in enumerate(lst):
                fused[p.chunk_id] = fused.get(p.chunk_id, 0.0) + 1.0 / (self.RRF_K + rank + 1)
        if not fused:
            return []
        top = max(fused.values())
        by_id = {p.chunk_id: p for p in [*bm, *vec]}
        ranked = sorted(fused.items(), key=lambda x: -x[1])[:k]
        return [replace(by_id[c], score=round(s / top, 3)) for c, s in ranked]

    def retrieve_for_story(self, article, objective="", min_related_score=0.2, max_related=3):
        """
        Primary passages come from an exact article-number lookup (authoritative, score 1.0).
        Related passages are articles it explicitly cross-references, then topical BM25 hits above
        a relevance threshold. Raises RetrievalError if the article's own text is not in the corpus.
        """
        primary = [p for p in self.get_article(article) if p.kind != "notes"]
        if not primary:
            raise RetrievalError(f"Article {article} was not found in the indexed constitutional text.")
        primary = [replace(p, score=1.0) for p in primary]

        seen = {p.article for p in primary}
        related = []
        for p in primary:
            for ref in p.cross_refs:
                if ref not in seen and ref in self.by_article:
                    seen.add(ref)
                    related.append(replace(self.by_article[ref][0], score=0.5))
        related = related[:max_related]

        query = f"{primary[0].article_title} {objective}"
        extra = [h for h in self.search(query, k=max_related, exclude_articles=seen) if h.score >= min_related_score]
        related.extend(extra[: max(0, max_related - len(related))])
        log.info("retrieved %d primary + %d related passages for article %s", len(primary), len(related), article)
        return primary, related

    def retrieve_for_question(self, question, article, k=2, min_score=0.2):
        """Follow-up retrieval: the story's article is always included; other articles only above the threshold."""
        primary = [replace(p, score=1.0) for p in self.get_article(article) if p.kind != "notes"]
        hits = [h for h in self.search(question, k=k, exclude_articles=[article]) if h.score >= min_score]
        return primary, hits
