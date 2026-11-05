import React, { useState, useEffect } from 'react';
import jsonData from '../data/data.json';
import { FaMagic } from 'react-icons/fa';
import StoryStudio from './story/StoryStudio';

export default function Articles({ partNo }) {
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [currentPartNo, setCurrentPartNo] = useState(partNo || 1);
  const [loading, setLoading] = useState(false);
  const [storyData, setStoryData] = useState(null);
  const [audience, setAudience] = useState('student');
  const [storyLang, setStoryLang] = useState('en');
  const [style, setStyle] = useState('everyday');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!partNo) {
      setCurrentPartNo(1);
    } else {
      setCurrentPartNo(partNo);
    }
  }, [partNo]);

  const openModal = (article) => {
    setSelectedArticle(article);
    setStoryData(null);
    setMessage('');
  };

  const closeModal = () => {
    setSelectedArticle(null);
    setStoryData(null);
    setMessage('');
  };

  const generateStory = async (fresh = false) => {
    if (!selectedArticle) return;

    setLoading(true);
    setStoryData(null);
    setMessage('');

    try {
      const response = await fetch('http://localhost:5000/api/story/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article: selectedArticle.article, audience, style, fresh, language: storyLang }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setMessage(data.error || 'Something went wrong. Please try again later.');
      } else {
        setStoryData(data);
      }
    } catch (error) {
      setMessage('Could not reach the story service. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const truncateText = (title, description, maxLength) => {
    let totalLength = title.length + description.length;
    if (totalLength > maxLength) {
      let remainingLength = maxLength - title.length;
      description = description.substring(0, remainingLength) + '...';
    }
    return { truncatedTitle: title, truncatedDescription: description };
  };

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {jsonData.map((item) =>
          item.part === currentPartNo ? (
            item.articles.map((art) => {
              const { truncatedTitle, truncatedDescription } = truncateText(
                art.title,
                art.description,
                140
              );
              return (
                <div
                  key={art.article}
                  className="flex flex-col justify-between h-full w-full max-w-xs p-6 bg-white border border-gray-200 rounded-lg shadow-lg"
                >
                  <div>
                    <h5>Article {art.article}</h5>
                    <h5 className="mb-2 text-xl font-bold tracking-tight text-gray-900">
                      {truncatedTitle}
                    </h5>
                    <p className="mb-3 font-normal text-gray-700">
                      {truncatedDescription}
                    </p>
                  </div>
                  <div className="mt-auto">
                    <button
                      onClick={() => openModal(art)}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-center text-white bg-blue-700 rounded-lg hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300"
                    >
                      Read more
                    </button>
                  </div>
                </div>
              );
            })
          ) : null
        )}
      </div>

      {selectedArticle && (
        <div
          id="default-modal"
          tabIndex="-1"
          aria-hidden="true"
          className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center w-full h-full bg-black bg-opacity-50"
        >
          <div className="relative w-full max-w-4xl p-6 max-h-full overflow-y-auto">
            <div className="relative bg-white rounded-lg shadow-lg">
              <div className="flex items-center justify-between p-4 md:p-5 border-b border-gray-200 rounded-t">
                <h3 className="text-xl font-semibold text-gray-900">
                  Article {selectedArticle.article} :{" "}
                </h3>
                <h3 className="text-xl font-semibold text-gray-700">
                  {selectedArticle.title}
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center"
                >
                  <svg
                    className="w-3 h-3"
                    aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 14 14"
                  >
                    <path
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
                    />
                  </svg>
                  <span className="sr-only">Close modal</span>
                </button>
              </div>
              <div className="p-4 md:p-6 space-y-4 overflow-y-auto max-h-[70vh]">
                <p className="text-base leading-relaxed text-gray-600">
                  {selectedArticle.description}
                </p>
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <label className="text-sm text-gray-700">
                      Audience{' '}
                      <select
                        className="ml-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                        id="age"
                        name="age"
                        value={audience}
                        onChange={(e) => setAudience(e.target.value)}
                      >
                        <option value="kid">Kid</option>
                        <option value="student">Student</option>
                        <option value="adult">Adult</option>
                      </select>
                    </label>
                    <label className="text-sm text-gray-700">
                      Language{' '}
                      <select
                        className="ml-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                        value={storyLang}
                        onChange={(e) => setStoryLang(e.target.value)}
                        aria-label="Story language"
                      >
                        <option value="en">English</option>
                        <option value="mr">मराठी (Marathi)</option>
                      </select>
                    </label>
                    <label className="text-sm text-gray-700">
                      Style{' '}
                      <select
                        className="ml-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                        id="style"
                        name="style"
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                      >
                        <option value="everyday">Everyday Life</option>
                        <option value="mystery">Mystery</option>
                        <option value="adventure">Adventure</option>
                        <option value="courtroom">Courtroom Simulation</option>
                      </select>
                    </label>
                    <button
                      onClick={() => generateStory(false)}
                      className="inline-flex items-center px-4 py-2 text-sm font-medium text-center text-white bg-blue-700 rounded-lg hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 disabled:opacity-60"
                      disabled={loading}
                    >
                      {loading ? 'Building a verified story...' : 'Generate Story'}
                      <FaMagic className="ml-2" />
                    </button>
                  </div>
                </div>
                {message && (
                  <div className="text-red-500">
                    <p>{message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      {storyData && (
        <StoryStudio
          key={storyData.story.title}
          data={storyData}
          article={selectedArticle.article}
          audience={audience}
          language={storyLang}
          onClose={() => setStoryData(null)}
          onRegenerate={() => generateStory(true)}
        />
      )}
    </div>
  );
}
