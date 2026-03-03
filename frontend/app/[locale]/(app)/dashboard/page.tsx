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
        <div className="card-hover p-4 md:p-5">
            <div className="flex items-start justify-between">
                <div>
                    <p className="label">{label}</p>
                    <p className="text-xl md:text-2xl font-semibold text-[var(--text-primary)] mt-1">{value}</p>
                </div>
                <div className="stat-icon-bg">
                    <Icon className="w-4.5 h-4.5 text-[var(--accent)]" />
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
                    <div className="skeleton h-6 w-28 rounded mb-2" />
                    <div className="skeleton h-4 w-72 rounded" />
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="card p-5 space-y-3">
                            <div className="skeleton h-3 w-20 rounded" />
                            <div className="skeleton h-7 w-14 rounded" />
                        </div>
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="card p-4 col-span-1 lg:col-span-2 space-y-3">
                        <div className="skeleton h-4 w-32 rounded" />
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="skeleton h-3 rounded" style={{ width: SKELETON_WIDTHS[i % SKELETON_WIDTHS.length] }} />
                        ))}
                    </div>
                    <div className="card p-4 space-y-3">
                        <div className="skeleton h-4 w-32 rounded" />
                        {[...Array(6)].map((_, i) => (
                            <div key={i} className="skeleton h-3 rounded" style={{ width: SKELETON_WIDTHS[(i + 2) % SKELETON_WIDTHS.length] }} />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (error || !stats) {
        return (
            <div className="card p-6 flex flex-col sm:flex-row sm:items-center gap-3 text-[var(--text-secondary)]">
                <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                    <p className="text-sm">{error || "No data available."}</p>
                </div>
                <div className="sm:ml-auto flex items-center gap-2">
                    <span className="text-xs text-[var(--text-muted)]">Retries: {attempt}</span>
                    <button className="btn-secondary text-xs" onClick={() => void loadData(true)}>
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <motion.div ref={headerRef} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">Operational overview of state report submissions</p>
            </motion.div>

            <div ref={cardsRef} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={FileText} label={t("totalReports")} value={stats.total_reports} />
                <StatCard icon={CheckCircle2} label={t("statesSubmitted")} value={stats.states_submitted} />
                <StatCard icon={MapPin} label={t("pendingStates")} value={stats.pending_states?.length ?? 0} />
                <StatCard icon={Clock} label={t("lastUpdated")} value={formatDate(stats.last_updated)} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div ref={tableRef} className="card col-span-1 lg:col-span-2">
                    <div className="p-4 border-b border-[var(--bg-border)] flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[var(--accent)]" />
                        <span className="font-medium text-sm text-[var(--text-primary)]">{t("recentUploads")}</span>
                    </div>

                    {(stats.recent_uploads?.length ?? 0) === 0 ? (
                        <p className="text-sm text-[var(--text-muted)] p-4">{t("noReports")}</p>
                    ) : (
                        <>
                            <div className="hidden md:block overflow-x-auto">
                                <table className="w-full text-sm" role="table">
                                    <thead>
                                        <tr className="border-b border-[var(--bg-border)]">
                                            <th className="text-left px-4 py-2.5 label">State</th>
                                            <th className="text-left px-4 py-2.5 label">Month</th>
                                            <th className="text-left px-4 py-2.5 label">File</th>
                                            <th className="text-left px-4 py-2.5 label">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stats.recent_uploads.map((r) => (
                                            <tr key={r.id} className="border-b border-[var(--bg-border)] last:border-0 hover:bg-[var(--bg-surface-2)] transition-colors">
                                                <td className="px-4 py-2.5 text-[var(--text-primary)] font-medium">{r.state}</td>
                                                <td className="px-4 py-2.5 text-[var(--text-secondary)]">{r.reporting_month}</td>
                                                <td className="px-4 py-2.5 text-[var(--text-muted)] truncate max-w-[220px]">{r.file_name}</td>
                                                <td className="px-4 py-2.5"><StatusBadge status={r.processed_status} /></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="md:hidden p-3 space-y-2">
                                {stats.recent_uploads.map((r) => (
                                    <div key={r.id} className="rounded-lg border border-[var(--bg-border)] p-3 bg-[var(--bg-surface-2)]">
                                        <div className="flex items-center justify-between gap-2">
                                            <p className="text-sm font-medium text-[var(--text-primary)]">{r.state}</p>
                                            <StatusBadge status={r.processed_status} />
                                        </div>
                                        <p className="text-xs text-[var(--text-secondary)] mt-1">{r.reporting_month}</p>
                                        <p className="text-xs text-[var(--text-muted)] mt-1 truncate">{r.file_name}</p>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                <div ref={pendingRef} className="card">
                    <div className="p-4 border-b border-[var(--bg-border)] flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse-dot" />
                        <span className="font-medium text-sm text-[var(--text-primary)]">{t("pendingStatesList")}</span>
                        <span className="ml-auto text-xs text-[var(--text-muted)]">{stats.pending_states?.length ?? 0}</span>
                    </div>
                    <div className="p-3 max-h-64 overflow-y-auto space-y-1">
                        {(stats.pending_states?.length ?? 0) === 0 ? (
                            <p className="text-sm text-[var(--text-muted)] p-1">All states submitted ✓</p>
                        ) : (
                            stats.pending_states.map((state) => (
                                <div key={state} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-[var(--bg-surface-2)] transition-colors">
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                                    <span className="text-xs text-[var(--text-secondary)]">{state}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <div ref={diagnosticsRef} className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Cpu className="w-4 h-4 text-[var(--accent)]" />
                    <p className="text-sm font-medium text-[var(--text-primary)]">System Diagnostics</p>
                    <span className={systemStatus?.overall_status === "healthy" ? "badge-indexed ml-auto" : "badge-failed ml-auto"}>
                        {systemStatus?.overall_status ?? "unknown"}
                    </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {diagnostics.map((item) => (
                        <div key={item.label} className="rounded-lg border border-[var(--bg-border)] px-3 py-2 flex items-center justify-between">
                            <span className="text-xs text-[var(--text-secondary)]">{item.label}</span>
                            <span className={item.ok ? "text-green-600 text-xs font-medium" : "text-red-500 text-xs font-medium"}>
                                {item.ok ? "Healthy" : "Unavailable"}
                            </span>
                        </div>
                    ))}
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-3">
                    Strict AI mode: {systemStatus?.strict_ai_mode ? "ON" : "OFF"}
                </p>
            </div>
        </div>
    );
}
