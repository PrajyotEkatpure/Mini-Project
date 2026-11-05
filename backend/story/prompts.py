AUDIENCE_GUIDE = {
    "kid": "Ages 7-11. Very short sentences, everyday words, familiar settings (school, playground, home). Warm and playful. Avoid legal terms unless a character explains them in one simple sentence.",
    "student": "Ages 12-18. Clear, conversational language. Introduce terms like 'State', 'citizen', 'Parliament' with brief explanations. Use school, college, and community situations.",
    "adult": "Adults. Natural, grown-up dialogue with real-world situations (workplace, neighbourhood, civic life). Precise vocabulary, but never long legal recitations.",
}

STYLE_GUIDE = {
    "mystery": "A small mystery: characters piece together clues and discover how the article applies.",
    "adventure": "An adventure/journey in which the characters meet the article's idea along the way.",
    "everyday": "A slice-of-life situation in an ordinary Indian family, school, or neighbourhood.",
    "courtroom": "A fictional moot-court / classroom courtroom simulation. It is a make-believe exercise, never a real case or a real judgment.",
}

LANGUAGE_GUIDE = {
    "en": "Write all story text in warm, natural, spoken English.",
    "mr": (
        "Write ALL story text (title, synopsis, scene titles/descriptions, dialogue, choices, feedback, summaries, key_concepts, "
        "final_summary, quiz questions/options/explanations) in Marathi (Devanagari). "
        "Use everyday spoken Marathi the way real Maharashtrian families, friends and neighbours talk (बोलीभाषा), NOT stiff, "
        "bookish or Sanskritised textbook Marathi and NOT a word-for-word translation of English. "
        "Use natural expressions and small touches like अरे, अगं, बाबा, ताई, दादा, अहो, खरंच?, बापरे!, हो ना. "
        "Set the story in a Maharashtrian setting (gaav, shala, bazaar, ST stand, ward office) with Marathi names. "
        "Keep the English words people actually use (Court, Police, Parliament, Article) where natural. "
        "Exception: the 'claims[].text' and 'claims[].quote' fields MUST stay in English, because they are checked word-by-word "
        "against the English source passages. Keep passage ids and JSON keys unchanged."
    ),
}

DEPTH_GUIDE = (
    "The learner must finish the story genuinely understanding the WHOLE article, not just its headline. "
    "Step 1: read the selected SOURCE PASSAGE and list for yourself every distinct provision in it (each right / clause / sub-clause / "
    "condition / exception / restriction / who it applies to). The story MUST cover every one of them, in plain words, each tied to a "
    "concrete everyday example (a real-feeling situation a citizen could face), and must also show the LIMITS and exceptions the text states "
    "(for example 'reasonable restrictions'), never only the positive side. Do not stop at one or two points. "
    "Structure: (1) a realistic problem with real stakes that exists because of this article; (2) a knowledgeable, patient character explains "
    "what the article says part by part, and each part is immediately shown in a small example; (3) a scene where a limit/exception/other "
    "side appears and the characters work out the balance; (4) resolution where the problem is solved by applying the article, with a clear "
    "emotional payoff; (5) a closing scene where a character summarises, in the learner's own simple words, everything the article gives. "
    "Each scene must have 5-8 dialogue lines with substance - questions, doubts, examples, answers - not one-line exchanges. "
    "Write at least one verified claim for EACH distinct provision of the article (4-8 claims across the story), each worded close to the passage. "
    "Realistic means: believable people, places, numbers of people, official offices and everyday consequences - but no invented laws, cases or penalties."
)

EMOTION_GUIDE = (
    "Make the story FEEL alive. Give the main character a real emotional arc (worry/confusion/unfairness -> understanding -> relief/pride/determination). "
    "Characters must express feelings in their own words (nervous, hurt, excited, proud, angry-but-calm), not only through the emotion tag; "
    "vary the 'emotion' tags to match. Use small human details (a shaking voice, a smile, a pause). "
    "The Article's idea must be the turning point of the plot: the problem in the story exists BECAUSE of the concept, and is resolved by understanding it, "
    "so a reader who follows the story can state the concept clearly afterwards. One character explains the idea in simple words, then the story shows it at work. "
    "Never lecture; no long speeches."
)

BACKGROUNDS = "village_square, school_classroom, courtroom, city_street, home_interior, market, parliament, office, railway_station, library"

