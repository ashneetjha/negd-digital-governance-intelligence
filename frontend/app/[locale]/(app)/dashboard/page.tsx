"use client";

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Activity, FileText, MapPin, Clock, Cpu } from "lucide-react";
import { ApiError, apiClient } from "@/lib/utils";
import { animateRevealOnScroll, animateStaggerIn, initGsap } from "@/lib/animations";

interface DashboardStats {
    total_reports: number;
    indexed_reports: number;
    states_submitted: number;
    pending_states: string[];
    last_updated: string | null;
    recent_uploads: Array<{
        id: string;
        state: string;
        reporting_month: string;
        file_name: string;
        processed_status: string;
        uploaded_at: string;
    }>;
}

interface SystemStatus {
    supabase: { reachable: boolean };
    groq: { reachable: boolean };
    embedding: { loaded: boolean };
    strict_ai_mode: boolean;
    overall_status: "healthy" | "degraded";
}

function StatusBadge({ status }: { status: string }) {
    const classes: Record<string, string> = {
        indexed: "badge-indexed",
        processing: "badge-processing",
        pending: "badge-pending",
        failed: "badge-failed",
    };
    return <span className={classes[status] || "badge"}>{status}</span>;
}

function StatCard({
    icon: Icon,
    label,
    value,
}: {
    icon: React.ElementType;
    label: string;
    value: string | number;
}) {
    return (
        // Added ambient-glow right here! 👇
        <div className="ambient-glow card-hover p-4 md:p-5 bg-white dark:bg-gray-900/50">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">{label}</p>
                    <p className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mt-1 tracking-tight">{value}</p>
                </div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-50 dark:bg-blue-900/30 flex-shrink-0">
                    <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
            </div>
        </div>
    );
}
const SKELETON_WIDTHS = ["64%", "78%", "56%", "82%", "69%", "74%"];

