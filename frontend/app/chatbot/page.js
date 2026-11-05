"use client";

import React, { useState, useRef, useEffect } from 'react';
import { RiRobot2Line } from 'react-icons/ri';
import { FaUser, FaPaperPlane, FaMicrophone, FaStop, FaImage, FaTimes } from 'react-icons/fa';
import NavBar from '@/components/NavBar';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const LANGUAGES = [
  { value: 'English', label: 'English' },
  { value: 'Hindi', label: 'हिन्दी (Hindi)' },
  { value: 'Marathi', label: 'मराठी (Marathi)' },
  { value: 'Tamil', label: 'தமிழ் (Tamil)' },
  { value: 'Telugu', label: 'తెలుగు (Telugu)' },
  { value: 'Kannada', label: 'ಕನ್ನಡ (Kannada)' },
  { value: 'Malayalam', label: 'മലയാളം (Malayalam)' },
  { value: 'Bengali', label: 'বাংলা (Bengali)' },
  { value: 'Gujarati', label: 'ગુજરાતી (Gujarati)' },
  { value: 'Punjabi', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { value: 'Odia', label: 'ଓଡ଼ିଆ (Odia)' },
  { value: 'Urdu', label: 'اردو (Urdu)' },
  { value: 'Assamese', label: 'অসমীয়া (Assamese)' },
];

const SPEECH_LANGS = [
  { value: 'en-IN', label: 'Speak: English' },
  { value: 'mr-IN', label: 'बोला: मराठी' },
];
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

const readAsDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });

const formatTime = (ts) =>
  new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });

