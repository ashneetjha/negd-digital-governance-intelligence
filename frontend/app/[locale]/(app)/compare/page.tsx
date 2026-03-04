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
        <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("subtitle")}</p>
            </div>

            <motion.form
                className="card p-5 space-y-4 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block" htmlFor="cmp-state">{t("state")}</label>
                        <select id="cmp-state" className="input-field bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800" value={state} onChange={(e) => setState(e.target.value)} required>
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
                    <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block" htmlFor="cmp-topic">{t("topic")}</label>
                    <input id="cmp-topic" type="text" className="input-field bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800" placeholder={t("topicPlaceholder")} value={topic} onChange={(e) => setTopic(e.target.value)} />
                </div>
                <div className="flex justify-end pt-2">
                    {/* 👇 Added ambient-glow here to make the primary action pop subtly */}
                    <button type="submit" className="ambient-glow btn-primary flex items-center gap-2" disabled={loading || !state || !monthA || !monthB}>
                        {loading ? <><Loader2 className="w-4 h-4 animate-spin" />{t("comparing")}</> : <><GitCompare className="w-4 h-4" />{t("submit")}</>}
                    </button>
                </div>
            </motion.form>

            {error && (
                <div className="card p-4 flex items-center gap-3 bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <p className="text-sm font-medium text-red-700 dark:text-red-400">{error}</p>
                </div>
            )}

            {loading && (
                <div className="space-y-4 animate-fade-in">
                    <div className="card p-5 space-y-4 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                        <div className="skeleton h-4 w-36 rounded" />
                        <div className="space-y-2">
                            <div className="skeleton-text w-full" />
                            <div className="skeleton-text w-11/12" />
                            <div className="skeleton-text w-3/4" />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card p-4 space-y-4 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                            <div className="skeleton h-4 w-28 rounded" />
                            <div className="space-y-2">
                                {[...Array(3)].map((_, i) => <div key={i} className="skeleton-text" style={{ width: SKELETON_WIDTHS[i % SKELETON_WIDTHS.length] }} />)}
                            </div>
                        </div>
                        <div className="card p-4 space-y-4 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                            <div className="skeleton h-4 w-32 rounded" />
                            <div className="space-y-2">
                                {[...Array(3)].map((_, i) => <div key={i} className="skeleton-text" style={{ width: SKELETON_WIDTHS[(i + 1) % SKELETON_WIDTHS.length] }} />)}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <AnimatePresence>
                {result && (
                    <motion.div className="space-y-4" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                        <div className="card p-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{t("summary")}</p>
                            <p className="text-sm text-gray-900 dark:text-gray-200 leading-relaxed">{result.summary}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="card p-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="p-1 rounded bg-green-100 dark:bg-green-900/30">
                                        <Plus className="w-4 h-4 text-green-600 dark:text-green-400" />
                                    </div>
                                    <p className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider">{t("newInitiatives")}</p>
                                </div>
                                {result.new_initiatives.length === 0 ? (
                                    <p className="text-sm text-gray-500 dark:text-gray-400 italic">{t("noChanges")}</p>
                                ) : (
                                    <ul className="space-y-2.5">
                                        {result.new_initiatives.map((item, i) => (
                                            <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-500 dark:bg-green-400 mt-1.5 flex-shrink-0" />
                                                <span>{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>

                            <div className="card p-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-2 mb-4">
                                    <div className="p-1 rounded bg-red-100 dark:bg-red-900/30">
                                        <Minus className="w-4 h-4 text-red-600 dark:text-red-400" />
                                    </div>
                                    <p className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider">{t("removedMentions")}</p>
                                </div>
                                {result.removed_mentions.length === 0 ? (
                                    <p className="text-sm text-gray-500 dark:text-gray-400 italic">{t("noChanges")}</p>
                                ) : (
                                    <ul className="space-y-2.5">
                                        {result.removed_mentions.map((item, i) => (
                                            <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                                                <span className="w-1.5 h-1.5 rounded-full bg-red-500 dark:bg-red-400 mt-1.5 flex-shrink-0" />
                                                <span className="opacity-80 line-through">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>

                        {result.quantitative_changes.length > 0 && (
                            <div className="card overflow-hidden bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                                <div className="p-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/20">
                                    <p className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider">{t("quantitativeChanges")}</p>
                                </div>
                                <div className="md:hidden p-3 space-y-2">
                                    {result.quantitative_changes.map((row, i) => (
                                        <div key={i} className="rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/30 p-3">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">{row.metric}</p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 font-mono">{monthA}: {row.month_a}</p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 font-mono">{monthB}: {row.month_b}</p>
                                        </div>
                                    ))}
                                </div>
                                <div className="hidden md:block">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-100 dark:border-gray-800">
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("metric")}</th>
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{monthA}</th>
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{monthB}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.quantitative_changes.map((row, i) => (
                                                <tr key={i} className="border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                                                    <td className="px-5 py-3 font-medium text-gray-900 dark:text-white">{row.metric}</td>
                                                    <td className="px-5 py-3 text-gray-600 dark:text-gray-300 font-mono text-xs">{row.month_a}</td>
                                                    <td className="px-5 py-3 text-gray-600 dark:text-gray-300 font-mono text-xs">{row.month_b}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {result.compliance_changes.length > 0 && (
                            <div className="card overflow-hidden bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                                <div className="p-4 border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/20 flex items-center gap-2">
                                    <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                    <p className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider">{t("complianceChanges")}</p>
                                </div>
                                <div className="md:hidden p-3 space-y-2">
                                    {result.compliance_changes.map((row, i) => (
                                        <div key={i} className="rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/30 p-3">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">{row.area}</p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{monthA}: <span className="font-semibold">{row.status_month_a}</span></p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400">{monthB}: <span className="font-semibold">{row.status_month_b}</span></p>
                                        </div>
                                    ))}
                                </div>
                                <div className="hidden md:block">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-100 dark:border-gray-800">
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("area")}</th>
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{monthA}</th>
                                                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">{monthB}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.compliance_changes.map((row, i) => (
                                                <tr key={i} className="border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                                                    <td className="px-5 py-3 font-medium text-gray-900 dark:text-white">{row.area}</td>
                                                    <td className="px-5 py-3 text-gray-600 dark:text-gray-300 font-semibold">{row.status_month_a}</td>
                                                    <td className="px-5 py-3 text-gray-600 dark:text-gray-300 font-semibold">{row.status_month_b}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {result.citations.length > 0 && (
                            <div className="card p-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800">
                                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">{t("citations")}</p>
                                <div className="flex flex-wrap gap-2">
                                    {result.citations.map((c, i) => (
                                        <span key={i} className="text-[11px] px-2.5 py-1.5 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-medium border border-gray-200 dark:border-gray-700">
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
                <div className="card p-10 text-center bg-transparent border-dashed border-gray-300 dark:border-gray-800 shadow-none">
                    <GitCompare className="w-10 h-10 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{t("noResult")}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 max-w-sm mx-auto">Select a state and two different months to compare governance progress and compliance changes.</p>
                </div>
            )}
        </div>
    );
}