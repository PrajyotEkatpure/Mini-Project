"""
Build the Constitution corpus from the official English PDF (and, when available, the Marathi text) into
backend/data/constitution.json. Run once (needs PyMuPDF):

    python build_corpus.py --en "path/Constitution.pdf" [--mr-dir path/to/marathi_page_texts]

Output passages: Preamble, every Article (with Part), amendment footnotes ("notes"), Schedules and Appendices.
Each passage: chunk_id, article, article_title, part, part_title, text, text_mr, kind, label, notes_for.
"""
import argparse
import json
import os
import re

import fitz

OUT = os.path.join(os.path.dirname(__file__), "data", "constitution.json")
MAX_CHUNK = 1500
ART_FIRST_PAGE, ART_LAST_PAGE = 32, 283  # 1-based, inclusive (Preamble .. Article 395)
SCHED_FIRST_PAGE = 284

ORD = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH", "TENTH", "ELEVENTH", "TWELFTH"]
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}

FOOT_START = re.compile(
    r"^(\d{1,3})\.\s+(Subs\.|Ins\.|Added|Omitted|Rep\.|Re-?numbered|The words|The brackets|The figures|Sub-clause|Clauses?|Entry|Entries|Art\.|Arts\.|"
    r"Article|Cl\.|Paragraph|Para|Chapter|Part|Proviso|See|Now|Sub-|Certain|Words|In |Section|S\.|Rule|Explanation|Vide|Subs|Ins|Omit|Rep|For |The |This |These |"
    r"Entries|Ibid|Sub|Para\.)"
)
ART_HEAD = re.compile(r"^\**(?:\d{1,3}\[|\[)?\**(\d{1,3}[A-Z]{0,2})\.(?:\s+(?=\S)|$)")
PART_HEAD = re.compile(r"^(?:\d{1,3}\[)?PART\s+([IVX]+[A-Z]?)(?:\s+([A-Z][A-Z ,'\-—–&]+))?\]?$")
TITLE_END = re.compile(r"\]?\.\s?[—⎯–-]{1,2}")
PARA_START = re.compile(r"^(\(\d+[A-Za-z]?\)|\([a-z]{1,3}\)|\([ivx]+\)|Provided|Explanation|\d{1,3}\[?\(|\*)")
HEADER_LINE = re.compile(r"^\((Part|Chapter|Schedule|Appendix|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth)[^)]*\)$", re.I)


REJECTED = []


def art_key(a):
    m = re.match(r"(\d+)([A-Z]*)", a)
    return int(m.group(1)), m.group(2)


def clean(text):
    text = re.sub(r"(?<![\w.])\d{1,3}\[", "", text)  # footnote markers like 1[
    text = re.sub(r"(?<=[\s,;:.—])\d{1,3}(?=\*\*\*)", "", text)
    text = text.replace("]", "").replace("[", "")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_page(page):
    """-> (body_lines, footnotes{num: text}) for one PDF page, using font size and position (footnotes are set smaller)."""
    lines = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            t = re.sub("[-]", "*", "".join(sp["text"] for sp in ln["spans"])).replace(" ", " ").strip()
            if t:
                lines.append((ln["bbox"][1], round(max(sp["size"] for sp in ln["spans"]), 1), t, ln["bbox"][0]))
    lines.sort(key=lambda x: x[0])
    rows, row_y = [], None  # lines on the same visual row (y within 4pt) are ordered left to right
    for ln_ in lines:
        if row_y is None or ln_[0] - row_y > 4:
            rows.append([ln_])
            row_y = ln_[0]
        else:
            rows[-1].append(ln_)
    lines = [(y, sz, t) for row in rows for (y, sz, t, _x) in sorted(row, key=lambda r: r[3])]
    if not lines:
        return [], {}
    count = {}
    for _, sz, t in lines:
        count[sz] = count.get(sz, 0) + len(t)
    body_size = max(count, key=count.get)
    body, foot = [], []
    for y, sz, t in lines:
        if y < 100 and (t == "THE CONSTITUTION OF INDIA" or HEADER_LINE.match(t) or re.fullmatch(r"\d{1,3}", t)):
            continue
        if t == "THE CONSTITUTION OF INDIA" or HEADER_LINE.match(t):
            continue
        if re.fullmatch(r"\d{1,3}", t) and (y < 100 or y > 700):
            continue
        if sz <= body_size - 0.8 and y > 400:
            foot.append(t)
        else:
            body.append(t)
    notes, cur = {}, None
    for l in foot:
        m = re.match(r"^(\d{1,3})\.\s+(.*)$", l)
        if m:
            cur = int(m.group(1))
            notes[cur] = m.group(2)
        elif cur is not None:
            notes[cur] += " " + l
    return body, notes


