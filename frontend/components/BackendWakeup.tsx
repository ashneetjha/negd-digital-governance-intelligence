"use client";

/**
 * BackendWakeup
 * ─────────────
 * Silently pings the FastAPI /api/ping endpoint as soon as the app shell
 * mounts.  This fires the request early enough to warm Render's free-tier
 * container while the user reads the dashboard — eliminating the "waiting
 * for first AI response" cold-start delay for most users.
 *
 * UX behaviour:
 *  • First 5 s  → invisible (no banner)
 *  • 5 s+ still waiting → subtle "Warming up AI services…" banner appears
 *  • Ping succeeds    → banner fades out with a brief "Ready" flash
 *  • Ping fails (60 s) → banner shows a non-blocking warning with retry
 */

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Read the backend URL from Next.js public env var; fall back to the
// canonical Render service URL so the build works without extra config.
const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ??
    "https://negd-portal-backend.onrender.com";

const PING_URL = `${API_BASE}/api/ping`;

// How long to wait before showing the banner (ms)
const SHOW_BANNER_AFTER_MS = 5_000;
// Total timeout before declaring the backend unreachable (ms)
const TIMEOUT_MS = 60_000;

type WakeState = "idle" | "pending" | "ready" | "slow" | "failed";

export default function BackendWakeup() {
    const [state, setState] = useState<WakeState>("idle");
    const [latencyMs, setLatencyMs] = useState<number | null>(null);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const abortRef = useRef<AbortController | null>(null);

    const doPing = () => {
        setState("pending");
        const t0 = performance.now();
        const ctrl = new AbortController();
        abortRef.current = ctrl;

        // Show the banner only after SHOW_BANNER_AFTER_MS
        timerRef.current = setTimeout(
            () => setState((s) => s === "pending" ? "slow" : s),
            SHOW_BANNER_AFTER_MS
        );

        const timeout = setTimeout(() => {
            ctrl.abort();
            setState("failed");
        }, TIMEOUT_MS);

        fetch(PING_URL, { signal: ctrl.signal })
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(() => {
                clearTimeout(timeout);
                if (timerRef.current) clearTimeout(timerRef.current);
                setLatencyMs(Math.round(performance.now() - t0));
                setState("ready");
                // Auto-dismiss the "ready" flash after 2 s
                setTimeout(() => setState("idle"), 2_000);
            })
            .catch((err) => {
                clearTimeout(timeout);
                if (timerRef.current) clearTimeout(timerRef.current);
                if ((err as Error).name !== "AbortError") {
                    setState("failed");
                }
            });
    };

    useEffect(() => {
        doPing();
        return () => {
            abortRef.current?.abort();
            if (timerRef.current) clearTimeout(timerRef.current);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const showBanner = state === "slow" || state === "ready" || state === "failed";

    return (
        <AnimatePresence>
            {showBanner && (
                <motion.div
                    key="wakeup-banner"
                    initial={{ opacity: 0, y: -12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.35, ease: "easeOut" }}
                    className={[
                        // Positioning — fixed top bar, above all content
                        "fixed top-0 left-0 right-0 z-[9999]",
                        "flex items-center justify-center gap-3 px-4 py-2.5",
                        "text-sm font-medium tracking-wide",
                        // Glassmorphic indigo strip matching the portal header
                        state === "failed"
                            ? "bg-red-600/90 backdrop-blur-md text-white"
                            : state === "ready"
                              ? "bg-emerald-600/90 backdrop-blur-md text-white"
                              : "bg-indigo-700/90 backdrop-blur-md text-indigo-50",
                        "border-b",
                        state === "failed"
                            ? "border-red-500/40"
                            : state === "ready"
                              ? "border-emerald-500/40"
                              : "border-indigo-500/40",
                    ].join(" ")}
                    role="status"
                    aria-live="polite"
                >
                    {state === "slow" && (
                        <>
                            {/* Animated spinner */}
                            <span
                                className="inline-block h-3.5 w-3.5 rounded-full border-2 border-indigo-200 border-t-white animate-spin"
                                aria-hidden="true"
                            />
                            <span>
                                Warming up AI services — first response may take up to 30 s&hellip;
                            </span>
                        </>
                    )}

                    {state === "ready" && (
                        <>
                            <span aria-hidden="true">✓</span>
                            <span>
                                AI services ready
                                {latencyMs !== null && (
                                    <span className="ml-1.5 opacity-75 text-xs font-normal">
                                        ({latencyMs} ms)
                                    </span>
                                )}
                            </span>
                        </>
                    )}

                    {state === "failed" && (
                        <>
                            <span aria-hidden="true">⚠</span>
                            <span>
                                Backend unreachable — AI features may be unavailable.
                            </span>
                            <button
                                onClick={doPing}
                                className="ml-2 underline underline-offset-2 hover:opacity-80 transition-opacity text-xs"
                            >
                                Retry
                            </button>
                        </>
                    )}
                </motion.div>
            )}
        </AnimatePresence>
    );
}
