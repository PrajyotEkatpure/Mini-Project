"use client";
import React, { useEffect, useState } from "react";
import TranslateComponent from "@/components/TranslateComponent";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMusic } from "@/components/MusicContext";

const LINKS = [
    { href: "/", label: "Home" },
    { href: "/explore", label: "Explore" },
    { href: "/chatbot", label: "Chatbot" },
    { href: "/learn", label: "Learn" },
    { href: "/book", label: "Book" },
    { href: "/games", label: "Games" },
    { href: "/leaderboard", label: "Leaderboard" },
    { href: "/about", label: "About us" },
];

export default function NavBar() {
    const [username, setUsername] = useState(null);
    const [open, setOpen] = useState(false);
    const { isPlaying, toggleMusic } = useMusic();
    const pathname = usePathname() || "/";

    useEffect(() => {
        const storedUsername = localStorage.getItem("username");
        if (storedUsername) {
            setUsername(storedUsername);
        }
    }, []);

    // close the mobile menu after navigating, or when Escape is pressed
    useEffect(() => {
        setOpen(false);
    }, [pathname]);
    useEffect(() => {
        const onKey = (e) => e.key === "Escape" && setOpen(false);
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    const handleLogout = () => {
        localStorage.clear();
        setUsername(null);
        window.location.href = "/";
    };

    const isActive = (href) => (href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/"));

    return (
        <nav className="bg-black text-gray-100 static bg-opacity-90 w-full top-0 start-0">
            <div className="flex flex-wrap items-center justify-between mx-auto p-4">
                <Link href="/" className="group flex items-center space-x-3 rtl:space-x-reverse">
                    <img
                        src="./../../logo.svg"
                        className="h-8 transition-transform duration-300 group-hover:rotate-12 group-hover:scale-110"
                        alt="Samvidhan Logo"
                    />
                    <span className="self-center text-2xl font-semibold whitespace-nowrap transition-colors group-hover:text-orange-400">
                        Samvidhan
                    </span>
                </Link>

                <div className="flex md:order-2 space-x-3 md:space-x-0 rtl:space-x-reverse items-center gap-3">
                    {/* Music toggle */}
                    <button
                        onClick={toggleMusic}
                        title={isPlaying ? "Pause Music" : "Play Music"}
                        aria-pressed={isPlaying}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-300 active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 ${
                            isPlaying
                                ? "bg-orange-500 border-orange-400 text-white shadow-lg shadow-orange-500/30 animate-pulse"
                                : "bg-transparent border-gray-500 text-gray-300 hover:border-orange-400 hover:text-orange-400"
                        }`}
                    >
                        {isPlaying ? (
                            <>
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                                </svg>
                                Music On
                            </>
                        ) : (
                            <>
                                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
                                </svg>
                                Music
                            </>
                        )}
                    </button>

                    {username ? (
                        <div className="flex items-center gap-4">
                            <span className="hidden sm:inline text-sm text-gray-100">Welcome, {username}</span>
                            <button
                                onClick={handleLogout}
                                className="text-white bg-red-600 hover:bg-red-700 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-red-600/30 active:scale-95 transition-all duration-200 focus:ring-4 focus:outline-none focus:ring-red-300 font-medium rounded-lg text-sm px-4 py-2 text-center"
                            >
                                Logout
                            </button>
                        </div>
                    ) : (
                        <Link href="/login">
                            <button
                                type="button"
                                className="text-white bg-orange-700 hover:bg-orange-600 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-orange-600/30 active:scale-95 transition-all duration-200 focus:ring-4 focus:outline-none focus:ring-orange-300 font-medium rounded-lg text-sm px-4 py-2 text-center"
                            >
                                Login
                            </button>
                        </Link>
                    )}

                    {/* Mobile menu button */}
                    <button
                        type="button"
                        onClick={() => setOpen((o) => !o)}
                        className="inline-flex items-center p-2 w-10 h-10 justify-center text-gray-300 rounded-lg md:hidden hover:bg-gray-800 hover:text-orange-400 active:scale-90 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
                        aria-controls="navbar-sticky"
                        aria-expanded={open}
                        aria-label={open ? "Close main menu" : "Open main menu"}
                    >
                        <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 17 14">
                            {open ? (
                                <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2 1l13 12M15 1L2 13" />
                            ) : (
                                <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M1 1h15M1 7h15M1 13h15" />
                            )}
                        </svg>
                    </button>
                </div>

                <div
                    className={`${open ? "flex" : "hidden"} items-center justify-between w-full md:flex md:w-auto md:order-1`}
                    id="navbar-sticky"
                >
                    <ul className="flex flex-col p-4 md:p-0 mt-4 font-medium border border-gray-700 rounded-lg md:space-x-8 rtl:space-x-reverse md:flex-row md:mt-0 md:border-0 w-full md:w-auto">
                        {LINKS.map(({ href, label }) => {
                            const active = isActive(href);
                            return (
                                <li key={href}>
                                    <Link
                                        href={href}
                                        aria-current={active ? "page" : undefined}
                                        className={`group relative block py-2 px-3 rounded md:p-0 transition-all duration-200 active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400 ${
                                            active
                                                ? "text-orange-400 bg-gray-800 md:bg-transparent"
                                                : "text-gray-100 hover:text-orange-400 hover:bg-gray-800 md:hover:bg-transparent md:hover:-translate-y-0.5"
                                        }`}
                                    >
                                        {label}
                                        <span
                                            aria-hidden="true"
                                            className={`hidden md:block absolute -bottom-1 left-0 h-0.5 rounded bg-orange-400 transition-all duration-300 ${
                                                active ? "w-full" : "w-0 group-hover:w-full"
                                            }`}
                                        />
                                    </Link>
                                </li>
                            );
                        })}
                        <li className="md:ml-8 px-3 py-2 md:p-0">
                            <TranslateComponent />
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    );
}
