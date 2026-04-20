"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { AlertTriangle, TrendingUp, Award, Loader2, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/utils";

interface StateScore {
    state: string;
    score: number;
    status: "High" | "Medium" | "Low";
    breakdown: {
        activity_level: number;
        initiative_diversity: number;
        timeliness_score: number;
        innovation_signal: number;
    };
    risk_factors: string[];
    justification: string;
}

interface RiskAlert {
    state: string;
    risk: string;
    severity: string;
    action: string;
}

interface Trend {
    scheme: string;
    states_mentioning?: number;
    mentions?: number;
}

interface IntelligenceData {
    status: "ok" | "error" | "no_data";
    all_states_scores?: StateScore[];
    top_performers?: StateScore[];
    risk_alerts?: RiskAlert[];
    emerging_trends?: Trend[];
}

export default function IntelligenceDashboard() {
    const t = useTranslations("dashboard");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<IntelligenceData | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    const fetchIntelligence = async () => {
        setRefreshing(true);
        try {
            const response = await apiClient.get<{ data: IntelligenceData }>("/intelligence/national");
            setData(response.data);
            setError(null);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load intelligence");
        } finally {
            setRefreshing(false);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchIntelligence();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="max-w-6xl mx-auto space-y-6">
                <div className="card p-6 border border-red-200 bg-red-50 dark:bg-red-900/20">
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                        <span className="text-red-700 dark:text-red-300">{error || "Intelligence data unavailable"}</span>
                    </div>
                </div>
                <button onClick={fetchIntelligence} className="btn-primary">
                    <RefreshCw className="w-4 h-4" /> Retry
                </button>
            </div>
        );
    }

    const topPerformers = data.top_performers || [];
    const riskAlerts = data.risk_alerts || [];
    const trends = data.emerging_trends || [];

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--text-primary)]">Government Intelligence Dashboard</h1>
                    <p className="text-sm text-[var(--text-muted)] mt-1">National governance health overview and risk detection</p>
                </div>
                <button
                    onClick={fetchIntelligence}
                    className="btn-secondary flex items-center gap-2"
                    disabled={refreshing}
                >
                    <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            {/* Top States Section */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
                    <Award className="w-5 h-5 text-yellow-600" />
                    Top Performing States
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {topPerformers.length > 0 ? (
                        topPerformers.map((state) => (
                            <div key={state.state} className="card p-4 border-l-4 border-blue-500">
                                <div className="flex items-start justify-between mb-3">
                                    <div>
                                        <h3 className="font-semibold text-[var(--text-primary)]">{state.state}</h3>
                                        <p className="text-sm text-[var(--text-muted)]">Governance Health Score</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-2xl font-bold text-blue-600">{state.score.toFixed(1)}</div>
                                        <div className={`text-xs font-semibold ${
                                            state.status === "High" ? "text-green-600" : "text-yellow-600"
                                        }`}>
                                            {state.status}
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-1 text-xs mb-3">
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-muted)]">Activity:</span>
                                        <span className="font-medium">{state.breakdown.activity_level.toFixed(1)}/10</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-muted)]">Diversity:</span>
                                        <span className="font-medium">{state.breakdown.initiative_diversity.toFixed(1)}/10</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-muted)]">Timeliness:</span>
                                        <span className="font-medium">{state.breakdown.timeliness_score.toFixed(1)}/10</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--text-muted)]">Innovation:</span>
                                        <span className="font-medium">{state.breakdown.innovation_signal.toFixed(1)}/10</span>
                                    </div>
                                </div>

                                {state.risk_factors.length > 0 && (
                                    <div className="pt-2 border-t border-[var(--bg-border)]">
                                        <p className="text-xs text-[var(--text-muted)] mb-1">Watch areas:</p>
                                        <ul className="text-xs space-y-0.5">
                                            {state.risk_factors.map((risk, idx) => (
                                                <li key={idx} className="text-amber-700 dark:text-amber-300">• {risk}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="col-span-3 text-center text-[var(--text-muted)] py-8">No performance data available</div>
                    )}
                </div>
            </div>

            {/* Risk Alerts Section */}
            {riskAlerts.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-600" />
                        Risk Alerts ({riskAlerts.length})
                    </h2>
                    <div className="space-y-2">
                        {riskAlerts.map((alert, idx) => (
                            <div key={idx} className={`card p-4 border-l-4 ${
                                alert.severity === "High" ? "border-red-500 bg-red-50 dark:bg-red-900/20" : "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20"
                            }`}>
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="font-semibold text-[var(--text-primary)]">{alert.state}: {alert.risk}</p>
                                        <p className="text-sm text-[var(--text-muted)] mt-1">{alert.action}</p>
                                    </div>
                                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                                        alert.severity === "High" ? "bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-100" : "bg-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100"
                                    }`}>
                                        {alert.severity}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Trends Section */}
            {trends.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                        Emerging Developments & Initiative Adoption
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {trends.map((trend, idx) => (
                            <div key={idx} className="card p-4 border-l-4 border-green-500">
                                <h3 className="font-semibold text-[var(--text-primary)]">{trend.scheme}</h3>
                                <div className="text-2xl font-bold text-green-600 mt-2">
                                    {trend.states_mentioning || trend.mentions || 0}
                                </div>
                                <p className="text-xs text-[var(--text-muted)] mt-1">
                                    {trend.states_mentioning ? "States" : "Mentions"} tracking this
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Summary Stats */}
            <div className="card p-6 bg-[var(--bg-surface-2)]">
                <h3 className="font-semibold text-[var(--text-primary)] mb-4">System Overview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                        <div className="text-2xl font-bold text-blue-600">
                            {data.all_states_scores?.length || 0}
                        </div>
                        <p className="text-xs text-[var(--text-muted)]">States Analyzed</p>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-green-600">
                            {topPerformers.length}
                        </div>
                        <p className="text-xs text-[var(--text-muted)]">High Performers</p>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-red-600">
                            {riskAlerts.length}
                        </div>
                        <p className="text-xs text-[var(--text-muted)]">Risk Alerts</p>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-yellow-600">
                            {trends.length}
                        </div>
                        <p className="text-xs text-[var(--text-muted)]">Emerging Schemes</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
