"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { AlertCircle, GitCompare, Loader2 } from "lucide-react";

import MonthYearPicker from "@/components/ui/MonthYearPicker";
import { INDIAN_STATES, apiClient } from "@/lib/utils";

interface CrossStateResult {
    summary: string;
    differences: string[];
    commonalities: string[];
    recommendations: string[];
    citations: Array<{ state: string; reporting_month: string; section_type: string }>;
}

export default function CrossStateComparePage() {
    const t = useTranslations("crossState");

    const [stateA, setStateA] = useState("");
    const [monthA, setMonthA] = useState("");
    const [stateB, setStateB] = useState("");
    const [monthB, setMonthB] = useState("");
    const [topic, setTopic] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<CrossStateResult | null>(null);

    const canSubmit = stateA && monthA && stateB && monthB;

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!canSubmit) return;

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const res = await apiClient.post<{ data: CrossStateResult }>("/compare/cross-state", {
                state_a: stateA,
                month_a: monthA,
                state_b: stateB,
                month_b: monthB,
                topic: topic || undefined,
            });
            setResult(res.data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : t("fallbackError"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 max-w-5xl">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <form className="card p-5 space-y-6" onSubmit={submit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="label" htmlFor="state-a">{t("stateA")}</label>
                        <select id="state-a" className="input-field" value={stateA} onChange={(e) => setStateA(e.target.value)}>
                            <option value="">--</option>
                            {INDIAN_STATES.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <MonthYearPicker
                            id="month-a"
                            label={t("monthA")}
                            value={monthA}
                            onChange={setMonthA}
                            placeholder="--"
                            required
                        />
                    </div>
                    <div>
                        <label className="label" htmlFor="state-b">{t("stateB")}</label>
                        <select id="state-b" className="input-field" value={stateB} onChange={(e) => setStateB(e.target.value)}>
                            <option value="">--</option>
                            {INDIAN_STATES.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <MonthYearPicker
                            id="month-b"
                            label={t("monthB")}
                            value={monthB}
                            onChange={setMonthB}
                            placeholder="--"
                            required
                        />
                    </div>
                </div>

                <div>
                    <label className="label" htmlFor="topic">{t("topic")}</label>
                    <input
                        id="topic"
                        type="text"
                        className="input-field"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder={t("topicPlaceholder")}
                    />
                </div>

                <div className="flex justify-end">
                    <button type="submit" className="btn-primary flex items-center gap-2 disabled:opacity-50" disabled={!canSubmit || loading}>
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
                        {loading ? t("comparing") : t("submit")}
                    </button>
                </div>
            </form>

            {error && (
                <div className="card p-4 flex items-center gap-2 text-red-600 dark:text-red-400">
                    <AlertCircle className="w-4 h-4" />
                    <span>{error}</span>
                </div>
            )}

            {!loading && !error && !result && (
                <div className="card p-8 text-center text-gray-400 text-sm">
                    Showing best available insights based on indexed reports
                </div>
            )}

            {result && (
                <div className="space-y-6">
                    <div className="card p-5">
                        <h2 className="section-title">{t("summary")}</h2>
                        <div className="section-divider" />
                        <p className="text-sm md:text-base leading-relaxed text-gray-200">{result?.summary || ""}</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 space-y-2">
                            <h2 className="section-title">{t("differences")}</h2>
                            <div className="section-divider" />
                            <ul className="space-y-2 text-sm text-gray-200">
                                {(result.differences || []).map((d, idx) => (
                                    <li key={idx}>- {d}</li>
                                ))}
                            </ul>
                        </div>
                        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 space-y-2">
                            <h2 className="section-title">{t("commonalities")}</h2>
                            <div className="section-divider" />
                            <ul className="space-y-2 text-sm text-gray-200">
                                {(result.commonalities || []).map((c, idx) => (
                                    <li key={idx}>- {c}</li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {(result.recommendations || []).length > 0 && (
                        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 space-y-2">
                            <h2 className="section-title">{t("recommendations")}</h2>
                            <div className="section-divider" />
                            <ul className="space-y-2 text-sm text-gray-200">
                                {result.recommendations.map((r, idx) => (
                                    <li key={idx}>- {r}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
