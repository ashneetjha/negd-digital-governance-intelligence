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
    gaps?: any[];
    recommendations?: any[];
    top_insights?: string[];
    confidence_reason?: string;
    structured?: {
        summary?: string;
        key_insights?: string[];
        changes_detected?: string[];
        risks?: string[];
        status?: string;
        confidence?: number;
        data_coverage?: "limited" | "moderate" | "strong";
    };
    metadata?: {
        route?: string;
        confidence?: number;
        latency?: number;
        confidence_reason?: string;
    };
    data_coverage?: "limited" | "moderate" | "strong";
    error?: boolean;
    error_type?: string;
    fallback_used?: boolean;
}

interface AnalysisEnvelope {
    answer?: string;
    sources?: Source[];
    gaps?: any[];
    recommendations?: any[];
    top_insights?: string[];
    confidence_reason?: string;
    structured?: AnalysisResult["structured"];
    metadata?: AnalysisResult["metadata"];
    data_coverage?: "limited" | "moderate" | "strong";
    data?: AnalysisResult;
    error?: boolean;
    error_type?: string;
    fallback_used?: boolean;
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
            const response = await apiClient.post<AnalysisEnvelope>("/analysis", {
                prompt,
                state: state || undefined,
                month: month || undefined,
            });

            const normalized: AnalysisResult = {
                answer: response.data?.answer || response.answer || "",
                sources: response.data?.sources || response.sources || [],
                chunks_retrieved: response.data?.chunks_retrieved || (response.data?.sources?.length ?? response.sources?.length ?? 0),
                gaps: response.data?.gaps || response.gaps,
                recommendations: response.data?.recommendations || response.recommendations,
                top_insights: response.data?.top_insights || response.top_insights,
                confidence_reason: response.data?.confidence_reason || response.confidence_reason || response.metadata?.confidence_reason || "",
                data_coverage: (response.data?.data_coverage || response.data_coverage || response.structured?.data_coverage || "limited") as "limited" | "moderate" | "strong",
                structured: response.data?.structured || response.structured,
                metadata: response.data?.metadata || response.metadata,
                error: response.data?.error ?? response.error,
                error_type: response.data?.error_type || response.error_type,
                fallback_used: response.data?.fallback_used ?? response.fallback_used,
            };