def _is_subheading(prev, line, nxt):
    """Short Title-case line between two Articles ("Right to Equality", "General") - not part of any Article."""
    if len(line) > 80 or line.startswith("(") or re.search(r"[.;:,—\-)\]]$", line) or not re.match(r"^[A-Z]", line):
        return False
    if nxt is None or not (ART_HEAD.match(nxt) or PART_HEAD.match(nxt) or re.match(r"^CHAPTER", nxt)):
        return False
    return prev is None or bool(re.search(r"[.;:\]\*]$", prev)) or len(line.split()) <= 8


def paragraphs(lines):
    paras, after_heading = [], False
    for i, l in enumerate(lines):
        prev = lines[i - 1] if i else None
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        upper = is_upper_heading(l) and not ART_HEAD.match(l)
        if _is_subheading(prev, l, nxt) and not upper:
            after_heading = True
            continue
        if (not paras or after_heading or upper or PARA_START.match(l) or ART_HEAD.match(l)
                or PART_HEAD.match(l) or re.match(r"^CHAPTER\s", l)):
            paras.append(l)
        else:
            paras[-1] += " " + l
        after_heading = upper
    return paras


def is_upper_heading(p):
    letters = re.sub(r"[^A-Za-z]", "", p)
    return len(letters) >= 3 and letters.isupper() and len(p) < 140


