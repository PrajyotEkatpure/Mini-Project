"use client";

import { Inter } from "next/font/google";
import Script from "next/script";
import { useEffect } from "react";
import "./globals.css";
import { MusicProvider } from "@/components/MusicContext";

if (typeof Promise.withResolvers === 'undefined') {
  Promise.withResolvers = function () {
    let resolve, reject;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  };
}

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }) {
  useEffect(() => {
    const loadGoogleTranslate = () => {
      if (window.google && window.google.translate && window.google.translate.TranslateElement) {
        new window.google.translate.TranslateElement(
          {
            pageLanguage: "en",
            includedLanguages: "hi,kn,ml,mr,ta,te,pa,bn,gu,or,si",
            layout: window.google.translate.TranslateElement.InlineLayout?.SIMPLE || 1,
          },
          "google_translate_element"
        );
      }
    };

    const interval = setInterval(() => {
      if (window.google && window.google.translate && window.google.translate.TranslateElement) {
        clearInterval(interval);
        loadGoogleTranslate();
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <html lang="en">
      <head>
        <Script
          src="https://translate.google.com/translate_a/element.js?cb=googleTranslateInit"
          strategy="lazyOnload"
        />
      </head>
      <body className={inter.className}>
        {/* Persistent Google Translate Widget */}
        <div
          id="google_translate_element"
          className="hidden md:block"
          style={{ position: "fixed", top: "20px", right: "300px", zIndex: 9999 }}
        ></div>

        <MusicProvider>
          {children}
        </MusicProvider>
      </body>
    </html>
  );
}