export default function DashboardPage() {
    const t = useTranslations("dashboard");
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [attempt, setAttempt] = useState(0);

    const headerRef = useRef<HTMLDivElement>(null);
    const cardsRef = useRef<HTMLDivElement>(null);
    const tableRef = useRef<HTMLDivElement>(null);
    const pendingRef = useRef<HTMLDivElement>(null);
    const diagnosticsRef = useRef<HTMLDivElement>(null);

    const loadData = useCallback(async (withRetry = true) => {
        setLoading(true);
        setError(null);
        const maxAttempts = withRetry ? 3 : 1;
        let currentAttempt = 0;
        let lastError = "Could not load dashboard data.";

        while (currentAttempt < maxAttempts) {
            try {
                const [statsPayload, systemPayload] = await Promise.all([
                    apiClient.get<DashboardStats>("/reports/stats"),
                    apiClient.get<SystemStatus>("/system/status"),
                ]);
                setStats(statsPayload);
                setSystemStatus(systemPayload);
                setAttempt(currentAttempt + 1);
                setLoading(false);
                return;
            } catch (err: unknown) {
                currentAttempt += 1;
                setAttempt(currentAttempt);
                lastError = err instanceof ApiError ? err.message : "Could not load dashboard data.";
                if (currentAttempt < maxAttempts) {
                    const backoffMs = 500 * (2 ** (currentAttempt - 1));
                    await new Promise((resolve) => setTimeout(resolve, backoffMs));
                }
            }
        }

        setError(lastError);
        setLoading(false);
    }, []);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            void loadData(true);
        }, 0);
        return () => window.clearTimeout(timer);
    }, [loadData]);

    useEffect(() => {
        if (loading || !stats) return;
        const reduceMotion = initGsap();
        if (reduceMotion) return;

        animateStaggerIn([headerRef.current], { delay: 0.05 });
        const cardNodes = cardsRef.current ? Array.from(cardsRef.current.children) : [];
        animateStaggerIn(cardNodes, { delay: 0.12 });
        animateRevealOnScroll(tableRef.current);
        animateRevealOnScroll(pendingRef.current);
        animateRevealOnScroll(diagnosticsRef.current);
    }, [loading, stats]);

    const formatDate = (iso: string | null) => {
        if (!iso) return "—";
        return new Date(iso).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        });
    };

    const diagnostics = useMemo(() => {
        if (!systemStatus) {
            return [
                { label: "Supabase", ok: false },
                { label: "Embeddings", ok: false },
                { label: "Groq", ok: false },
            ];
        }
        return [
            { label: "Supabase", ok: systemStatus.supabase.reachable },
            { label: "Embeddings", ok: systemStatus.embedding.loaded },
            { label: "Groq", ok: systemStatus.groq.reachable },
        ];
    }, [systemStatus]);

    if (loading) {
        return (
            <div className="space-y-6">
                <div>
                    <div className="skeleton h-8 w-48 rounded mb-2" />
                    <div className="skeleton h-4 w-72 rounded" />
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="card p-5 space-y-3">
                            <div className="skeleton h-3 w-20 rounded" />
                            <div className="skeleton h-8 w-16 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error || !stats) {
        return (
            <div className="card p-6 flex flex-col sm:flex-row sm:items-center gap-3 text-gray-600 dark:text-gray-400">
                <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                    <p className="text-sm">{error || "No data available."}</p>
                </div>
                <div className="sm:ml-auto flex items-center gap-2">
                    <span className="text-xs text-gray-500">Retries: {attempt}</span>
                    <button className="btn-secondary text-xs" onClick={() => void loadData(true)}>
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            <motion.div ref={headerRef} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Operational overview of state report submissions</p>
            </motion.div>

            <div ref={cardsRef} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={FileText} label={t("totalReports")} value={stats.total_reports} />
                <StatCard icon={CheckCircle2} label={t("statesSubmitted")} value={stats.states_submitted} />
                <StatCard icon={MapPin} label={t("pendingStates")} value={stats.pending_states?.length ?? 0} />
                <StatCard icon={Clock} label={t("lastUpdated")} value={formatDate(stats.last_updated)} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div ref={tableRef} className="card col-span-1 lg:col-span-2 bg-white dark:bg-gray-900/50">
                    <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        <span className="font-semibold text-sm text-gray-900 dark:text-white">{t("recentUploads")}</span>
                    </div>

                    {(stats.recent_uploads?.length ?? 0) === 0 ? (
                        <p className="text-sm text-gray-500 p-4">{t("noReports")}</p>
                    ) : (
                        <>
                            <div className="hidden md:block overflow-x-auto">
                                <table className="w-full text-sm" role="table">
                                    <thead>
                                        <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/20">
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">State</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Month</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">File</th>
                                            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stats.recent_uploads.map((r) => (
                                            <tr key={r.id} className="border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                                <td className="px-4 py-3 text-gray-900 dark:text-white font-medium">{r.state}</td>
                                                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{r.reporting_month}</td>
                                                <td className="px-4 py-3 text-gray-500 dark:text-gray-500 truncate max-w-[220px]">{r.file_name}</td>
                                                <td className="px-4 py-3"><StatusBadge status={r.processed_status} /></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="md:hidden p-3 space-y-2">
                                {stats.recent_uploads.map((r) => (
                                    <div key={r.id} className="rounded-lg border border-gray-100 dark:border-gray-800 p-3 bg-gray-50 dark:bg-gray-800/30">
                                        <div className="flex items-center justify-between gap-2">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">{r.state}</p>
                                            <StatusBadge status={r.processed_status} />
                                        </div>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{r.reporting_month}</p>
                                        <p className="text-xs text-gray-500 mt-1 truncate">{r.file_name}</p>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                <div className="space-y-6">
                    <div ref={pendingRef} className="card bg-white dark:bg-gray-900/50">
                        <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse-dot" />
                            <span className="font-semibold text-sm text-gray-900 dark:text-white">{t("pendingStatesList")}</span>
                            <span className="ml-auto text-xs font-medium text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">{stats.pending_states?.length ?? 0}</span>
                        </div>
                        <div className="p-3 max-h-[300px] overflow-y-auto space-y-1">
                            {(stats.pending_states?.length ?? 0) === 0 ? (
                                <p className="text-sm text-gray-500 p-2 text-center">All states submitted ✓</p>
                            ) : (
                                stats.pending_states.map((state) => (
                                    <div key={state} className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                        <div className="w-1.5 h-1.5 rounded-full bg-amber-400/80 flex-shrink-0" />
                                        <span className="text-sm text-gray-700 dark:text-gray-300">{state}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <div ref={diagnosticsRef} className="card p-4 bg-white dark:bg-gray-900/50">
                        <div className="flex items-center gap-2 mb-4">
                            <Cpu className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">System Diagnostics</p>
                            <span className={systemStatus?.overall_status === "healthy" ? "badge-indexed ml-auto" : "badge-failed ml-auto"}>
                                {systemStatus?.overall_status ?? "unknown"}
                            </span>
                        </div>
                        <div className="space-y-2">
                            {diagnostics.map((item) => (
                                <div key={item.label} className="rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 px-3 py-2 flex items-center justify-between">
                                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{item.label}</span>
                                    <span className={item.ok ? "text-green-600 dark:text-green-400 text-xs font-semibold" : "text-red-500 dark:text-red-400 text-xs font-semibold"}>
                                        {item.ok ? "Healthy" : "Unavailable"}
                                    </span>
                                </div>
                            ))}
                        </div>
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-4 text-center font-mono">
                            STRICT_AI_MODE: {systemStatus?.strict_ai_mode ? "ENABLED" : "DISABLED"}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}