def chunk_text(text):
    paras = [p for p in text.split("\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > MAX_CHUNK:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks or [text.strip()]


def parse_articles(doc):
    """Return (preamble_text, preamble_notes, articles[list of dict])."""
    articles, preamble_lines, preamble_notes = [], [], []
    part, part_title = "", ""
    cur = None
    last_key = (0, "")
    pending_part = None
    for pno in range(ART_FIRST_PAGE, ART_LAST_PAGE + 1):
        body, notes = split_page(doc[pno - 1])
        paras = paragraphs(body)
        markers_used = set()
        for idx, p in enumerate(paras):
            m_part = PART_HEAD.match(p)
            if m_part:
                part, part_title, pending_part = "Part " + m_part.group(1), (m_part.group(2) or "").strip(), True
                continue
            if pending_part and is_upper_heading(p) and not ART_HEAD.match(p) and not p.startswith("CHAPTER"):
                part_title = clean((part_title + " " + p).strip())
                continue
            pending_part = None
            if re.match(r"^CHAPTER\s", p) or (is_upper_heading(p) and not ART_HEAD.match(p) and cur is not None and len(p) < 100):
                continue
            h = ART_HEAD.match(p)
            rest = p[h.end():] if h else ""
            if h and TITLE_END.search(rest[:420]):
                key = art_key(h.group(1))
                if not (key >= last_key and key[0] - last_key[0] <= 40 and key != last_key):
                    REJECTED.append((pno, h.group(1), last_key, p[:60]))
                if key >= last_key and key[0] - last_key[0] <= 40 and key != last_key:
                    cur = {"article": h.group(1), "title": "", "part": part, "part_title": part_title, "paras": [], "notes": [], "page": pno}
                    m_end = TITLE_END.search(rest)
                    cur["title"] = clean(rest[: m_end.start()])
                    first = rest[m_end.end():].strip()
                    cur["paras"].append(first)
                    articles.append(cur)
                    last_key = key
                    mk = set(int(x) for x in re.findall(r"(?<![\w.])(\d{1,3})\[", p[: h.end() + 4] + rest))
                    for n in sorted(mk):
                        if n in notes and (pno, n) not in markers_used:
                            cur["notes"].append(notes[n])
                            markers_used.add((pno, n))
                    continue
            # group sub-heading ("Right to Equality") directly before an article head
            nxt = paras[idx + 1] if idx + 1 < len(paras) else ""
            if cur is not None and len(p) < 90 and not re.search(r"[.;:,—\-)]$", p) and not p.startswith("(") and ART_HEAD.match(nxt):
                continue
            if cur is None:
                preamble_lines.append(p)
                for n in sorted(set(int(x) for x in re.findall(r"(?<![\w.])(\d{1,3})\[", p))):
                    if n in notes:
                        preamble_notes.append(notes[n])
                continue
            cur["paras"].append(p)
            for n in sorted(set(int(x) for x in re.findall(r"(?<![\w.])(\d{1,3})\[", p))):
                if n in notes and (pno, n) not in markers_used:
                    cur["notes"].append(notes[n])
                    markers_used.add((pno, n))
    return preamble_lines, preamble_notes, articles


def parse_schedules(doc):
    """Schedules + appendices -> list of {key, label, paras}."""
    secs, cur = [], None
    for pno in range(SCHED_FIRST_PAGE, len(doc) + 1):
        body, notes = split_page(doc[pno - 1])
        for l in body:
            m = re.match(r"^(?:THE\s+)?(" + "|".join(ORD) + r")\s+SCHEDULE$", l)
            a = re.match(r"^APPENDIX\s+([IV]+)$", l)
            if m:
                n = ORD.index(m.group(1)) + 1
                cur = {"key": f"SCH{n}", "label": f"{m.group(1).title()} Schedule", "paras": [], "notes": []}
                secs.append(cur)
                continue
            if a:
                cur = {"key": f"APP{ROMAN.get(a.group(1), a.group(1))}", "label": f"Appendix {a.group(1)}", "paras": [], "notes": []}
                secs.append(cur)
                continue
            if cur is not None:
                cur["paras"].append(l)
        if cur is not None:
            cur["notes"].extend(notes.values())
    for s in secs:
        s["text"] = clean("\n".join(paragraphs(s["paras"])))
    return secs


# ------------------------------------------------------------------------------------ Marathi
DEV = str.maketrans("०१२३४५६७८९", "0123456789")
MR_ART = re.compile(r"^(?:[०-९]{1,3}\s*)?\[?([०-९]{1,3})([क-ज्ञ]{0,2})\.\s+")


def parse_marathi(mr_dir):
    """-> {numeric_article: [text, ...]} in document order (Marathi pages concatenated, footnotes removed)."""
    files = sorted(f for f in os.listdir(mr_dir) if f.endswith(".txt"))
    paras = []
    for f in files:
        raw = open(os.path.join(mr_dir, f), encoding="utf-8").read()
        cut = re.search(r"^-{10,}\s*$|^[०-९]{1,3}\.\s+(?:संविधान|[“\"].*(?:मजकूर|ऐवजी)|.*अधिनियम)", raw, re.M)
        if cut:
            raw = raw[: cut.start()]
        for p in re.split(r"\n\s*\n", raw):
            p = " ".join(p.split())
            if p:
                paras.append(p)
    heads, cur = {}, None
    for p in paras:
        m = MR_ART.match(p)
        if m and "—" in p[:300]:
            num = int(m.group(1).translate(DEV))
            cur = {"num": num, "suffix_mr": m.group(2), "paras": [p]}
            heads.setdefault(num, []).append(cur)
        elif cur is not None:
            cur["paras"].append(p)
    return heads


def attach_marathi(articles, heads):
    mapped = 0
    by_num = {}
    for a in articles:
        n, suf = art_key(a["article"])
        by_num.setdefault(n, []).append(a)
    for n, arts in by_num.items():
        arts.sort(key=lambda a: art_key(a["article"]))
        mh = heads.get(n, [])
        if len(mh) == len(arts):
            for a, h in zip(arts, mh):
                a["text_mr"] = clean("\n".join(h["paras"]))
                mapped += 1
    return mapped


def build(en_pdf, mr_dir=None):
    doc = fitz.open(en_pdf)
    pre_lines, pre_notes, articles = parse_articles(doc)
    passages = []

    def add(chunk_id, article, title, part, part_title, text, kind, label, text_mr="", notes_for=""):
        passages.append({
            "chunk_id": chunk_id, "article": article, "article_title": title, "part": part, "part_title": part_title,
            "text": text, "text_mr": text_mr, "kind": kind, "label": label, "notes_for": notes_for,
        })

    pre = clean("\n".join(paragraphs(pre_lines)))
    if pre:
        add("PREAMBLE-0", "PREAMBLE", "Preamble", "Preamble", "", pre, "preamble", "Preamble")
        if pre_notes:
            add("PREAMBLE-N", "PREAMBLE", "Preamble", "Preamble", "", " ".join(clean(n) for n in pre_notes), "notes", "Preamble", notes_for="PREAMBLE")

    mr_mapped = 0
    if mr_dir and os.path.isdir(mr_dir):
        mr_mapped = attach_marathi(articles, parse_marathi(mr_dir))
    for a in articles:
        text = clean("\n".join(a["paras"]))
        if re.match(r"^Omitted", text):
            m_om = re.match(r"^(.*?(?:\)|\d{4})\.)(?:\s|$)", text)
            text = (m_om.group(1) if m_om else text).strip()
        if not text:
            text = "(Omitted)"
        label = f"Article {a['article']}"
        mr = a.get("text_mr", "")
        chunks = chunk_text(text)
        mr_chunks = chunk_text(mr) if mr else []
        for i, c in enumerate(chunks):
            add(f"A{a['article']}-{i}", a["article"], a["title"], a["part"], a["part_title"], c, "article", label,
                text_mr=(mr_chunks[i] if i < len(mr_chunks) and len(mr_chunks) == len(chunks) else (mr if len(chunks) == 1 else "")))
        if a["notes"]:
            note_txt = "Amendment notes: " + " ".join(f"({k}) {clean(n)}" for k, n in enumerate(a["notes"], 1))
            add(f"A{a['article']}-N", a["article"], a["title"], a["part"], a["part_title"], note_txt, "notes", label, notes_for=a["article"])
    for s in parse_schedules(doc):
        for i, c in enumerate(chunk_text(s["text"])):
            add(f"{s['key']}-{i}", s["key"], s["label"], "Schedules" if s["key"].startswith("SCH") else "Appendices", "", c,
                "schedule" if s["key"].startswith("SCH") else "appendix", s["label"])
        if s["notes"]:
            add(f"{s['key']}-N", s["key"], s["label"], "Schedules" if s["key"].startswith("SCH") else "Appendices", "",
                "Amendment notes: " + " ".join(clean(n) for n in s["notes"])[:3000], "notes", s["label"], notes_for=s["key"])
    return passages, len(articles), mr_mapped


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--en", required=True)
    ap.add_argument("--mr-dir", default=None)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    passages, n_art, n_mr = build(args.en, args.mr_dir)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False, indent=1)
    kinds = {}
    for p in passages:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    print(f"articles parsed: {n_art}; with Marathi text: {n_mr}; passages: {len(passages)}; by kind: {kinds}")
    print("written:", args.out)
