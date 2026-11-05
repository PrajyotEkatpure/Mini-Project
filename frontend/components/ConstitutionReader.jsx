"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

// Worker is served from /public so the reader also works offline.
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

const PDF_URL = "/Constitution.pdf";
const ZOOMS = [0.6, 0.8, 1, 1.25, 1.5, 2];

// The PDF is a scan without an outline or text layer, so navigation is by page number.
function AshokaChakra({ className = "" }) {
  const spokes = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" strokeWidth="4" />
      <circle cx="50" cy="50" r="7" fill="currentColor" />
      {spokes.map((a) => (
        <line key={a} x1="50" y1="50" x2="50" y2="6" stroke="currentColor" strokeWidth="2"
          transform={`rotate(${a} 50 50)`} />
      ))}
    </svg>
  );
}

function Btn({ children, className = "", ...props }) {
  return (
    <button
      type="button"
      {...props}
      className={`inline-flex items-center justify-center rounded-lg border border-amber-300/40 bg-white/10 px-3 py-1.5 text-sm font-medium text-amber-50 transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40 ${className}`}
    >
      {children}
    </button>
  );
}

function Thumb({ n, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group mb-3 block w-full rounded-md p-1 text-center transition ${
        active ? "bg-amber-400/30 ring-2 ring-amber-300" : "hover:bg-white/10"
      }`}
    >
      <div className="overflow-hidden rounded-sm bg-[#fbf3dd] shadow-md">
        <Page pageNumber={n} width={110} renderTextLayer={false} renderAnnotationLayer={false} />
      </div>
      <span className="mt-1 block text-xs text-amber-100/80">{n}</span>
    </button>
  );
}

export default function ConstitutionReader() {
  const [numPages, setNumPages] = useState(null);
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [spread, setSpread] = useState(true);
  const [wide, setWide] = useState(true);
  const [showThumbs, setShowThumbs] = useState(false);
  const [jump, setJump] = useState("1");
  const [loadError, setLoadError] = useState("");
  const [width, setWidth] = useState(600);
  const stageRef = useRef(null);
  const wrapRef = useRef(null);

  // Fit pages to the available width (one page on narrow screens, two side by side on wide ones).
  useEffect(() => {
    const measure = () => {
      const w = stageRef.current?.clientWidth || 800;
      const isWide = w >= 900;
      setWide(isWide);
      setWidth(Math.max(260, (isWide && spread ? w / 2 : w) - 32));
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [spread, showThumbs, numPages]);

  const twoUp = wide && spread;
  // Page 1 is the cover and stands alone; after that pages pair up (2-3, 4-5, ...).
  const leftPage = twoUp && page > 1 ? (page % 2 === 0 ? page : page - 1) : page;
  const rightPage = twoUp && leftPage > 1 && numPages && leftPage + 1 <= numPages ? leftPage + 1 : null;

  const goTo = useCallback(
    (n) => {
      if (!numPages) return;
      const clamped = Math.min(Math.max(1, n), numPages);
      setPage(clamped);
      setJump(String(clamped));
      wrapRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    },
    [numPages]
  );

  const next = () => goTo(twoUp ? (leftPage === 1 ? 2 : leftPage + 2) : page + 1);
  const prev = () => goTo(twoUp ? (leftPage <= 2 ? 1 : leftPage - 2) : page - 1);

  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT") return;
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const fullscreen = () => {
    const el = document.getElementById("constitution-reader");
    if (document.fullscreenElement) document.exitFullscreen();
    else el?.requestFullscreen?.();
  };

  const submitJump = (e) => {
    e.preventDefault();
    const n = parseInt(jump, 10);
    if (!Number.isNaN(n)) goTo(n);
  };

  const pageProps = {
    width: width * zoom,
    renderTextLayer: false,
    renderAnnotationLayer: false,
    loading: <div className="grid h-96 place-items-center text-sm text-stone-500">Turning the page...</div>,
  };

  return (
    <section
      id="constitution-reader"
      className="overflow-hidden rounded-2xl border border-amber-900/30 bg-[#1b1410] shadow-2xl"
    >
      {/* Tricolour band */}
      <div className="flex h-1.5">
        <div className="flex-1 bg-[#FF9933]" />
        <div className="flex-1 bg-white" />
        <div className="flex-1 bg-[#138808]" />
      </div>

      {/* Header */}
      <header className="relative flex flex-wrap items-center gap-4 bg-gradient-to-r from-[#2a1d12] via-[#3b2a18] to-[#2a1d12] px-5 py-4">
        <AshokaChakra className="h-12 w-12 flex-none text-[#4aa3ff] drop-shadow" />
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-[0.3em] text-amber-300/80">We, the People of India</p>
          <h2 className="font-serif text-2xl font-bold text-amber-50 sm:text-3xl">The Constitution of India</h2>
          <p className="text-sm text-amber-100/70">
            Read it right here, page by page{numPages ? ` - ${numPages} pages` : ""}, or keep a copy.
          </p>
        </div>
        <a
          href={PDF_URL}
          download="Constitution-of-India.pdf"
          className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#FF9933] to-[#e8741a] px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:brightness-110"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Download PDF
        </a>
      </header>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-y border-amber-900/40 bg-[#241a12] px-4 py-2">
        <div className="flex items-center gap-2">
          <Btn onClick={() => setShowThumbs((v) => !v)} aria-pressed={showThumbs} title="Page thumbnails">
            Pages
          </Btn>
          <Btn onClick={prev} disabled={!numPages || page <= 1} aria-label="Previous page">&larr; Prev</Btn>
          <form onSubmit={submitJump} className="flex items-center gap-1 text-sm text-amber-100">
            <input
              value={jump}
              onChange={(e) => setJump(e.target.value.replace(/\D/g, ""))}
              className="w-14 rounded-md border border-amber-300/30 bg-black/30 px-2 py-1 text-center text-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-400"
              aria-label="Go to page"
              inputMode="numeric"
            />
            <span>/ {numPages || "..."}</span>
          </form>
          <Btn onClick={next} disabled={!numPages || page >= numPages} aria-label="Next page">Next &rarr;</Btn>
        </div>
        <div className="flex items-center gap-2">
          <Btn onClick={() => setZoom((z) => ZOOMS[Math.max(0, ZOOMS.indexOf(z) - 1)] ?? 1)} disabled={zoom <= ZOOMS[0]} aria-label="Zoom out">-</Btn>
          <span className="w-12 text-center text-sm text-amber-100">{Math.round(zoom * 100)}%</span>
          <Btn onClick={() => setZoom((z) => ZOOMS[Math.min(ZOOMS.length - 1, ZOOMS.indexOf(z) + 1)] ?? 1)} disabled={zoom >= ZOOMS[ZOOMS.length - 1]} aria-label="Zoom in">+</Btn>
          <Btn onClick={() => setZoom(1)}>Fit</Btn>
          <Btn onClick={() => setSpread((v) => !v)} className="hidden lg:inline-flex" title="Toggle two-page spread">
            {spread ? "Single page" : "Book spread"}
          </Btn>
          <Btn onClick={fullscreen}>Full screen</Btn>
        </div>
      </div>

      <Document
        file={PDF_URL}
        onLoadSuccess={({ numPages: n }) => setNumPages(n)}
        onLoadError={() => setLoadError("The Constitution could not be loaded. Use the download button instead.")}
        loading={<div className="grid h-[60vh] place-items-center text-amber-100/80">Opening the Constitution...</div>}
        error={<div className="grid h-[60vh] place-items-center px-6 text-center text-red-300">Could not load the PDF. Use the download button above.</div>}
      >
        {numPages && !loadError && (
          <div className="flex">
            {/* Thumbnails */}
            {showThumbs && (
              <aside className="hidden h-[75vh] w-36 flex-none overflow-y-auto border-r border-amber-900/40 bg-[#17100b] p-3 sm:block">
                {Array.from({ length: numPages }, (_, i) => i + 1).map((n) => (
                  <Thumb key={n} n={n} active={n === leftPage || n === rightPage} onClick={() => goTo(n)} />
                ))}
              </aside>
            )}

            {/* Reading stage */}
            <div ref={stageRef} className="min-w-0 flex-1">
              <div
                ref={wrapRef}
                className="h-[75vh] overflow-auto bg-[radial-gradient(ellipse_at_center,#4a3622_0%,#241a12_75%)] p-4"
              >
                <div className="mx-auto flex w-max min-w-full items-start justify-center">
                  <div className={`flex ${rightPage ? "shadow-[0_20px_50px_rgba(0,0,0,0.6)]" : ""}`}>
                    <div className="relative bg-[#fbf3dd] shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
                      <Page pageNumber={leftPage} {...pageProps} />
                      <span className="pointer-events-none absolute bottom-1 left-2 text-[10px] text-stone-500">{leftPage}</span>
                    </div>
                    {rightPage && (
                      <div className="relative border-l border-stone-400/60 bg-[#fbf3dd] shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
                        <Page pageNumber={rightPage} {...pageProps} />
                        <span className="pointer-events-none absolute bottom-1 right-2 text-[10px] text-stone-500">{rightPage}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              {/* Hidden preload of the next pages keeps turning fast */}
              <div className="hidden">
                {[1, 2, 3].map((o) => {
                  const n = leftPage + (rightPage ? 1 : 0) + o;
                  return n <= numPages ? (
                    <Page key={n} pageNumber={n} width={width * zoom} renderTextLayer={false} renderAnnotationLayer={false} />
                  ) : null;
                })}
              </div>
            </div>
          </div>
        )}
      </Document>

      <footer className="flex flex-wrap items-center justify-between gap-2 bg-[#241a12] px-5 py-2 text-xs text-amber-100/70">
        <span>Tip: use the &larr; &rarr; arrow keys to turn pages.</span>
        <span>
          {rightPage ? `Pages ${leftPage}-${rightPage}` : `Page ${leftPage}`}
          {numPages ? ` of ${numPages}` : ""}
        </span>
      </footer>
    </section>
  );
}
