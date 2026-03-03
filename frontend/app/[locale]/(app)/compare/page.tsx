"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitCompare, Loader2, AlertCircle, Plus, Minus, Shield } from "lucide-react";
import { INDIAN_STATES, apiClient } from "@/lib/utils";
import MonthYearPicker from "@/components/ui/MonthYearPicker";

interface QuantChange { metric: string; month_a: string; month_b: string; }
interface ComplianceChange { area: string; status_month_a: string; status_month_b: string; }
interface Citation { state: string; reporting_month: string; section_type: string; }

interface CompareResult {
    summary: string;
    new_initiatives: string[];
    removed_mentions: string[];
    quantitative_changes: QuantChange[];
    compliance_changes: ComplianceChange[];
    citations: Citation[];
    error?: string;
}

const SKELETON_WIDTHS = ["72%", "84%", "68%"];

export default function ComparePage() {
    const t = useTranslations("compare");
    const [state, setState] = useState("");
    const [monthA, setMonthA] = useState("");
    const [monthB, setMonthB] = useState("");
    const [topic, setTopic] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<CompareResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!state || !monthA || !monthB) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const data = await apiClient.post<{ data: CompareResult }>("/compare", {
                state,
                month_a: monthA,
                month_b: monthB,
                topic: topic || undefined,
            });
            setResult(data.data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Comparison failed.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in max-w-4xl">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <motion.form
                className="card p-5 space-y-4"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                        <label className="label" htmlFor="cmp-state">{t("state")}</label>
                        <select id="cmp-state" className="input-field" value={state} onChange={(e) => setState(e.target.value)} required>
                            <option value="">— Select —</option>
                            {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>
                    <div>
                        <MonthYearPicker
                            id="cmp-month-a"
                            label={t("monthA")}
                            value={monthA}
                            onChange={setMonthA}
                            placeholder="— Select —"
                            required
                        />
                    </div>
                    <div>
                        <MonthYearPicker
                            id="cmp-month-b"
                            label={t("monthB")}
                            value={monthB}
                            onChange={setMonthB}
                            placeholder="— Select —"
                            required
                        />
                    </div>
                </div>
                <div>
                    <label className="label" htmlFor="cmp-topic">{t("topic")}</label>
                    <input id="cmp-topic" type="text" className="input-field" placeholder={t("topicPlaceholder")} value={topic} onChange={(e) => setTopic(e.target.value)} />
                </div>
                <div className="flex justify-end">
                    <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading || !state || !monthA || !monthB}>
                        {loading ? <><Loader2 className="w-4 h-4 animate-spin" />{t("comparing")}</> : <><GitCompare className="w-4 h-4" />{t("submit")}</>}
                    </button>
                </div>
            </motion.form>

            {error && (
                <div className="card p-4 flex items-center gap-3">
                    <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                    <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
            )}

            {loading && (
                <div className="space-y-4 animate-fade-in">
                    <div className="card p-5 space-y-3">
                        <div className="skeleton h-4 w-36 rounded" />
                        <div className="space-y-2">
                            <div className="skeleton-text w-full" />
                            <div className="skeleton-text w-11/12" />
                            <div className="skeleton-text w-3/4" />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card p-4 space-y-3">
                            <div className="skeleton h-4 w-28 rounded" />
                            <div className="space-y-1.5">
                                {[...Array(3)].map((_, i) => <div key={i} className="skeleton-text" style={{ width: SKELETON_WIDTHS[i % SKELETON_WIDTHS.length] }} />)}
                            </div>
                        </div>
                        <div className="card p-4 space-y-3">
                            <div className="skeleton h-4 w-32 rounded" />
                            <div className="space-y-1.5">
                                {[...Array(3)].map((_, i) => <div key={i} className="skeleton-text" style={{ width: SKELETON_WIDTHS[(i + 1) % SKELETON_WIDTHS.length] }} />)}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <AnimatePresence>
                {result && (
                    <motion.div className="space-y-4" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                        <div className="card p-5">
                            <p className="label mb-2">{t("summary")}</p>
                            <p className="text-sm text-[var(--text-primary)] leading-relaxed">{result.summary}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="card p-4">
                                <div className="flex items-center gap-2 mb-3">
                                    <Plus className="w-4 h-4 text-green-500" />
                                    <p className="label">{t("newInitiatives")}</p>
                                </div>
                                {result.new_initiatives.length === 0 ? (
                                    <p className="text-xs text-[var(--text-muted)]">{t("noChanges")}</p>
                                ) : (
                                    <ul className="space-y-1">
                                        {result.new_initiatives.map((item, i) => (
                                            <li key={i} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-1.5 flex-shrink-0" />
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>

                            <div className="card p-4">
                                <div className="flex items-center gap-2 mb-3">
                                    <Minus className="w-4 h-4 text-red-400" />
                                    <p className="label">{t("removedMentions")}</p>
                                </div>
                                {result.removed_mentions.length === 0 ? (
                                    <p className="text-xs text-[var(--text-muted)]">{t("noChanges")}</p>
                                ) : (
                                    <ul className="space-y-1">
                                        {result.removed_mentions.map((item, i) => (
                                            <li key={i} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>

                        {result.quantitative_changes.length > 0 && (
                            <div className="card overflow-hidden">
                                <div className="p-4 border-b border-[var(--bg-border)]">
                                    <p className="label">{t("quantitativeChanges")}</p>
                                </div>
                                <div className="md:hidden p-3 space-y-2">
                                    {result.quantitative_changes.map((row, i) => (
                                        <div key={i} className="rounded-lg border border-[var(--bg-border)] bg-[var(--bg-surface-2)] p-3">
                                            <p className="text-sm font-medium text-[var(--text-primary)]">{row.metric}</p>
                                            <p className="text-xs text-[var(--text-secondary)] mt-1">{monthA}: {row.month_a}</p>
                                            <p className="text-xs text-[var(--text-secondary)]">{monthB}: {row.month_b}</p>
                                        </div>
                                    ))}
                                </div>
                                <div className="hidden md:block">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-[var(--bg-border)]">
                                                <th className="text-left px-4 py-2.5 label">{t("metric")}</th>
                                                <th className="text-left px-4 py-2.5 label">{monthA}</th>
                                                <th className="text-left px-4 py-2.5 label">{monthB}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.quantitative_changes.map((row, i) => (
                                                <tr key={i} className="border-b border-[var(--bg-border)] last:border-0">
                                                    <td className="px-4 py-2.5 font-medium text-[var(--text-primary)]">{row.metric}</td>
                                                    <td className="px-4 py-2.5 text-[var(--text-secondary)]">{row.month_a}</td>
                                                    <td className="px-4 py-2.5 text-[var(--text-secondary)]">{row.month_b}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {result.compliance_changes.length > 0 && (
                            <div className="card overflow-hidden">
                                <div className="p-4 border-b border-[var(--bg-border)] flex items-center gap-2">
                                    <Shield className="w-4 h-4 text-[var(--accent)]" />
                                    <p className="label">{t("complianceChanges")}</p>
                                </div>
                                <div className="md:hidden p-3 space-y-2">
                                    {result.compliance_changes.map((row, i) => (
                                        <div key={i} className="rounded-lg border border-[var(--bg-border)] bg-[var(--bg-surface-2)] p-3">
                                            <p className="text-sm font-medium text-[var(--text-primary)]">{row.area}</p>
                                            <p className="text-xs text-[var(--text-secondary)] mt-1">{monthA}: {row.status_month_a}</p>
                                            <p className="text-xs text-[var(--text-secondary)]">{monthB}: {row.status_month_b}</p>
                                        </div>
                                    ))}
                                </div>
                                <div className="hidden md:block">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-[var(--bg-border)]">
                                                <th className="text-left px-4 py-2.5 label">{t("area")}</th>
                                                <th className="text-left px-4 py-2.5 label">{monthA}</th>
                                                <th className="text-left px-4 py-2.5 label">{monthB}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.compliance_changes.map((row, i) => (
                                                <tr key={i} className="border-b border-[var(--bg-border)] last:border-0">
                                                    <td className="px-4 py-2.5 font-medium text-[var(--text-primary)]">{row.area}</td>
                                                    <td className="px-4 py-2.5 text-[var(--text-secondary)]">{row.status_month_a}</td>
                                                    <td className="px-4 py-2.5 text-[var(--text-secondary)]">{row.status_month_b}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {result.citations.length > 0 && (
                            <div className="card p-4">
                                <p className="label mb-3">{t("citations")}</p>
                                <div className="flex flex-wrap gap-2">
                                    {result.citations.map((c, i) => (
                                        <span key={i} className="text-xs px-2 py-1 rounded bg-[var(--bg-surface-2)] text-[var(--text-secondary)]">
                                            {c.state} · {c.reporting_month} · {c.section_type}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            {!result && !loading && !error && (
                <div className="card p-8 text-center text-[var(--text-muted)]">
                    <GitCompare className="w-8 h-8 mx-auto mb-3 opacity-40" />
                    <p className="text-sm">{t("noResult")}</p>
                </div>
            )}
        </div>
    );
}
