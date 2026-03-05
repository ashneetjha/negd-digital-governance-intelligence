"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronDown, ChevronUp, Loader2, AlertCircle, BookOpen, Sparkles, ShieldCheck, BarChart3 } from "lucide-react";
import { clsx } from "clsx";
import { INDIAN_STATES, apiClient } from "@/lib/utils";
import MonthYearPicker from "@/components/ui/MonthYearPicker";

interface Source {
    state: string;
    reporting_month: string;
    section_type: string | null;
    page_number: number | null;
    similarity_score: number;
}

interface AnalysisResult {
    answer: string;
    sources: Source[];
    chunks_retrieved: number;
}

function AnalysisSkeleton() {
    return (
        <div className="space-y-4">
            <div className="card p-5 space-y-4">
                <div className="flex items-center gap-2 border-b border-[var(--bg-border)] pb-3">
                    <div className="skeleton w-4 h-4 rounded" />
                    <div className="skeleton h-4 w-32 rounded" />
                </div>
                <div className="space-y-2">
                    <div className="skeleton-text w-full" />
                    <div className="skeleton-text w-full" />
                    <div className="skeleton-text w-11/12" />
                    <div className="skeleton-text w-3/4" />
                    <div className="skeleton-text w-full" />
                    <div className="skeleton-text w-5/6" />
                </div>
            </div>
        </div>
    );
}

