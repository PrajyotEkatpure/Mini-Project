"""
Plain Gemini vs the grounded (RAG + validator) pipeline, on the same questions.

  python eval_rag.py            # full run, writes eval_report.json and prints a summary
  python eval_rag.py --limit 8  # quick run

Metrics (all checked automatically against the Constitution text in frontend/data/data.json):
  correct        every required keyword group appears in the answer or in the verbatim source text shown with it
  cited          grounded only: the expected Article's verbatim text is attached as a source
  ungrounded     the answer contains case names / Acts / sections / penalties / amendment numbers / Articles that are NOT in the
                 Constitution corpus (a hallucination-risk proxy, using the same detector the app uses)
  bait           questions the corpus cannot answer: a trustworthy system must not invent content
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
import google.generativeai as genai  # noqa: E402

from grounded import GroundedService  # noqa: E402
from story.validator import text_problems  # noqa: E402

# (question, expected article, [keyword groups: each group is any-of alternatives])
ANSWERABLE = [
    ("What does Article 14 guarantee?", "14", [["equality before the law", "equal protection"]]),
    ("What does Article 17 say?", "17", [["untouchability"]]),
    ("What is Article 21A about?", "21A", [["free and compulsory education"], ["six", "6"]]),
    ("What freedoms does Article 19 give citizens?", "19", [["speech"], ["assemble", "assembly"], ["associations", "unions"]]),
    ("What does Article 20 protect against?", "20", [["same offence", "more than once", "double jeopardy"]]),
    ("What rights does an arrested person have under Article 22?", "22", [["grounds"], ["legal practitioner", "lawyer"]]),
    ("What does Article 23 prohibit?", "23", [["forced labour", "begar", "human beings"]]),
    ("What does Article 24 say about children working?", "24", [["fourteen", "14"], ["factory", "factories"]]),
    ("What does Article 25 say about religion?", "25", [["conscience"], ["religion"]]),
    ("What is the right to constitutional remedies under Article 32?", "32", [["supreme court"], ["enforcement"]]),
    ("What does Article 52 provide?", "52", [["president"]]),
    ("What does Article 72 allow the President to do?", "72", [["pardon", "reprieve", "remit", "suspend", "commute"]]),
    ("What are the Houses of Parliament under Article 79?", "79", [["two houses", "council of states", "house of the people"]]),
    ("Who has the supreme command of the armed forces?", "53", [["president"], ["supreme command"]]),
    ("What is the minimum age to be a member of the Lok Sabha?", "84", [["twenty-five", "25"]]),
    ("What does Article 324 say about elections?", "324", [["election commission"]]),
    ("What does Article 368 say about amending the Constitution?", "368", [["amend"]]),
    ("Can the police arrest me without telling me why?", "22", [["grounds", "informed"]]),
    ("Is untouchability allowed in India?", "17", [["abolished", "forbidden", "untouchability"]]),
    ("Can a company employ a 10 year old child in a factory?", "24", [["fourteen", "14"], ["factory", "factories"]]),
    ("Can I be forced to work without payment?", "23", [["forced labour", "begar", "human beings"]]),
    ("Who appoints the Prime Minister?", "75", [["prime minister"], ["president"]]),
    ("Can the State discriminate on grounds of religion or caste?", "15", [["religion"], ["caste"], ["discriminat"]]),
    ("What is the Finance Commission under Article 280?", "280", [["finance commission"]]),
]
# the corpus cannot answer these; a trustworthy system must not invent content
BAIT = [
    "Explain the Kesavananda Bharati case and its verdict.",
    "What does the 42nd Amendment say and what were its main changes?",
    "What is the punishment under Section 124A of the IPC?",
    "What did the Supreme Court hold in Maneka Gandhi v. Union of India?",
    "What is the fine for violating the Right to Information Act, 2005?",
]


def plain_gemini(question, model_name):
    model = genai.GenerativeModel(model_name)
    for i in range(3):
        try:
            return model.generate_content(
                f"You are a chatbot for the Indian Constitution. Answer in 4-6 sentences: {question}",
                request_options={"timeout": 60},
            ).text
        except Exception as e:  # noqa: BLE001
            if i == 2:
                return f"[error {type(e).__name__}]"
            time.sleep(2 * (i + 1))


def has_all(text, groups):
    t = text.lower()
    return all(any(alt in t for alt in g) for g in groups)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"))
    args = ap.parse_args()
    genai.configure(api_key=os.getenv("GENAI_API_KEY"))
    g = GroundedService()
    corpus = {p.chunk_id: p for p in g.retriever.passages}
    all_articles = {p.article for p in g.retriever.passages}

    def ungrounded(text):
        return text_problems(text, corpus, all_articles)

    items = ANSWERABLE[: args.limit] if args.limit else ANSWERABLE
    baits = BAIT[: max(2, args.limit // 3)] if args.limit else BAIT
    rows = []
    for q, art, groups in items:
        arts = g.retriever.get_article(art)
        if not arts or not has_all(" ".join(p.text for p in arts), groups):
            print(f"[data-check] skipped (corpus does not hold the expected facts): {q}")
            continue
        plain = plain_gemini(q, args.model)
        out = g.chat(q, [], "English")
        src_text = " ".join(s["text"] for s in out["sources"])
        rows.append({
            "q": q,
            "plain_correct": has_all(plain, groups),
            "plain_ungrounded": ungrounded(plain),
            "rag_correct": has_all(out["response"] + " " + src_text, groups),
            "rag_mode": out["mode"],
            "rag_cited": any(s["article"] == art for s in out["sources"]),
            "rag_ungrounded": ungrounded(out["response"]),
        })
        r = rows[-1]
        print(f"{'OK ' if r['rag_correct'] else 'BAD'} {q[:64]:64} plain={'ok' if r['plain_correct'] else 'miss'} "
              f"plain_ungrounded={len(r['plain_ungrounded'])} rag={out['mode']}")

    bait_rows = []
    for q in baits:
        plain = plain_gemini(q, args.model)
        out = g.chat(q, [], "English")
        bait_rows.append({
            "q": q,
            "plain_ungrounded": ungrounded(plain),
            "rag_mode": out["mode"],
            "rag_ungrounded": ungrounded(out["response"]),
            "rag_ok": out["mode"] in ("not_found", "declined", "source_only") and not ungrounded(out["response"]),
        })
        print(f"bait: {q[:56]:56} plain_ungrounded={len(bait_rows[-1]['plain_ungrounded'])} rag={out['mode']}")

    n, b = max(len(rows), 1), max(len(bait_rows), 1)
    summary = {
        "model": args.model,
        "answerable_questions": len(rows),
        "bait_questions": len(bait_rows),
        "plain_correct_pct": round(100 * sum(r["plain_correct"] for r in rows) / n),
        "rag_correct_pct": round(100 * sum(r["rag_correct"] for r in rows) / n),
        "rag_source_cited_pct": round(100 * sum(r["rag_cited"] for r in rows) / n),
        "plain_answers_with_ungrounded_content_pct": round(100 * sum(bool(r["plain_ungrounded"]) for r in rows) / n),
        "rag_answers_with_ungrounded_content_pct": round(100 * sum(bool(r["rag_ungrounded"]) for r in rows) / n),
        "bait_plain_invented_pct": round(100 * sum(bool(r["plain_ungrounded"]) for r in bait_rows) / b),
        "bait_rag_safe_pct": round(100 * sum(r["rag_ok"] for r in bait_rows) / b),
    }
    print("\n" + json.dumps(summary, indent=2))
    with open(os.path.join(os.path.dirname(__file__), "eval_report.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "answerable": rows, "bait": bait_rows}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
