import re
import unicodedata

STOPWORDS = frozenset(
    """a an and are as at be been being but by can could do does for from had has have he her his i if in into is it its
    may me my no not of on or our shall she so such that the their them then there these they this those to under was we were
    what when where which who will with would you your""".split()
)


def normalize(text):
    """Lowercase, unify quotes/dashes/whitespace so quote matching is robust."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace(" ", " ")
    text = re.sub(r"[‘’‚′]", "'", text)
    text = re.sub(r"[“”„″]", '"', text)
    text = re.sub(r"[‐-―]", "-", text)
    text = re.sub(r"[^\w\s'\"()-]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def stem(word):
    for suffix in ("ations", "ation", "ings", "ing", "ed", "es", "s", "ly"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def content_tokens(text):
    return [stem(t) for t in re.findall(r"[a-z0-9]+", normalize(text)) if t not in STOPWORDS and len(t) > 1]
