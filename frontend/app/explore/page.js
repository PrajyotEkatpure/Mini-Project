"use client";
import Articles from '@/components/Articles';
import React, { useState } from 'react';
import jsonData from './data.json';
import NavBar from '@/components/NavBar';
import dynamic from 'next/dynamic';

// react-pdf needs the browser (canvas, workers), so the reader is never rendered on the server.
const ConstitutionReader = dynamic(() => import('@/components/ConstitutionReader'), {
  ssr: false,
  loading: () => <div className="p-10 text-center text-gray-500">Opening the Constitution...</div>,
});

export default function Page() {
  const [partNo, setPartNo] = useState('Part I');
  const [view, setView] = useState('articles'); // 'articles' | 'read'

  return (
    <div className="min-h-screen bg-white">
      <NavBar />
      
      {/* Mobile Sidebar Toggle */}
      <button
        data-drawer-target="default-sidebar"
        data-drawer-toggle="default-sidebar"
        aria-controls="default-sidebar"
        type="button"
        className="sm:hidden fixed top-20 left-4 z-50 p-2 rounded-md bg-white shadow-md hover:bg-gray-100 transition-colors duration-200"
      >
        <span className="sr-only">Open sidebar</span>
        <svg
          className="w-6 h-6 text-gray-600"
          aria-hidden="true"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            clipRule="evenodd"
            fillRule="evenodd"
            d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 10.5a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5a.75.75 0 01-.75-.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10z"
          />
        </svg>
      </button>

      {/* Sidebar */}
      {view === 'articles' && (
      <aside
        id="default-sidebar"
        className="fixed top-0 left-0 z-40 w-64 h-screen transition-transform -translate-x-full sm:translate-x-0 shadow-lg"
        aria-label="Sidebar"
      >
        <div className="h-full px-3 py-4 overflow-y-auto bg-white border-r border-gray-200">
          <div className="mb-6">
            <a href="/">
              <button
                className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 transition-colors duration-200"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Home
              </button>
            </a>
          </div>
          
          <h2 className="px-3 mb-4 text-lg font-semibold text-gray-900">Constitution Parts</h2>
          <ul className="space-y-1">
            {jsonData.map((item) => (
              <li key={item.part}>
                <button
                  onClick={() => {
                    setPartNo(item.part);
                    console.log(item.part);
                  }}
                  className={`flex items-center w-full p-3 text-gray-700 rounded-lg hover:bg-gray-100 group transition-colors duration-200 ${
                    partNo === item.part ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <svg
                    className={`flex-shrink-0 w-5 h-5 transition-colors duration-200 ${
                      partNo === item.part 
                        ? 'text-blue-600' 
                        : 'text-gray-500 group-hover:text-gray-900'
                    }`}
                    aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="currentColor"
                    viewBox="0 0 18 18"
                  >
                    <path d="M6.143 0H1.857A1.857 1.857 0 0 0 0 1.857v4.286C0 7.169.831 8 1.857 8h4.286A1.857 1.857 0 0 0 8 6.143V1.857A1.857 1.857 0 0 0 6.143 0Zm10 0h-4.286A1.857 1.857 0 0 0 10 1.857v4.286C10 7.169 10.831 8 11.857 8h4.286A1.857 1.857 0 0 0 18 6.143V1.857A1.857 1.857 0 0 0 16.143 0Zm-10 10H1.857A1.857 1.857 0 0 0 0 11.857v4.286C0 17.169.831 18 1.857 18h4.286A1.857 1.857 0 0 0 8 16.143v-4.286A1.857 1.857 0 0 0 6.143 10Zm10 0h-4.286A1.857 1.857 0 0 0 10 11.857v4.286c0 1.026.831 1.857 1.857 1.857h4.286A1.857 1.857 0 0 0 18 16.143v-4.286A1.857 1.857 0 0 0 16.143 10Z" />
                  </svg>
                  <span className="ms-3 text-left">{item.part}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>
      )}

      {/* Main Content */}
      <div className={`p-4 ${view === 'articles' ? 'sm:ml-64' : 'max-w-7xl mx-auto'}`}>
        <div role="tablist" aria-label="Explore mode" className="mt-2 inline-flex rounded-xl bg-gray-100 p-1">
          {[
            ['articles', 'Browse Articles'],
            ['read', 'Read the Constitution'],
          ].map(([key, label]) => (
            <button
              key={key}
              role="tab"
              aria-selected={view === key}
              onClick={() => setView(key)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                view === key ? 'bg-white text-gray-900 shadow' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {view === 'articles' ? (
          <div className="p-4 mt-4 bg-white rounded-lg shadow-md">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">{partNo}</h1>
            <Articles partNo={partNo} />
          </div>
        ) : (
          <div className="mt-4">
            <ConstitutionReader />
          </div>
        )}
      </div>
    </div>
  );
}