STORY_SYSTEM = """You write interactive educational stories about the Constitution of India as strict JSON.

GROUNDING RULES (non-negotiable):
- Every statement about what the Constitution says or provides MUST be supported by the SOURCE PASSAGES provided. Cite them only by their exact passage ids.
- You may invent fictional characters, places, dialogue and hypothetical events. You must NOT invent or mention: court cases, judgments, statutes/Acts/sections, penalties, amendments, dates of laws, or articles that are not in the SOURCE PASSAGES.
- Do not claim a fictional situation is a legal violation or a court outcome. Fictional situations are hypothetical examples; say 'in this made-up situation' rather than giving a legal verdict.
- Preserve qualifications in the text ('except', 'subject to', 'provided that'). Do not overstate (no 'absolute', 'always', 'never') unless the text says so.
- If you put words in quotation marks and attribute them to the Constitution, they must be copied verbatim from a passage. Prefer paraphrase over quotation.
- Do not make characters recite long legal text. One character asks, another explains in plain words, the first asks a follow-up.

OUTPUT: a single JSON object, no markdown, matching exactly this shape (no extra keys):
{
 "title": str, "article": str (the article number as given), "audience": "kid|student|adult", "style": "mystery|adventure|everyday|courtroom",
 "synopsis": str,
 "characters": [ {"id": lowercase_id, "name": str (Indian name), "role": str, "skin": "light|wheat|brown|deep", "hair": "black|brown|grey|white", "outfit": "saffron|green|blue|maroon|teal|mustard|navy|plum", "accessory": "none|glasses|turban|dupatta|cap|robe"} ],  // 2-4 characters
 "start_scene_id": str,
 "scenes": [ {
    "id": lowercase_id, "title": str, "description": str,
    "background": one of [__BACKGROUNDS__], "background_prompt": str (short illustration description),
    "staging": [ {"character": character id, "position": "left|center|right"} ],
    "dialogue": [ {"speaker": character id, "text": str, "emotion": "neutral|happy|curious|worried|surprised|thoughtful|determined", "pose": "standing|talking|pointing|thinking|reading"} ],  // 5-8 lines per scene; every speaker must be staged
    "learning_objective": str,
    "claims": [ {"id": "c1", "text": str (a plain, precise statement of what the Constitution provides, worded close to the passage), "source_ids": [passage ids], "quote": optional verbatim excerpt} ],
    "choices": [ {"id": lowercase_id, "text": str, "next_scene_id": scene id, "feedback": str, "is_hypothetical": true} ],  // 0 or 2-3 choices
    "next_scene_id": scene id or null,  // use EITHER choices OR next_scene_id; both empty on ending scenes
    "summary": str (what the learner should take from this scene), "is_hypothetical": true
 } ],  // 5-7 scenes, at least one scene with choices, branches must rejoin or end; at least one ending scene
 "key_concepts": [str],
 "final_summary": str,
 "quiz": [ {"question": str, "options": [str, ...2-4], "answer_index": int, "explanation": str, "source_ids": [passage ids]} ]  // 4 questions that test understanding of different parts of the article
}
Claim ids must be unique per scene (c1, c2...). Include at least one claim in scenes that explain the article, and cite the selected article's passage in at least two claims.""".replace("__BACKGROUNDS__", BACKGROUNDS)


def format_passages(primary, related):
    def block(p, tag):
        return f"[{p.chunk_id}] ({tag}) {p.display_label} - {p.article_title} | {p.part} | source: {p.source}\n{p.text}"

    out = ["SOURCE PASSAGES (selected article):"] + [block(p, "selected") for p in primary]
    if related:
        out.append("\nSOURCE PASSAGES (related, optional):")
        out += [block(p, "related") for p in related]
    return "\n\n".join(out)


def story_prompt(article, title, audience, style, objective, primary, related, feedback=None, language="en"):
    p = (
        f"Create a story that helps a learner understand Article {article} ({title}).\n"
        f"Audience: {audience}. {AUDIENCE_GUIDE[audience]}\n"
        f"Style: {style}. {STYLE_GUIDE[style]}\n"
        f"Learning objective: {objective}\n"
        f"Language: {LANGUAGE_GUIDE[language]}\n"
        f"Storytelling: {EMOTION_GUIDE}\n"
        f"Depth and coverage: {DEPTH_GUIDE}\n"
        f"Use Indian names and settings. The \"article\" field must be \"{article}\".\n\n"
        f"{format_passages(primary, related)}\n"
    )
    if feedback:
        p += (
            "\nYOUR PREVIOUS ATTEMPT WAS REJECTED BY THE VALIDATOR FOR THESE REASONS. Fix all of them, "
            "keep the story otherwise similar, and do not introduce anything not in the source passages:\n- "
            + "\n- ".join(feedback[:12])
        )
    return p


FOLLOWUP_SYSTEM = """You are a character in an educational story about the Constitution of India, answering a learner's question in character.

RULES:
- Answer ONLY from the SOURCE PASSAGES. Cite passage ids in claims. Do not invent cases, statutes, penalties, amendments or articles.
- If the passages do not establish the answer, set "supported": false, and say in character that the available source material does not establish the answer. Do not guess.
- Match the audience's vocabulary. Keep the answer short (2-5 sentences). Fictional examples must be clearly hypothetical, never a legal verdict.
- Earlier story dialogue is NOT a source; only the passages are.
OUTPUT JSON only: {"answer": str, "supported": bool, "emotion": "neutral|happy|curious|worried|surprised|thoughtful|determined", "claims": [ {"id": "c1", "text": str (precise statement worded close to the passage), "source_ids": [ids], "quote": optional verbatim excerpt} ]}"""


def followup_prompt(article, title, audience, character, scene_summary, history, question, primary, related, feedback=None, language="en"):
    hist = "\n".join(f"{h.get('role', 'user')}: {str(h.get('text', ''))[:300]}" for h in (history or [])[-6:])
    p = (
        f"Story article: Article {article} ({title}). Audience: {audience}. {AUDIENCE_GUIDE[audience]}\n"
        f"You are {character['name']}, {character['role']}.\n"
        + ("Reply in natural, warm spoken Marathi (Devanagari), the way a real person talks, with feeling - not stiff textbook Marathi. 'claims[].text' and 'claims[].quote' stay in English.\n" if language == "mr" else "") +
        f"Current scene (context only, not a source): {scene_summary}\n"
        f"Conversation so far:\n{hist or '(none)'}\n\n"
        f"{format_passages(primary, related)}\n\nLearner's question: {question}\n"
    )
    if feedback:
        p += f"\nYour previous answer was rejected: {feedback}. Answer again using only the passages, or set supported=false."
    return p
