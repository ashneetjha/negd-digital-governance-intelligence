"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, FileText, CheckCircle2, TrendingUp, Cpu, MapPin, Trophy, ShieldAlert, Zap, ArrowRight } from "lucide-react";
import { ApiError, apiClient } from "@/lib/utils";
import { animateStaggerIn } from "@/lib/animations";

interface RankingData {
    total_states: number;
    total_reports: number;
    total_chunks: number;
    top_performers: any[];
    bottom_performers: any[];
    risk_alerts: any[];
    emerging_trends: any[];
    all_states_scores: any[];
    gap_analysis: any[];
    recommendations: any[];
    confidence_reason: string;
    confidence: number;
    status: string;
}

function StatusBadge({ status }: { status: string }) {
    const s = status.toLowerCase();
    if (s === "high") return <span className="badge-indexed bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">High</span>;
    if (s === "medium") return <span className="badge-processing bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">Medium</span>;
    return <span className="badge-failed bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Low</span>;
}

export default function RankingDashboard() {
    const [data, setData] = useState<RankingData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRanking = async () => {
            try {
                const response = await apiClient.get<{ data: RankingData }>("/intelligence/national");
                setData(response.data);
            } catch (err) {
                setError(err instanceof ApiError ? err.message : "Failed to load ranking data.");
            } finally {
                setLoading(false);
            }
        };
        fetchRanking();
    }, []);

    if (loading) {
        return (
            <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
                <div className="skeleton h-8 w-64 rounded mb-2" />
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(i => <div key={i} className="card p-5 h-28 skeleton" />)}
                </div>
                <div className="skeleton h-64 w-full rounded card" />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="card p-6 flex items-center gap-3 bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30 max-w-4xl mx-auto">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-sm font-medium text-red-700 dark:text-red-400">{error || "No data available."}</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            {/* Header & Confidence */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
                        <Trophy className="w-6 h-6 text-amber-500" /> State Ranking Dashboard
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        AI-powered governance health scoring spanning {data.total_states} states and {data.total_reports} reports.
                    </p>
                </motion.div>
                
                <div className="bg-white dark:bg-gray-900/50 card px-4 py-2 border-l-4 border-l-blue-500 max-w-md">
                    <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5" /> Intelligence Confidence
                    </p>
                    <p className="text-[11px] text-gray-500 dark:text-gray-500 mt-1 leading-snug">
                        {data.confidence_reason}
                    </p>
                </div>
            </div>

            {/* Gap Analysis & Recommendations (Top Section) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recommendations */}
                <div className="card bg-white dark:bg-gray-900/50 overflow-hidden flex flex-col">
                    <div className="bg-blue-50/50 dark:bg-blue-900/20 px-5 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
                        <Zap className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        <h2 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">Actionable Recommendations</h2>
                    </div>
                    <div className="p-5 flex-1 overflow-y-auto max-h-[300px] space-y-4">
                        {data.recommendations.map((rec, i) => (
                            <div key={i} className="flex gap-3 items-start">
                                <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5">
                                    {rec.priority}
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{rec.area}</h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{rec.recommendation}</p>
                                    <div className="mt-2 flex items-center gap-1 text-[11px] text-green-600 dark:text-green-400 font-medium bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded inline-flex">
                                        <TrendingUp className="w-3 h-3" /> {rec.expected_impact}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Gap Analysis */}
                <div className="card bg-white dark:bg-gray-900/50 overflow-hidden flex flex-col">
                    <div className="bg-amber-50/50 dark:bg-amber-900/20 px-5 py-3 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                        <h2 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider">Identified Gaps</h2>
                    </div>
                    <div className="p-4 flex-1 overflow-y-auto max-h-[300px] space-y-3">
                        {data.gap_analysis.map((gap, i) => (
                            <div key={i} className="border border-gray-100 dark:border-gray-800 rounded-lg p-3 bg-gray-50/50 dark:bg-gray-800/30">
                                <div className="flex justify-between items-start mb-1">
                                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{gap.area}</h3>
                                    <span className={
                                        gap.severity === "High" ? "text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                                        gap.severity === "Medium" ? "text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" :
                                        "text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                                    }>{gap.severity}</span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-2">{gap.description}</p>
                                <p className="text-[10px] font-mono text-gray-500 bg-white dark:bg-gray-900 px-2 py-1 rounded inline-block border border-gray-200 dark:border-gray-700">Metric: {gap.metric}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Full State Ranking Table */}
            <div className="card bg-white dark:bg-gray-900/50 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
                    <h2 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                        <MapPin className="w-4 h-4" /> Full State Ranking
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50/80 dark:bg-gray-800/50 text-xs text-gray-500 uppercase font-semibold">
                            <tr>
                                <th className="px-5 py-3 w-16 text-center">Rank</th>
                                <th className="px-5 py-3">State</th>
                                <th className="px-5 py-3">Score</th>
                                <th className="px-5 py-3">Status</th>
                                <th className="px-5 py-3 hidden md:table-cell">Breakdown (Activity / Diversity)</th>
                                <th className="px-5 py-3 hidden lg:table-cell w-1/3">Key Risk Factors</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                            {data.all_states_scores.map((s) => (
                                <tr key={s.state} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                                    <td className="px-5 py-3 text-center">
                                        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                                            s.rank <= 3 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400' : 
                                            'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                                        }`}>
                                            {s.rank}
                                        </span>
                                    </td>
                                    <td className="px-5 py-3 font-medium text-gray-900 dark:text-white">{s.state}</td>
                                    <td className="px-5 py-3">
                                        <div className="flex items-center gap-2">
                                            <span className="font-bold">{s.score.toFixed(1)}</span>
                                            <span className="text-[10px] text-gray-400">/ 10</span>
                                        </div>
                                    </td>
                                    <td className="px-5 py-3"><StatusBadge status={s.status} /></td>
                                    <td className="px-5 py-3 hidden md:table-cell">
                                        <div className="flex items-center gap-3">
                                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden" title={`Activity: ${s.breakdown.activity_level.toFixed(1)}/10`}>
                                                <div className="bg-blue-500 h-1.5" style={{ width: `${s.breakdown.activity_level * 10}%` }}></div>
                                            </div>
                                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden" title={`Diversity: ${s.breakdown.initiative_diversity.toFixed(1)}/10`}>
                                                <div className="bg-purple-500 h-1.5" style={{ width: `${s.breakdown.initiative_diversity * 10}%` }}></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-5 py-3 hidden lg:table-cell text-xs text-gray-500">
                                        {s.risk_factors.length > 0 ? (
                                            <div className="flex flex-wrap gap-1">
                                                {s.risk_factors.map((rf: string) => (
                                                    <span key={rf} className="px-1.5 py-0.5 rounded border border-red-200 bg-red-50 text-red-600 dark:bg-red-900/10 dark:border-red-900/30 dark:text-red-400">
                                                        {rf.replace(/_/g, ' ')}
                                                    </span>
                                                ))}
                                            </div>
                                        ) : (
                                            <span className="text-gray-400 italic">None detected</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