export default function Page() {
  const [language, setLanguage] = useState('English');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const endOfChatRef = useRef(null);
  const recogRef = useRef(null);
  const fileRef = useRef(null);
  const [speechLang, setSpeechLang] = useState('en-IN');
  const [listening, setListening] = useState(false);
  const [notice, setNotice] = useState('');
  const [image, setImage] = useState(null); // { mime, data, preview }

  const toggleMic = () => {
    setNotice('');
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (!SR) {
      setNotice('Voice input is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }
    const rec = new SR();
    rec.lang = speechLang;
    rec.interimResults = true;
    rec.continuous = false;
    const base = message ? message.trim() + ' ' : '';
    rec.onresult = (ev) => {
      let t = '';
      for (let i = 0; i < ev.results.length; i++) t += ev.results[i][0].transcript;
      setMessage(base + t);
    };
    rec.onerror = (ev) => {
      const map = {
        'not-allowed': 'Microphone permission was denied. Allow the microphone in the browser address bar and try again.',
        'service-not-allowed': 'Microphone permission was denied. Allow the microphone and try again.',
        'no-speech': 'No speech was heard. Please try again.',
        network: 'Voice recognition needs an internet connection.',
        'audio-capture': 'No microphone was found.',
      };
      setNotice(map[ev.error] || `Voice input failed (${ev.error}).`);
    };
    rec.onend = () => setListening(false);
    recogRef.current = rec;
    try {
      rec.start();
      setListening(true);
    } catch {
      setListening(false);
    }
  };

  const pickImage = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setNotice('');
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      setNotice('Please choose a PNG, JPG or WebP image.');
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setNotice('The image is larger than 5 MB. Please choose a smaller one.');
      return;
    }
    const url = await readAsDataUrl(file);
    setImage({ mime: file.type, data: url.split(',')[1], preview: url });
  };

  useEffect(() => () => recogRef.current?.abort?.(), []);

  const handleSubmit = async (e, override) => {
    e?.preventDefault?.();
    const text = (typeof override === 'string' ? override : message).trim();
    if ((!text && !image) || loading) return;
    if (listening) recogRef.current?.stop();
    const sentImage = image;

    const history = chatHistory
      .filter((m) => m.role === 'user' || (m.role === 'bot' && !m.error))
      .map(({ role, content }) => ({ role, content }));

    setChatHistory((prev) => [...prev, { role: 'user', content: text || '(image)', image: sentImage?.preview, ts: Date.now() }]);
    setMessage('');
    setImage(null);
    setNotice('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/get_response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, feedback: 'Message from the user', language, history, ...(sentImage ? { image: { mime: sentImage.mime, data: sentImage.data } } : {}) }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.response) {
        throw new Error(data.error || 'The chatbot could not answer right now.');
      }
      setChatHistory((prev) => [...prev, { role: 'bot', content: data.response, sources: data.sources || [], mode: data.mode, verified: data.verified, ts: Date.now() }]);
    } catch (error) {
      console.error('Error:', error);
      const offline = error instanceof TypeError;
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'bot',
          error: true,
          ts: Date.now(),
          content: offline
            ? 'Cannot reach the server. Please make sure the backend is running on port 5000.'
            : error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    endOfChatRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, loading]);

  return (
    <div className="h-[100dvh] flex flex-col overflow-hidden bg-gradient-to-br from-orange-50 to-blue-50">
      <NavBar />
      
      {/* Header */}
      <div className="bg-white shadow-md px-3 py-3 sm:p-6 shrink-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center gap-3 sm:gap-4">
          <div className="bg-gradient-to-r from-orange-500 to-red-500 p-2 sm:p-3 rounded-full shrink-0">
            <RiRobot2Line className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-base sm:text-2xl font-bold text-gray-800 sm:truncate leading-tight">RashtraGuru Chatbot</h1>
            <p className="hidden sm:block text-gray-600">Your guide to understanding Indian Constitution</p>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 shrink-0">
            <span className="hidden sm:inline font-medium">Reply in</span>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="max-w-[8.5rem] sm:max-w-none rounded-lg border border-gray-300 bg-white px-2 sm:px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500"
              aria-label="Chatbot reply language"
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain">
      <div className="max-w-4xl mx-auto p-3 sm:p-4 pb-6">
        {chatHistory.length === 0 ? (
          <div className="text-center py-8 sm:py-20">
            <div className="bg-white p-5 sm:p-8 rounded-2xl shadow-lg max-w-lg mx-auto">
              <RiRobot2Line className="w-16 h-16 mx-auto text-orange-500 mb-4" />
              <h2 className="text-xl font-semibold mb-4">Welcome to RashtraGuru!</h2>
              <p className="text-gray-600 mb-4">
                Ask me about the Indian Constitution in 13 languages - pick one above, or tap a question to start:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[
                  "What are the Fundamental Rights?",
                  "What does Article 21 say?",
                  "Can police arrest me without telling me why?",
                  "What is the right to education?",
                  "Who appoints the Prime Minister?",
                  "What does Article 14 guarantee?",
                ].map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => handleSubmit(null, q)}
                    className="bg-gray-50 hover:bg-orange-50 hover:border-orange-300 border border-transparent active:scale-95 transition p-2.5 rounded-lg text-sm text-gray-700 text-left"
                  >
                    {q}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-xs text-gray-500">Answers come from the text of the Constitution, with sources. You can also use the mic or upload an image.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {chatHistory.map((entry, index) => (
              <div key={index} className={`flex ${entry.role === 'bot' ? 'justify-start' : 'justify-end'} gap-3`}>
                {entry.role === 'bot' && (
                  <div className="flex-shrink-0">
                    <div className="bg-gradient-to-r from-orange-500 to-red-500 p-2 rounded-full">
                      <RiRobot2Line className="w-6 h-6 text-white" />
                    </div>
                  </div>
                )}
                <div className={`flex flex-col max-w-[85%] sm:max-w-[70%] min-w-0 ${entry.role === 'bot' ? 'items-start' : 'items-end'}`}>
                  <div className={`p-4 rounded-2xl ${
                    entry.role === 'bot' 
                      ? 'bg-white shadow-md' 
                      : 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
                  }`}>
                    {entry.image && <img src={entry.image} alt="Uploaded" className="mb-2 max-h-48 rounded-lg" />}
                    <p className={`text-sm whitespace-pre-wrap break-words ${entry.error ? 'text-red-600' : ''}`}>{entry.content}</p>
                  </div>
                  {entry.role === 'bot' && !entry.error && entry.verified && (
                    <div className="mt-2 w-full min-w-0">
                      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                        {entry.mode === 'answer' ? 'Verified against the Constitution text' : entry.mode === 'source_only' ? 'Exact Constitution text' : entry.mode === 'not_found' && entry.sources?.length ? 'Closest provisions (exact text)' : 'Checked'}
                      </span>
                      {entry.sources?.length > 0 && (
                        <details className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-gray-800">
                          <summary className="cursor-pointer font-semibold text-amber-900">
                            Sources: {entry.sources.map((s) => s.label || `Article ${s.article}`).filter((v, i, a) => a.indexOf(v) === i).join(', ')}
                          </summary>
                          <ul className="mt-2 space-y-2">
                            {entry.sources.map((s) => (
                              <li key={s.id}>
                                <p className="font-semibold">{s.label || `Article ${s.article}`} -{s.article_title} <span className="font-normal text-gray-500">({s.part})</span></p>
                                {language === 'Marathi' && s.text_mr && (
                                  <p className="whitespace-pre-line leading-relaxed mb-1 border-l-4 border-orange-300 pl-2" lang="mr">{s.text_mr}</p>
                                )}
                                <p className="whitespace-pre-line leading-relaxed">{s.text.replace(/\n{2,}/g, '\n')}</p>
                              </li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  )}
                  <span className="text-xs text-gray-500 mt-1">
                    {formatTime(entry.ts)}
                  </span>
                </div>
                {entry.role === 'user' && (
                  <div className="flex-shrink-0">
                    <div className="bg-gray-200 p-2 rounded-full">
                      <FaUser className="w-6 h-6 text-gray-600" />
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3" aria-live="polite">
                <div className="bg-gradient-to-r from-orange-500 to-red-500 p-2 rounded-full h-fit">
                  <RiRobot2Line className="w-6 h-6 text-white" />
                </div>
                <div className="bg-white shadow-md rounded-2xl px-4 py-3 flex items-center gap-1" role="status" aria-label="RashtraGuru is typing">
                  <span className="w-2 h-2 rounded-full bg-orange-400 animate-bounce" />
                  <span className="w-2 h-2 rounded-full bg-orange-400 animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-orange-400 animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            )}
            <div ref={endOfChatRef} />
          </div>
        )}
      </div>
      </div>

      {/* Input Form */}
      <div className="shrink-0 bg-white border-t border-gray-200 p-2 sm:p-4">
        <div className="max-w-4xl mx-auto">
          {notice && <p className="mb-2 text-sm text-red-600" role="alert">{notice}</p>}
          {image && (
            <div className="mb-2 flex items-center gap-2">
              <img src={image.preview} alt="Selected" className="h-14 rounded-lg border" />
              <button type="button" onClick={() => setImage(null)} className="text-gray-600 hover:text-red-600" aria-label="Remove image"><FaTimes /></button>
              <span className="text-xs text-gray-600">Ask a question about this image (or just send it).</span>
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <select value={speechLang} onChange={(e) => setSpeechLang(e.target.value)} disabled={listening} className="hidden sm:block rounded-xl border border-gray-300 bg-white px-2 text-sm text-gray-900" aria-label="Speaking language">
              {SPEECH_LANGS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
            <button type="button" onClick={toggleMic} className={`shrink-0 px-3 rounded-xl border ${listening ? 'bg-red-500 text-white animate-pulse border-red-500' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`} aria-label={listening ? 'Stop listening' : 'Speak your question'} title={listening ? 'Stop' : 'Speak'}>
              {listening ? <FaStop /> : <FaMicrophone />}
            </button>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" onChange={pickImage} className="hidden" />
            <button type="button" onClick={() => fileRef.current?.click()} className="shrink-0 px-3 rounded-xl border border-gray-300 bg-white text-gray-700 hover:bg-gray-50" aria-label="Upload an image" title="Upload image"><FaImage /></button>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={listening ? 'Listening…' : image ? 'Ask about this image…' : language === 'English' ? 'Ask about the Indian Constitution...' : `Ask in any language - reply in ${language}`}
              className="flex-1 min-w-0 px-3 sm:px-4 py-3 rounded-xl bg-gray-100 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
            />
            <button
              type="submit"
              disabled={loading}
              className="shrink-0 px-4 sm:px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-medium hover:opacity-90 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? '...' : (
                <>
                  <span className="hidden sm:inline">Ask</span> <FaPaperPlane className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}