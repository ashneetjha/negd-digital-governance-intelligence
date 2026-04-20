"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon, Monitor, CheckCircle2, XCircle, Loader2, Activity } from "lucide-react";
import { clsx } from "clsx";
import { ApiError, apiClient, getApiBase } from "@/lib/utils";

type ConnStatus = "idle" | "checking" | "ok" | "error";

interface TestResult {
    status: ConnStatus;
    latencyMs?: number;
    errorMsg?: string;
}

const API_BASE = getApiBase();

export default function SettingsPage() {
    const t = useTranslations("settings");
    const { theme, setTheme } = useTheme();
    const params = useParams();
    const pathname = usePathname();
    const router = useRouter();
    const locale = (params?.locale as string) || "en";

    const [mounted, setMounted] = useState(false);
    const [sysStatus, setSysStatus] = useState<TestResult>({ status: "idle" });
    const [chatStatus, setChatStatus] = useState<TestResult>({ status: "idle" });
    const [analysisStatus, setAnalysisStatus] = useState<TestResult>({ status: "idle" });
    const [intelStatus, setIntelStatus] = useState<TestResult>({ status: "idle" });

    const toggleLanguage = (lang: string) => {
        if (lang === locale) return;
        const newPath = pathname.replace(`/${locale}`, `/${lang}`);
        router.push(newPath);
    };

    const runTest = async (
        setter: React.Dispatch<React.SetStateAction<TestResult>>,
        fn: () => Promise<void>
    ) => {
        setter({ status: "checking" });
        const t0 = performance.now();
        try {
            await fn();
            setter({ status: "ok", latencyMs: Math.round(performance.now() - t0) });
        } catch (err: any) {
            const msg = err instanceof ApiError ? err.message : (err.message || "Unknown error");
            setter({ status: "error", latencyMs: Math.round(performance.now() - t0), errorMsg: msg });
        }
    };

    const checkConnections = useCallback(async () => {
        // Run all tests in parallel to accurately map system capacity
        await Promise.all([
            runTest(setSysStatus, async () => {
                const res = await fetch(`${API_BASE}/api/system/status`, { signal: AbortSignal.timeout(30000) });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
            }),
            runTest(setChatStatus, async () => {
                await apiClient.post("/chat", { message: "system ping" });
            }),
            runTest(setAnalysisStatus, async () => {
                // Testing RAG retrieval pathway
                await apiClient.post("/analysis", { prompt: "test analysis", state: "Delhi" });
            }),
            runTest(setIntelStatus, async () => {
                await apiClient.get("/intelligence/national");
            })
        ]);
    }, []);

    useEffect(() => {
        setMounted(true);
        const timer = window.setTimeout(() => {
            void checkConnections();
        }, 0);
        return () => window.clearTimeout(timer);
    }, [checkConnections]);

    const StatusRow = ({ label, result, description }: { label: string, result: TestResult, description: string }) => (
        <div className="flex items-center justify-between py-3 border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50/50 dark:hover:bg-gray-800/10 px-2 rounded-lg transition-colors">
            <div className="flex-1 pr-4">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    {label}
                </p>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 font-mono tracking-tight">{description}</p>
                {result.status === "error" && result.errorMsg && (
                    <div className="mt-2 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 p-2 rounded">
                         <p className="text-xs text-red-600 dark:text-red-400 font-mono">Error: {result.errorMsg}</p>
                    </div>
                )}
            </div>
            <div className="flex flex-col items-end gap-1.5 min-w-[100px]">
                <div className={clsx(
                    "flex items-center gap-2 px-2.5 py-1.5 rounded-md border w-full justify-center transition-all",
                    result.status === "checking" ? "bg-blue-50 dark:bg-blue-900/20 border-blue-100 dark:border-blue-800/30" :
                    result.status === "ok" ? "bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800/30" :
                    result.status === "error" ? "bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/30" :
                    "bg-gray-50 dark:bg-gray-800/30 border-gray-100 dark:border-gray-800"
                )}>
                    {result.status === "checking" && <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600 dark:text-blue-400" />}
                    {result.status === "ok" && <CheckCircle2 className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />}
                    {result.status === "error" && <XCircle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />}
                    
                    <span className={clsx(
                        "text-[11px] font-bold uppercase tracking-wider",
                        result.status === "checking" ? "text-blue-700 dark:text-blue-400" :
                        result.status === "ok" ? "text-green-700 dark:text-green-400" :
                        result.status === "error" ? "text-red-700 dark:text-red-400" :
                        "text-gray-500 dark:text-gray-400"
                    )}>
                        {result.status === "checking" ? "Testing" : result.status === "ok" ? "Passed" : result.status === "error" ? "Failed" : "Idle"}
                    </span>
                </div>
                {result.latencyMs !== undefined && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 font-mono font-medium">
                        {result.latencyMs} ms
                    </span>
                )}
            </div>
        </div>
    );

    const themeOptions = [
        { value: "light", label: t("light"), icon: Sun },
        { value: "dark", label: t("dark"), icon: Moon },
        { value: "system", label: t("system"), icon: Monitor },
    ];
    const resolvedTheme = mounted ? (theme ?? "system") : "system";

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-12">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Platform Diagnostic Interface</p>
            </div>

            <motion.div className="card p-5 space-y-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-3.5 h-3.5" />
                        System Health Dashboard
                    </p>
                    <button 
                        onClick={() => void checkConnections()} 
                        disabled={sysStatus.status === "checking" || chatStatus.status === "checking" || analysisStatus.status === "checking" || intelStatus.status === "checking"}
                        className="ambient-glow bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-medium text-[11px] py-1.5 px-3 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {sysStatus.status === "checking" ? "Running Diagnostics..." : "Run Diagnostics"}
                    </button>
                </div>
                
                <div className="bg-gray-50/50 dark:bg-black/20 p-2 rounded-xl border border-gray-100 dark:border-gray-800/50 space-y-1">
                    <StatusRow 
                        label="Core Backend Heartbeat" 
                        result={sysStatus} 
                        description="GET /api/system/status" 
                    />
                    <StatusRow 
                        label="General Conversational RAG" 
                        result={chatStatus} 
                        description="POST /api/chat — Standard query test" 
                    />
                    <StatusRow 
                        label="Governance Intelligence Engine" 
                        result={analysisStatus} 
                        description="POST /api/analysis — PGVector Hybrid Retrieval" 
                    />
                    <StatusRow 
                        label="State Ranking Metrics Pipeline" 
                        result={intelStatus} 
                        description="GET /api/intelligence/national — Matrix compute validation" 
                    />
                </div>
            </motion.div>

            <motion.div className="card p-5 space-y-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t("appearance")}</p>
                <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2.5">{t("theme")}</p>
                    <div className="flex gap-2">
                        {themeOptions.map(({ value, label, icon: Icon }) => (
                            <button
                                key={value}
                                onClick={() => setTheme(value)}
                                className={clsx(
                                    "flex-1 flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl border text-xs font-medium transition-all duration-200",
                                    resolvedTheme === value
                                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 shadow-sm"
                                        : "border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400 hover:border-blue-400 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/50",
                                )}
                            >
                                <Icon className="w-4 h-4" />
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2.5">{t("language")}</p>
                    <div className="flex gap-2">
                        {[
                            { code: "en", label: t("english"), flag: "🇬🇧" },
                            { code: "hi", label: t("hindi"), flag: "🇮🇳" },
                        ].map(({ code, label, flag }) => (
                            <button
                                key={code}
                                onClick={() => toggleLanguage(code)}
                                className={clsx(
                                    "flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border text-xs font-medium transition-all duration-200",
                                    locale === code
                                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 shadow-sm"
                                        : "border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400 hover:border-blue-400 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/50",
                                )}
                            >
                                <span>{flag}</span>
                                {label}
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>

            <motion.div className="card p-5 space-y-1.5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">About</p>
                <p className="text-sm text-gray-900 dark:text-white font-semibold flex items-center gap-2">
                    Digital Governance Intelligence Portal
                    <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest">PROD</span>
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 font-medium mt-1">National e-Governance Division (NeGD), MeitY</p>
                <div className="text-xs text-gray-400 dark:text-gray-500 font-medium border-t border-[var(--bg-border)] pt-3 mt-3">
                    By: Ashneet Jha<br/>
                    Portfolio: <a href="https://ashneetjha.netlify.app/" target="_blank" rel="noreferrer" className="text-blue-500 hover:text-blue-600 transition-colors">https://ashneetjha.netlify.app/</a><br/>
                    Intern, IIT Ropar | SRM IST, KTR
                </div>
            </motion.div>
        </div>
    );
}