export default function AnalysisPage() {
    const t = useTranslations("analysis");
    const [state, setState] = useState("");
    const [month, setMonth] = useState("");
    const [prompt, setPrompt] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showSources, setShowSources] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const data = await apiClient.post<{ data: AnalysisResult }>("/analysis", {
                prompt,
                state: state || undefined,
                month: month || undefined,
            });
            setResult(data.data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : t("noResult"));
        } finally {
            setLoading(false);
        }
    };

    const confidenceLabel = (score: number) => {
        if (score >= 0.8) return { label: "High", color: "text-green-600 dark:text-green-400", barColor: "bg-green-500" };
        if (score >= 0.6) return { label: "Medium", color: "text-amber-600 dark:text-amber-400", barColor: "bg-amber-500" };
        return { label: "Low", color: "text-red-500", barColor: "bg-red-500" };
    };

    const avgConfidence =
        result?.sources?.length
            ? result.sources.reduce((sum, s) => sum + s.similarity_score, 0) / result.sources.length
            : 0;

    const renderAnswer = (text: string) => {
        return text.split("\n").filter(Boolean).map((paragraph, i) => (
            <p key={i} className="text-sm text-[var(--text-primary)] leading-relaxed">
                {paragraph}
            </p>
        ));
    };

    return (
        <div className="space-y-6 animate-fade-in max-w-5xl">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Left — Filters */}
                <div className="space-y-4">
                    <div className="card p-4 space-y-4">
                        <p className="label">{t("filters")}</p>
                        <div>
                            <label className="label text-2xs" htmlFor="analysis-state">{t("state")}</label>
                            <select id="analysis-state" className="input-field" value={state} onChange={(e) => setState(e.target.value)}>
                                <option value="">{t("allStates")}</option>
                                {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <div>
                            <MonthYearPicker
                                id="analysis-month"
                                label={t("month")}
                                value={month}
                                onChange={setMonth}
                                placeholder={t("allMonths")}
                            />
                        </div>
                    </div>

                    {/* Stats Panel with Confidence Visualization */}
                    {result && (
                        <motion.div className="card p-4 space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <p className="label">Query Stats</p>
                            <div className="space-y-3">
                                {/* Chunks Retrieved */}
                                <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1.5">
                                        <BarChart3 className="w-3 h-3 text-[var(--text-muted)]" />
                                        <span className="text-[var(--text-muted)]">{t("chunksRetrieved")}</span>
                                    </div>
                                    <span className="font-medium text-[var(--text-primary)]">{result.chunks_retrieved}</span>
                                </div>

                                {/* Confidence with progress bar */}
                                <div className="space-y-1.5">
                                    <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-1.5">
                                            <ShieldCheck className="w-3 h-3 text-[var(--text-muted)]" />
                                            <span className="text-[var(--text-muted)]">{t("confidence")}</span>
                                        </div>
                                        <span className={clsx("font-medium", confidenceLabel(avgConfidence).color)}>
                                            {confidenceLabel(avgConfidence).label} ({(avgConfidence * 100).toFixed(0)}%)
                                        </span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-bar-fill"
                                            style={{ width: `${avgConfidence * 100}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Source count */}
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-[var(--text-muted)]">Sources Used</span>
                                    <span className="font-medium text-[var(--text-primary)]">{result.sources?.length ?? 0}</span>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </div>

                {/* Center + Right — Query + Result */}
                <div className="col-span-1 lg:col-span-3 space-y-4">
                    {/* Query Form */}
                    <motion.form
                        className="card p-5 space-y-4"
                        onSubmit={handleSubmit}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <label className="label" htmlFor="analysis-prompt">{t("promptLabel")}</label>
                        <textarea
                            id="analysis-prompt"
                            rows={4}
                            className="input-field resize-none"
                            placeholder={t("promptPlaceholder")}
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            maxLength={2000}
                        />
                        <div className="flex items-center justify-between">
                            <span className="text-xs text-[var(--text-muted)]">{prompt.length}/2000</span>
                            <button
                                type="submit"
                                className="btn-primary flex items-center gap-2"
                                disabled={loading || !prompt.trim()}
                            >
                                {loading ? (
                                    <><Loader2 className="w-4 h-4 animate-spin" />{t("analysing")}</>
                                ) : (
                                    <><Sparkles className="w-4 h-4" />{t("submit")}</>
                                )}
                            </button>
                        </div>
                    </motion.form>

                    {/* Error */}
                    {error && (
                        <div className="card p-4 flex items-center gap-3">
                            <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                        </div>
                    )}

                    {/* Loading Skeleton */}
                    {loading && <AnalysisSkeleton />}

                    {/* Result */}
                    <AnimatePresence>
                        {result && (
                            <motion.div
                                className="card p-5 space-y-4"
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.3 }}
                            >
                                <div className="flex items-center gap-2 border-b border-[var(--bg-border)] pb-3">
                                    <BookOpen className="w-4 h-4 text-[var(--accent)]" />
                                    <span className="font-medium text-sm text-[var(--text-primary)]">{t("answer")}</span>
                                </div>

                                {/* Answer text — rendered as paragraphs */}
                                <div className="space-y-3">
                                    {renderAnswer(result.answer)}
                                </div>

                                {/* Sources toggle */}
                                {(result.sources?.length ?? 0) > 0 && (
                                    <div className="border-t border-[var(--bg-border)] pt-3">
                                        <button
                                            type="button"
                                            className="flex items-center gap-2 text-xs font-medium text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                                            onClick={() => setShowSources(!showSources)}
                                        >
                                            {t("sources")} ({result.sources.length})
                                            {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                        </button>

                                        <AnimatePresence>
                                            {showSources && (
                                                <motion.div
                                                    className="mt-3 space-y-2"
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: "auto" }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                >
                                                    {result.sources.map((src, i) => {
                                                        const conf = confidenceLabel(src.similarity_score);
                                                        return (
                                                            <div key={i} className="rounded-lg bg-[var(--bg-surface-2)] px-3 py-2 text-xs">
                                                                <div className="flex items-center gap-2 flex-wrap">
                                                                    <span className="font-medium text-[var(--text-primary)]">{i + 1}.</span>
                                                                    <span className="text-[var(--accent)]">State: {src.state}</span>
                                                                    <span className="text-[var(--text-muted)]">|</span>
                                                                    <span>Month: {src.reporting_month}</span>
                                                                    {src.section_type && (
                                                                        <>
                                                                            <span className="text-[var(--text-muted)]">|</span>
                                                                            <span>Section: {src.section_type}</span>
                                                                        </>
                                                                    )}
                                                                    {src.page_number && (
                                                                        <>
                                                                            <span className="text-[var(--text-muted)]">|</span>
                                                                            <span>Page {src.page_number}</span>
                                                                        </>
                                                                    )}
                                                                    <span className={clsx("ml-auto font-medium", conf.color)}>
                                                                        {(src.similarity_score * 100).toFixed(0)}%
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Empty state */}
                    {!result && !loading && !error && (
                        <div className="card p-8 text-center text-[var(--text-muted)]">
                            <Search className="w-8 h-8 mx-auto mb-3 opacity-40" />
                            <p className="text-sm">{t("noResult")}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
