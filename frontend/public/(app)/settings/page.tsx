"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useParams, usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sun, Moon, Monitor, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import { ApiError, apiClient, getApiBase } from "@/lib/utils";

type ConnStatus = "idle" | "checking" | "ok" | "error";

interface SystemStatus {
    supabase: { reachable: boolean };
    groq: { reachable: boolean };
    embedding: { loaded: boolean };
    strict_ai_mode: boolean;
    overall_status: "healthy" | "degraded";
}

const API_BASE = getApiBase();

export default function SettingsPage() {
    const t = useTranslations("settings");
    const { theme, setTheme } = useTheme();
    const params = useParams();
    const pathname = usePathname();
    const router = useRouter();
    const locale = (params?.locale as string) || "en";

    const [backendStatus, setBackendStatus] = useState<ConnStatus>("idle");
    const [aiStatus, setAiStatus] = useState<ConnStatus>("idle");
    const [embeddingStatus, setEmbeddingStatus] = useState<ConnStatus>("idle");
    const [statusHint, setStatusHint] = useState<string>("");

    const toggleLanguage = (lang: string) => {
        if (lang === locale) return;
        const newPath = pathname.replace(`/${locale}`, `/${lang}`);
        router.push(newPath);
    };

    const checkConnections = useCallback(async () => {
        setBackendStatus("checking");
        setAiStatus("checking");
        setEmbeddingStatus("checking");
        setStatusHint("");
        try {
            const health = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(6000) });
            setBackendStatus(health.ok ? "ok" : "error");
        } catch {
            setBackendStatus("error");
        }

        try {
            const payload = await apiClient.get<SystemStatus>("/system/status");
            setAiStatus(payload.groq.reachable ? "ok" : "error");
            setEmbeddingStatus(payload.embedding.loaded ? "ok" : "error");
            setStatusHint(
                payload.strict_ai_mode
                    ? "Strict AI mode: ON"
                    : "Strict AI mode: OFF",
            );
        } catch (err: unknown) {
            setAiStatus("error");
            setEmbeddingStatus("error");
            setStatusHint(err instanceof ApiError ? err.message : "Failed to read system status.");
        }
    }, []);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            void checkConnections();
        }, 0);
        return () => window.clearTimeout(timer);
    }, [checkConnections]);

    const StatusIcon = ({ status }: { status: ConnStatus }) => {
        if (status === "checking") return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
        if (status === "ok") return <CheckCircle2 className="w-4 h-4 text-green-500 dark:text-green-400" />;
        if (status === "error") return <XCircle className="w-4 h-4 text-red-500 dark:text-red-400" />;
        return <div className="w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-800" />;
    };

    const StatusText = ({ status }: { status: ConnStatus }) => {
        if (status === "checking") return <span className="text-xs text-gray-500 dark:text-gray-400">{t("checking")}</span>;
        if (status === "ok") return <span className="text-xs font-medium text-green-600 dark:text-green-400">{t("connected")}</span>;
        if (status === "error") return <span className="text-xs font-medium text-red-600 dark:text-red-400">{t("disconnected")}</span>;
        return <span className="text-xs text-gray-400 dark:text-gray-600">—</span>;
    };

    const themeOptions = [
        { value: "light", label: t("light"), icon: Sun },
        { value: "dark", label: t("dark"), icon: Moon },
        { value: "system", label: t("system"), icon: Monitor },
    ];

    const resolvedTheme = theme ?? "system";

    return (
        <div className="max-w-xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
            </div>

            <motion.div className="card p-5 space-y-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
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

            <motion.div className="card p-5 space-y-4 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">{t("api")}</p>
                    {/* 👇 ambient-glow class added here */}
                    <button 
                        onClick={() => void checkConnections()} 
                        className="ambient-glow bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 text-gray-700 dark:text-gray-300 font-medium text-xs py-1.5 px-3 rounded-lg transition-colors"
                    >
                        Recheck
                    </button>
                </div>
                
                {statusHint && <p className="text-xs text-gray-500 dark:text-gray-400 font-mono bg-gray-50 dark:bg-gray-800/50 p-2 rounded-md border border-gray-100 dark:border-gray-800">{statusHint}</p>}
                
                <div className="space-y-3 pt-1">
                    {[
                        { label: t("backendStatus"), status: backendStatus, url: `${API_BASE}/health` },
                        { label: t("aiStatus"), status: aiStatus, url: "Groq API (via backend system status)" },
                        { label: "Embeddings (SentenceTransformers)", status: embeddingStatus, url: "paraphrase-MiniLM-L3-v2" },
                    ].map(({ label, status, url }) => (
                        <div key={label} className="flex items-center justify-between py-1 border-b border-gray-50 dark:border-gray-800/50 last:border-0">
                            <div>
                                <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
                                <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{url}</p>
                            </div>
                            <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800/30 px-2 py-1.5 rounded-md border border-gray-100 dark:border-gray-800">
                                <StatusIcon status={status} />
                                <StatusText status={status} />
                            </div>
                        </div>
                    ))}
                </div>
            </motion.div>

            <motion.div className="card p-5 space-y-1.5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">About</p>
                <p className="text-sm text-gray-900 dark:text-white font-semibold">Digital Governance Intelligence Portal</p>
                <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">National e-Governance Division (NeGD), MeitY</p>
                <p className="text-xs text-gray-500 dark:text-gray-500">Developed by NeGD and Ashneet Jha (ashneetjha.netlify.app), Intern at IIT Ropar</p>
                <p className="text-xs text-gray-400 dark:text-gray-600 pt-2 font-mono">Open Source · MIT License</p>
            </motion.div>
        </div>
    );
}