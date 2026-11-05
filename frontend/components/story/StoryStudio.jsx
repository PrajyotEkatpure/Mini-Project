"use client";
import React, { useCallback, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Background, CharacterFigure } from "./art";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
const SLOT_LEFT = { left: "4%", center: "32%", right: "60%" };
const QUICK_QUESTIONS = [
  "Why does this article matter?",
  "Can you explain that in simpler words?",
  "Can you give me another example?",
  "Which part of the Constitution supports your explanation?",
];

function SourceChip({ s }) {
  return (
    <span className="inline-block rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
      {s.label || `Article ${s.article}`} · {s.id}
    </span>
  );
}

function SourceList({ sources, only }) {
  const list = only ? sources.filter((s) => only.includes(s.id)) : sources;
  if (!list.length) return null;
  return (
    <ul className="mt-2 space-y-2">
      {list.map((s) => (
        <li key={s.id} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-gray-800">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <SourceChip s={s} />
            <span className="text-xs text-gray-600">{s.article_title} · {s.part}</span>
          </div>
          <p className="whitespace-pre-line leading-relaxed">{s.text}</p>
          <p className="mt-1 text-xs text-gray-500">{s.source}</p>
        </li>
      ))}
    </ul>
  );
}

function Stage({ story, scene, line, lineIdx }) {
  const chars = useMemo(() => Object.fromEntries(story.characters.map((c) => [c.id, c])), [story]);
  const speaker = line?.speaker;
  const speakerSlot = scene.staging.find((s) => s.character === speaker)?.position || "center";
  return (
    <div className="relative aspect-[16/10] w-full overflow-hidden rounded-xl border-4 border-amber-900/80 bg-amber-100 shadow-xl sm:aspect-video">
      <AnimatePresence mode="wait">
        <motion.div key={scene.id} className="absolute inset-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}>
          <Background id={scene.background} />
          {scene.staging.map((st) => {
            const c = chars[st.character];
            if (!c) return null;
            const isSpeaking = st.character === speaker;
            const l = isSpeaking ? line : [...scene.dialogue.slice(0, lineIdx + 1)].reverse().find((d) => d.speaker === st.character);
            return (
              <motion.div
                key={st.character}
                className="absolute bottom-0 h-[82%] w-[34%]"
                style={{ left: SLOT_LEFT[st.position] }}
                initial={{ y: 40, opacity: 0 }}
                animate={{ y: isSpeaking ? 0 : 10, opacity: 1, scale: isSpeaking ? 1.03 : 0.97, filter: isSpeaking ? "brightness(1)" : "brightness(.85)" }}
                transition={{ type: "spring", stiffness: 140, damping: 18 }}
              >
                <div className="flex h-full items-end justify-center">
                  <CharacterFigure character={c} emotion={l?.emotion || "neutral"} pose={isSpeaking ? l?.pose || "talking" : "standing"} speaking={isSpeaking} mirrored={st.position === "right"} />
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </AnimatePresence>
      {scene.is_hypothetical && (
        <span className="absolute left-3 top-3 rounded-full bg-indigo-900/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-white">
          Made-up example
        </span>
      )}
      <span className="absolute right-3 top-3 max-w-[55%] truncate rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-amber-900">{scene.title}</span>
      <AnimatePresence mode="wait">
        {line && (
          <motion.div
            key={`${scene.id}-${lineIdx}`}
            className="absolute inset-x-2 bottom-2 sm:inset-x-6 sm:bottom-4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            aria-live="polite"
          >
            <div className={`mx-auto max-w-3xl rounded-2xl border-2 border-amber-900 bg-white/95 p-3 shadow-lg sm:p-4 ${speakerSlot === "right" ? "sm:ml-auto sm:mr-0" : ""}`}>
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-amber-800">
                {chars[speaker]?.name} <span className="font-normal normal-case text-gray-500">· {chars[speaker]?.role}</span>
              </p>
              <p className="text-sm leading-relaxed text-gray-900 sm:text-base">{line.text}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Quiz({ quiz, sources }) {
  const [answers, setAnswers] = useState({});
  const done = Object.keys(answers).length === quiz.length;
  const score = quiz.filter((q, i) => answers[i] === q.answer_index).length;
  return (
    <div className="space-y-5">
      {quiz.map((q, i) => {
        const picked = answers[i];
        return (
          <fieldset key={i} className="rounded-lg border border-gray-200 bg-white p-4">
            <legend className="px-1 text-sm font-semibold text-gray-900">{i + 1}. {q.question}</legend>
            <div className="mt-2 grid gap-2">
              {q.options.map((o, j) => {
                const state = picked == null ? "" : j === q.answer_index ? "border-green-600 bg-green-50" : j === picked ? "border-red-500 bg-red-50" : "opacity-60";
                return (
                  <button key={j} disabled={picked != null} onClick={() => setAnswers((a) => ({ ...a, [i]: j }))} className={`rounded-lg border-2 px-3 py-2 text-left text-sm text-gray-900 hover:bg-amber-50 disabled:cursor-default ${state || "border-gray-300"}`}>
                    {o}
                  </button>
                );
              })}
            </div>
            {picked != null && (
              <div className="mt-3 text-sm text-gray-800">
                <p><strong>{picked === q.answer_index ? "Correct." : "Not quite."}</strong> {q.explanation}</p>
                <div className="mt-1 flex flex-wrap gap-1">{sources.filter((s) => q.source_ids.includes(s.id)).map((s) => <SourceChip key={s.id} s={s} />)}</div>
              </div>
            )}
          </fieldset>
        );
      })}
      {done && <p className="rounded-lg bg-amber-100 p-3 text-center font-semibold text-amber-900">You scored {score} out of {quiz.length}.</p>}
    </div>
  );
}

export default function StoryStudio({ data, article, audience, language = "en", onClose, onRegenerate }) {
  const { story, sources, validation } = data;
  const scenesById = useMemo(() => Object.fromEntries(story.scenes.map((s) => [s.id, s])), [story]);
  const chars = useMemo(() => Object.fromEntries(story.characters.map((c) => [c.id, c])), [story]);
  const [path, setPath] = useState([story.start_scene_id]);
  const [lineIdx, setLineIdx] = useState(0);
  const [picked, setPicked] = useState(null);
  const [phase, setPhase] = useState("story");
  const [showLearn, setShowLearn] = useState(true);
  const [talkTo, setTalkTo] = useState(story.characters[0].id);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [chat, setChat] = useState([]);

  const scene = scenesById[path[path.length - 1]];
  const line = scene.dialogue[lineIdx];
  const atEnd = lineIdx >= scene.dialogue.length - 1;
  const hasChoices = scene.choices.length > 0;

  const go = useCallback((sceneId) => {
    setPath((p) => [...p, sceneId]);
    setLineIdx(0);
    setPicked(null);
  }, []);

  const next = () => {
    if (!atEnd) return setLineIdx(lineIdx + 1);
    if (picked) return go(picked.next_scene_id);
    if (hasChoices) return;
    if (scene.next_scene_id) return go(scene.next_scene_id);
    setPhase("summary");
  };
  const prev = () => {
    if (lineIdx > 0) return setLineIdx(lineIdx - 1);
    if (path.length > 1) {
      setPath(path.slice(0, -1));
      setLineIdx(scenesById[path[path.length - 2]].dialogue.length - 1);
      setPicked(null);
    }
  };
  const jump = (id) => {
    const i = path.indexOf(id);
    if (i >= 0) {
      setPath(path.slice(0, i + 1));
      setLineIdx(0);
      setPicked(null);
      setPhase("story");
    }
  };

  const ask = async (q) => {
    const text = (q ?? question).trim();
    if (!text || asking) return;
    const c = chars[talkTo];
    setChat((h) => [...h, { role: "user", text }]);
    setQuestion("");
    setAsking(true);
    try {
      const res = await fetch(`${API}/api/story/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          article, audience, language, question: text, character: { name: c.name, role: c.role }, scene_summary: scene.summary,
          history: chat.slice(-6).map((m) => ({ role: m.role, text: m.text })),
        }),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.error || "Request failed");
      setChat((h) => [...h, { role: "character", who: c, text: j.answer, supported: j.supported, sources: j.sources }]);
    } catch (e) {
      setChat((h) => [...h, { role: "character", who: c, text: `I couldn't answer that right now (${e.message}). Please try again.`, supported: false, sources: [] }]);
    } finally {
      setAsking(false);
    }
  };

  const sceneSources = sources.filter((s) => scene.claims.some((c) => c.source_ids.includes(s.id)));

  return (
    <div className="fixed inset-0 z-[60] overflow-y-auto bg-stone-900/90 p-2 sm:p-6" role="dialog" aria-modal="true" aria-label={`Story: ${story.title}`}>
      <div className="mx-auto max-w-6xl rounded-2xl bg-amber-50 p-3 shadow-2xl sm:p-5">
        <header className="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-amber-800">Article {story.article} · {story.audience} · {story.style}</p>
            <h2 className="text-xl font-bold text-gray-900 sm:text-2xl">{story.title}</h2>
            <p className="text-sm text-gray-700">{story.synopsis}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={onRegenerate} className="rounded-lg border border-amber-700 px-3 py-1.5 text-sm font-medium text-amber-900 hover:bg-amber-100">New story</button>
            <button onClick={onClose} className="rounded-lg bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700" aria-label="Close story">Close</button>
          </div>
        </header>

        {phase === "story" ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
            <div>
              <Stage story={story} scene={scene} line={line} lineIdx={lineIdx} />

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button onClick={prev} disabled={path.length === 1 && lineIdx === 0} className="rounded-lg border border-gray-400 px-3 py-2 text-sm font-medium text-gray-900 hover:bg-white disabled:opacity-40">Back</button>
                {!(atEnd && hasChoices && !picked) && (
                  <button onClick={next} className="rounded-lg bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800">
                    {!atEnd ? "Next line" : picked || scene.next_scene_id ? "Next scene" : "Finish story"}
                  </button>
                )}
                <span className="ml-auto text-xs text-gray-600">Scene {path.length} · line {lineIdx + 1}/{scene.dialogue.length}</span>
              </div>

              {atEnd && hasChoices && (
                <div className="mt-3 rounded-xl border-2 border-indigo-300 bg-indigo-50 p-3">
                  <p className="mb-2 text-sm font-semibold text-indigo-900">What should happen next?</p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {scene.choices.map((c) => (
                      <button key={c.id} onClick={() => setPicked(c)} disabled={!!picked} className={`rounded-lg border-2 bg-white px-3 py-2 text-left text-sm text-gray-900 hover:bg-indigo-100 ${picked?.id === c.id ? "border-indigo-600" : "border-indigo-200"} disabled:cursor-default`}>
                        {c.text}
                      </button>
                    ))}
                  </div>
                  {picked && (
                    <div className="mt-3 text-sm text-gray-900">
                      <p>{picked.feedback}</p>
                      {picked.is_hypothetical && <p className="mt-1 text-xs text-indigo-800">This is a made-up situation, not a legal conclusion.</p>}
                      <button onClick={next} className="mt-2 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-800">Continue</button>
                    </div>
                  )}
                </div>
              )}

              <nav aria-label="Storyboard timeline" className="mt-4 flex gap-2 overflow-x-auto pb-1">
                {path.map((id, i) => (
                  <button key={`${id}-${i}`} onClick={() => jump(id)} className={`shrink-0 rounded-lg border-2 px-3 py-1.5 text-left text-xs ${i === path.length - 1 ? "border-amber-700 bg-amber-200 font-bold" : "border-amber-300 bg-white"} text-gray-900`}>
                    <span className="block text-[10px] uppercase text-gray-500">Scene {i + 1}</span>
                    {scenesById[id].title}
                  </button>
                ))}
              </nav>
            </div>

            <aside className="space-y-3">
              <section className="rounded-xl border border-amber-300 bg-white">
                <button onClick={() => setShowLearn(!showLearn)} aria-expanded={showLearn} className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-bold text-gray-900">
                  Constitutional learning panel <span aria-hidden>{showLearn ? "−" : "+"}</span>
                </button>
                {showLearn && (
                  <div className="space-y-3 border-t border-amber-200 px-4 py-3 text-sm text-gray-800">
                    <p><strong>Goal:</strong> {scene.learning_objective}</p>
                    {scene.claims.length > 0 ? (
                      <div>
                        <p className="font-semibold">What the Constitution provides <span className="ml-1 rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-bold text-green-800">VERIFIED AGAINST SOURCE</span></p>
                        <ul className="mt-1 list-disc space-y-1 pl-5">
                          {scene.claims.map((c) => (
                            <li key={c.id}>{c.text} <span className="whitespace-nowrap">{sources.filter((s) => c.source_ids.includes(s.id)).map((s) => <SourceChip key={s.id} s={s} />)}</span></li>
                          ))}
                        </ul>
                        <SourceList sources={sceneSources} />
                      </div>
                    ) : (
                      <p className="text-gray-600">This scene sets up the situation; no constitutional claim is made here.</p>
                    )}
                    <p><strong>Takeaway:</strong> {scene.summary}</p>
                  </div>
                )}
              </section>

              <section className="rounded-xl border border-amber-300 bg-white p-4">
                <h3 className="text-sm font-bold text-gray-900">Ask a character</h3>
                <div className="mt-2 flex flex-wrap gap-1">
                  {story.characters.map((c) => (
                    <button key={c.id} onClick={() => setTalkTo(c.id)} aria-pressed={talkTo === c.id} className={`rounded-full border px-3 py-1 text-xs ${talkTo === c.id ? "border-amber-700 bg-amber-200 font-bold" : "border-gray-300"} text-gray-900`}>{c.name}</button>
                  ))}
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {QUICK_QUESTIONS.map((q) => (
                    <button key={q} onClick={() => ask(q)} disabled={asking} className="rounded-full bg-amber-100 px-2.5 py-1 text-xs text-amber-900 hover:bg-amber-200 disabled:opacity-50">{q}</button>
                  ))}
                </div>
                <form onSubmit={(e) => { e.preventDefault(); ask(); }} className="mt-2 flex gap-2">
                  <input value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={500} placeholder={`Ask ${chars[talkTo].name}…`} className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900" aria-label="Your question" />
                  <button disabled={asking || !question.trim()} className="rounded-lg bg-amber-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">Ask</button>
                </form>
                <div className="mt-3 max-h-72 space-y-2 overflow-y-auto" aria-live="polite">
                  {chat.map((m, i) =>
                    m.role === "user" ? (
                      <p key={i} className="ml-auto w-fit max-w-[90%] rounded-xl bg-gray-100 px-3 py-2 text-sm text-gray-900">{m.text}</p>
                    ) : (
                      <div key={i} className="max-w-[95%] rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-gray-900">
                        <p className="text-xs font-bold text-amber-800">{m.who.name}</p>
                        <p>{m.text}</p>
                        {!m.supported && <p className="mt-1 text-xs italic text-gray-600">Not established by the available source text.</p>}
                        <SourceList sources={m.sources || []} />
                      </div>
                    )
                  )}
                  {asking && <p className="text-xs text-gray-600">{chars[talkTo].name} is thinking…</p>}
                </div>
              </section>
            </aside>
          </div>
        ) : (
          <div className="space-y-5">
            <section className="rounded-xl border border-amber-300 bg-white p-4 sm:p-6">
              <h3 className="text-lg font-bold text-gray-900">What you learned about Article {story.article}</h3>
              <p className="mt-2 text-gray-800">{story.final_summary}</p>
              <div className="mt-3 flex flex-wrap gap-2">{story.key_concepts.map((k) => <span key={k} className="rounded-full bg-amber-200 px-3 py-1 text-sm text-amber-900">{k}</span>)}</div>
              <h4 className="mt-4 text-sm font-bold text-gray-900">Verified source text</h4>
              <SourceList sources={sources.filter((s) => s.cited)} />
              <p className="mt-3 text-xs text-gray-600">
                {validation.claims_verified} claims checked against the retrieved text; {validation.claims_removed} unsupported claim(s) removed before display. Characters and events are fictional.
              </p>
            </section>
            <section>
              <h3 className="mb-2 text-lg font-bold text-gray-900">Check your understanding</h3>
              <Quiz quiz={story.quiz} sources={sources} />
            </section>
            <div className="flex gap-2">
              <button onClick={() => jump(path[0])} className="rounded-lg border border-amber-700 px-4 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100">Replay story</button>
              <button onClick={onClose} className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white">Done</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
