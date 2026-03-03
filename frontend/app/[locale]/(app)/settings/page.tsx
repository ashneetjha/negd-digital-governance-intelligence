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
        if (status === "checking") return <Loader2 className="w-4 h-4 animate-spin text-[var(--accent)]" />;
        if (status === "ok") return <CheckCircle2 className="w-4 h-4 text-green-500" />;
        if (status === "error") return <XCircle className="w-4 h-4 text-red-500" />;
        return <div className="w-4 h-4 rounded-full bg-[var(--bg-border)]" />;
    };

    const StatusText = ({ status }: { status: ConnStatus }) => {
        if (status === "checking") return <span className="text-xs text-[var(--text-muted)]">{t("checking")}</span>;
        if (status === "ok") return <span className="text-xs text-green-600 dark:text-green-400">{t("connected")}</span>;
        if (status === "error") return <span className="text-xs text-red-500">{t("disconnected")}</span>;
        return <span className="text-xs text-[var(--text-muted)]">—</span>;
    };

    const themeOptions = [
        { value: "light", label: t("light"), icon: Sun },
        { value: "dark", label: t("dark"), icon: Moon },
        { value: "system", label: t("system"), icon: Monitor },
    ];

    const resolvedTheme = theme ?? "system";

    return (
        <div className="max-w-xl space-y-6 animate-fade-in">
            <div>
                <h1 className="page-title">{t("title")}</h1>
            </div>

            <motion.div className="card p-5 space-y-5" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <p className="label">{t("appearance")}</p>

                <div>
                    <p className="text-xs text-[var(--text-secondary)] mb-2">{t("theme")}</p>
                    <div className="flex gap-2">
                        {themeOptions.map(({ value, label, icon: Icon }) => (
                            <button
                                key={value}
                                onClick={() => setTheme(value)}
                                className={clsx(
                                    "flex-1 flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl border text-xs font-medium transition-all",
                                    resolvedTheme === value
                                        ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                                        : "border-[var(--bg-border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:bg-[var(--bg-surface-2)]",
                                )}
                            >
                                <Icon className="w-4 h-4" />
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                <div>
                    <p className="text-xs text-[var(--text-secondary)] mb-2">{t("language")}</p>
                    <div className="flex gap-2">
                        {[
                            { code: "en", label: t("english"), flag: "🇬🇧" },
                            { code: "hi", label: t("hindi"), flag: "🇮🇳" },
                        ].map(({ code, label, flag }) => (
                            <button
                                key={code}
                                onClick={() => toggleLanguage(code)}
                                className={clsx(
                                    "flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border text-xs font-medium transition-all",
                                    locale === code
                                        ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                                        : "border-[var(--bg-border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:bg-[var(--bg-surface-2)]",
                                )}
                            >
                                <span>{flag}</span>
                                {label}
                            </button>
                        ))}
                    </div>
                </div>
            </motion.div>

            <motion.div className="card p-5 space-y-4" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <div className="flex items-center justify-between">
                    <p className="label">{t("api")}</p>
                    <button onClick={() => void checkConnections()} className="btn-secondary text-xs py-1 px-2">Recheck</button>
                </div>
                {statusHint && <p className="text-xs text-[var(--text-muted)]">{statusHint}</p>}
                <div className="space-y-3">
                    {[
                        { label: t("backendStatus"), status: backendStatus, url: `${API_BASE}/health` },
                        { label: t("aiStatus"), status: aiStatus, url: "Groq API (via backend system status)" },
                        { label: "Embeddings (SentenceTransformers)", status: embeddingStatus, url: "all-MiniLM-L6-v2" },
                    ].map(({ label, status, url }) => (
                        <div key={label} className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-[var(--text-primary)]">{label}</p>
                                <p className="text-xs text-[var(--text-muted)]">{url}</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <StatusIcon status={status} />
                                <StatusText status={status} />
                            </div>
                        </div>
                    ))}
                </div>
            </motion.div>

            <motion.div className="card p-5 space-y-1" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                <p className="label">About</p>
                <p className="text-sm text-[var(--text-primary)] font-medium">Digital Governance Intelligence Portal</p>
                <p className="text-xs text-[var(--text-muted)]">National e-Governance Division (NeGD), MeitY</p>
                <p className="text-xs text-[var(--text-muted)]">Developed by IIT Ropar</p>
                <p className="text-xs text-[var(--text-muted)] pt-1">Version 1.0.0 · Open Source · MIT License</p>
            </motion.div>
        </div>
    );
}
