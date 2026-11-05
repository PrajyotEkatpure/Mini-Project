"use client"
import React, { useState, useEffect, useRef } from 'react';
import NavBar from '@/components/NavBar';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const SECTIONS = [
  'Relevant Constitutional Articles',
  'Simplified Explanations of Legal Concepts',
  'What the Constitution lets you do',
  'Articles',
];
const SECTION_LABELS = { Articles: 'Exact text of the Articles (from the Constitution)' };

const EXAMPLES = [
  'My landlord asked me to leave because of my religion.',
  'Police arrested me and did not tell me the reason.',
  'My school refused admission because of my caste.',
];

// Turn bare URLs in an answer into clickable links.
function linkify(text) {
  return String(text).split(/(https?:\/\/[^\s)]+)/g).map((part, i) =>
    /^https?:\/\//.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline break-all">
        {part}
      </a>
    ) : (
      part
    )
  );
}

function App() {
  const [result, setResult] = useState(null);
  const [scenario, setScenario] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    if (result || error) endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [result, error]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = scenario.trim();
    if (!text || loading) return;

    setResult(null);
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/get_scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.response) {
        throw new Error(data.error || 'Could not analyse this scenario. Please try again.');
      }
      setResult(data.response);
      setScenario('');
    } catch (err) {
      console.error('Error:', err);
      setError(
        err instanceof TypeError
          ? 'Cannot reach the server. Please make sure the backend is running on port 5000.'
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='bg-white min-h-screen flex flex-col'>
      <NavBar />
      <div className='flex-grow flex justify-center items-center p-4 '>
        <section className='w-full max-w-4xl h-[calc(100vh-6rem)]'>
          <div className="border-4 border-amber-900 rounded-lg bg-amber-50 w-full h-full flex flex-col shadow-lg overflow-hidden">
            <div className="bg-amber-800 text-amber-50 p-4 text-center text-xl font-serif">
              Constitutional Scenario Learning
            </div>
            <div className='flex-grow p-5 overflow-y-auto bg-amber-50'>
              {!result && !loading && !error && (
                <div className="text-center text-amber-900 py-10">
                  <p className="font-serif text-lg mb-4">Describe a real-life situation and see which parts of the Constitution apply.</p>
                  <div className="flex flex-col items-center gap-2">
                    {EXAMPLES.map((ex) => (
                      <button
                        key={ex}
                        type="button"
                        onClick={() => setScenario(ex)}
                        className="text-sm bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded-full px-4 py-1.5"
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {loading && <div className='text-center text-amber-900 animate-pulse'>System is preparing response...</div>}
              {error && (
                <div role="alert" className="p-3 bg-red-50 border border-red-300 text-red-700 rounded-lg my-2">{error}</div>
              )}
              {result && (
                <div>
                  <div className="p-2 bg-amber-100 rounded-lg my-2">
                    <h2 className="font-semibold text-amber-900">Scenario:</h2>
                    <p className="text-amber-900">{result.scenario}</p>
                    {result.verified && (
                      <span className="mt-2 inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                        Every statement below is checked against the Constitution text
                      </span>
                    )}
                  </div>
                  {SECTIONS.map((section) =>
                    (result[section] || []).length > 0 && (
                      <div key={section} className="p-2 bg-amber-100 rounded-lg my-2">
                        <h2 className="font-semibold text-amber-900">{SECTION_LABELS[section] || section}:</h2>
                        {result[section].map((item, i) => (
                          <div key={i} className="mt-1">
                            <p className="text-amber-900 font-medium">{item.title}</p>
                            <p className='text-black whitespace-pre-line'>{linkify(item.answer)}</p>
                          </div>
                        ))}
                      </div>
                    )
                  )}
                  {result.disclaimer && <p className="mt-3 text-xs italic text-amber-900">{result.disclaimer}</p>}
                </div>
              )}
              <div ref={endRef} />
            </div>

            <form className="p-4 bg-amber-100" onSubmit={handleSubmit}>
              <div className="flex flex-row input-group w-full relative">
                <textarea
                  placeholder="Ask Your Doubt .... "
                  onChange={(e) => setScenario(e.target.value)}
                  value={scenario}
                  className="input justify-center input-bordered w-full border-2 p-2 border-amber-900 bg-amber-50 text-amber-900 placeholder-amber-700 focus:ring-2 focus:ring-amber-700 focus:border-transparent"
                  required
                />
                <button
                  className="btn2 btn-square w-auto ml-2 px-3 bg-amber-800 hover:bg-amber-900 text-amber-50 disabled:opacity-50"
                  type="submit"
                  disabled={loading}
                  aria-label="Send scenario"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z" />
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