            setResult(normalized);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : t("noResult"));
        } finally {
            setLoading(false);
        }
    };

    const coverageColor = {
        limited: "bg-red-500/20 text-red-400",
        moderate: "bg-yellow-500/20 text-yellow-400",
        strong: "bg-green-500/20 text-green-400",
    } as const;

    const confidenceLabel = (score: number) => {
        if (score >= 0.8) return { label: "High", color: "bg-green-500/20 text-green-400", barColor: "bg-green-500" };
        if (score >= 0.6) return { label: "Medium", color: "bg-yellow-500/20 text-yellow-400", barColor: "bg-yellow-500" };
        return { label: "Low", color: "bg-red-500/20 text-red-400", barColor: "bg-red-500" };
    };

    const avgConfidenceFromSources =
        result?.sources?.length
            ? result.sources.reduce((sum, s) => sum + s.similarity_score, 0) / result.sources.length
            : 0;

    const safeStructured = result?.structured || {
        summary: "",
        key_insights: [],
        changes_detected: [],
        risks: [],
        confidence: 0.5,
        data_coverage: "limited" as const,
    };

    const safeCoverage = result?.data_coverage || "limited";

    const effectiveConfidence =
        result?.metadata?.confidence ?? safeStructured.confidence ?? avgConfidenceFromSources ?? 0.5;

    const renderAnswer = (text: string) => {
        return text.split("\n").filter(Boolean).map((paragraph, i) => (
            <p key={i} className="text-sm text-[var(--text-primary)] leading-relaxed">
                {paragraph}
            </p>
        ));
    };

    const renderLines = (lines: string[] = []) => {
        const bulletLines = lines.filter((line) => line.trim().startsWith("- ") || line.trim().startsWith("•"));
        const textLines = lines.filter((line) => !(line.trim().startsWith("- ") || line.trim().startsWith("•")));

        return (
            <div className="text-gray-200 text-sm leading-relaxed space-y-1">
                {textLines.map((line, idx) => (
                    <p key={`text-${idx}`}>{line}</p>
                ))}
                {bulletLines.length > 0 && (
                    <ul className="list-disc ml-5 space-y-1 text-gray-200">
                        {bulletLines.map((line, idx) => (
                            <li key={`bullet-${idx}`}>{line.replace(/^[-•]\s*/, "")}</li>
                        ))}
                    </ul>
                )}
            </div>
        );
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
                    <div className="card p-5 space-y-6">
                        <p className="label">{t("filters")}</p>
                        <div>
                            <label className="label text-2xs" htmlFor="analysis-state">{t("state")}</label>
                            <select id="analysis-state" className="input-field" value={state} onChange={(e) => setState(e.target.value)}>
                                <option value="">{t("allStates")}</option>
                                {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        <div className="relative overflow-visible">
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
                        <motion.div className="card p-5 space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <p className="label">Query Stats</p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                {/* Chunks Retrieved */}
                                <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1.5">
                                        <BarChart3 className="w-3 h-3 text-[var(--text-muted)]" />
                                        <span className="text-[var(--text-muted)]">{t("chunksRetrieved")}</span>
                                    </div>
                                    <span className="font-medium text-[var(--text-primary)]">{result?.chunks_retrieved ?? 0}</span>
                                </div>

                                {/* Data Coverage */}
                                <div className="flex items-center justify-between text-xs border-t border-[var(--bg-border)] pt-3">
                                    <div className="flex items-center gap-1.5">
                                        <BarChart3 className="w-3 h-3 text-[var(--text-muted)]" />
                                        <span className="text-[var(--text-muted)]">Data Coverage</span>
                                    </div>
                                    <span className={clsx("px-2 py-1 text-xs rounded-full", coverageColor[safeCoverage])}>
                                        {safeCoverage}
                                    </span>
                                </div>

                                {/* Confidence with progress bar */}
                                <div className="space-y-1.5 border-t border-[var(--bg-border)] pt-3">
                                    <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-1.5">
                                            <ShieldCheck className="w-3 h-3 text-[var(--text-muted)]" />
                                            <span className="text-[var(--text-muted)]">{t("confidence")}</span>
                                        </div>
                                        <span className={clsx("px-2 py-1 text-xs rounded-full", confidenceLabel(effectiveConfidence).color)}>
                                            {confidenceLabel(effectiveConfidence).label}
                                        </span>
                                    </div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-bar-fill"
                                            style={{ width: `${effectiveConfidence * 100}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Route */}
                                {result?.metadata?.route && (
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-[var(--text-muted)]">Route</span>
                                        <span className="font-medium text-[var(--text-primary)] uppercase tracking-wide">{result.metadata.route}</span>
                                    </div>
                                )}

                                {/* Latency */}
                                {typeof result?.metadata?.latency === "number" && (
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-[var(--text-muted)]">Latency</span>
                                        <span className="font-medium text-[var(--text-primary)]">{result.metadata.latency.toFixed(0)} ms</span>
                                    </div>
                                )}

                                {/* Source count */}
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-[var(--text-muted)]">Sources Used</span>
                                    <span className="font-medium text-[var(--text-primary)]">{result.sources?.length ?? 0}</span>
                                </div>
                            </div>
                            
                            {/* Confidence Reason Box */}
                            {result?.confidence_reason && (
                                <p className="text-sm text-[var(--text-muted)] mt-4 p-3 bg-[var(--bg-surface-2)] rounded-lg italic">
                                    {result.confidence_reason}
                                </p>
                            )}
                        </motion.div>
                    )}
                </div>

                {/* Center + Right — Query + Result */}
                <div className="col-span-1 lg:col-span-3 space-y-4">
                    {/* Query Form */}
                    <motion.form
                        className="card p-5 space-y-6"
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
                                className="btn-primary flex items-center gap-2 disabled:opacity-50"
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
                                {result.error_type === "NO_DATA_FOR_FILTER" && result.fallback_used === false && (
                                    <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900/30 rounded-lg text-sm mb-4 font-semibold flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" />
                                        Showing best available insights based on indexed reports
                                    </div>
                                )}

                                <div className="flex items-center gap-2 border-b border-[var(--bg-border)] pb-3">
                                    <BookOpen className="w-4 h-4 text-[var(--accent)]" />
                                    <span className="font-medium text-sm text-[var(--text-primary)]">{t("answer")}</span>
                                </div>

                                {/* Answer text — rendered as paragraphs */}
                                <div className="space-y-3 text-sm md:text-base">
                                    {renderAnswer(result?.answer || "")}
                                </div>

                                {/* Structured governance output */}
                                {(safeStructured.summary ||
                                    (safeStructured.key_insights?.length ?? 0) > 0 ||
                                    (safeStructured.changes_detected?.length ?? 0) > 0 ||
                                    (safeStructured.risks?.length ?? 0) > 0) && (
                                    <div className="border-t border-[var(--bg-border)] pt-4 space-y-6">
                                        {safeStructured.summary && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Executive Summary</h3>
                                                {renderLines([safeStructured.summary])}
                                            </div>
                                        )}

                                        {(safeStructured.key_insights?.length ?? 0) > 0 && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Key Insights</h3>
                                                {renderLines(((result?.top_insights?.length ?? 0) > 0 ? result.top_insights : safeStructured.key_insights) || [])}
                                            </div>
                                        )}

                                        {(result.gaps?.length ?? 0) > 0 && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Identified Gaps</h3>
                                                <div className="space-y-3">
                                                    {result.gaps!.map((gap, i) => (
                                                        <div key={i} className="text-[15px] bg-amber-50/10 border border-amber-900/30 p-3 rounded-lg leading-relaxed text-gray-200">
                                                            <span className="font-semibold">{gap.area}:</span> {gap.description}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {(result.recommendations?.length ?? 0) > 0 && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Recommendations</h3>
                                                <div className="space-y-3">
                                                    {result.recommendations!.map((rec, i) => (
                                                        <div key={i} className="text-[15px] bg-blue-50/10 border border-blue-900/30 p-3 rounded-lg leading-relaxed text-gray-200">
                                                            <span className="font-semibold">{rec.area}:</span> {rec.recommendation}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {(safeStructured.changes_detected?.length ?? 0) > 0 && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Changes Detected / Ongoing Work</h3>
                                                {renderLines(safeStructured.changes_detected || [])}
                                            </div>
                                        )}

                                        {(safeStructured.risks?.length ?? 0) > 0 && (
                                            <div className="space-y-2">
                                                <h3 className="text-indigo-300 font-medium text-sm uppercase tracking-wide">Risks</h3>
                                                {renderLines(safeStructured.risks || [])}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Sources toggle */}
                                {(result.sources?.length ?? 0) > 0 && (
                                    <div className="border-t border-[var(--bg-border)] pt-3">
                                        <button
                                            type="button"
                                            className="flex items-center gap-2 text-sm font-semibold border border-[var(--bg-border)] px-4 py-2 rounded-lg text-[var(--accent)] hover:bg-[var(--bg-surface-2)] transition-colors mt-2"
                                            onClick={() => setShowSources(!showSources)}
                                        >
                                            {showSources ? "Hide Sources" : "Show Sources"} ({result.sources.length})
                                            {showSources ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
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
                            <p className="text-sm">Showing best available insights based on indexed reports</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
