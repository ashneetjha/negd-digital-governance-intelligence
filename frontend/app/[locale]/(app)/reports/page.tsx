"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronRight, Trash2, X, AlertCircle, FileText, Loader2 } from "lucide-react";
import { apiClient, INDIAN_STATES } from "@/lib/utils";

interface Report {
    id: string;
    state: string;
    reporting_month: string;
    file_name: string;
    uploaded_at: string;
    processed_status: string;
    chunk_count: number;
    scheme: string | null;
}

interface ReportDetail {
    report: Report & { error_message?: string };
    chunks: Array<{ id: string; chunk_text: string; section_type: string; page_number: number; chunk_index: number }>;
    chunk_count: number;
}

function StatusBadge({ status }: { status: string }) {
    const map: Record<string, string> = {
        indexed: "badge-indexed", processing: "badge-processing", pending: "badge-pending", failed: "badge-failed",
    };
    return <span className={map[status] || "badge"}>{status}</span>;
}

export default function ReportsPage() {
    const t = useTranslations("reports");
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [stateFilter, setStateFilter] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [selected, setSelected] = useState<ReportDetail | null>(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [deleting, setDeleting] = useState<string | null>(null);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const data = await apiClient.get<{ reports: Report[] }>("/reports");
            setReports(data.reports);
        } catch {
            setReports([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { void fetchReports(); }, []);

    const openDetail = async (id: string) => {
        setLoadingDetail(true);
        try {
            const data = await apiClient.get<ReportDetail>(`/reports/${id}`);
            setSelected(data);
        } finally {
            setLoadingDetail(false);
        }
    };

    const deleteReport = async (id: string) => {
        if (!confirm(t("confirmDelete"))) return;
        setDeleting(id);
        try {
            await apiClient.delete(`/reports/${id}`);
            setReports((r) => r.filter((x) => x.id !== id));
            if (selected?.report.id === id) setSelected(null);
        } finally {
            setDeleting(null);
        }
    };

    const filtered = reports.filter((r) => {
        const q = search.toLowerCase();
        const matchSearch = !q || r.state.toLowerCase().includes(q) || r.reporting_month.includes(q) || r.file_name.toLowerCase().includes(q);
        const matchState = !stateFilter || r.state === stateFilter;
        const matchStatus = !statusFilter || r.processed_status === statusFilter;
        return matchSearch && matchState && matchStatus;
    });

    const formatDate = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

    return (
        <div className="space-y-5 animate-fade-in">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
                <div className="relative flex-1 min-w-48">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
                    <input className="input-field pl-8" placeholder={t("search")} value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
                <select className="input-field w-44" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}>
                    <option value="">All States</option>
                    {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <select className="input-field w-36" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="">All Statuses</option>
                    {["indexed", "processing", "pending", "failed"].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <button className="btn-secondary text-xs" onClick={() => void fetchReports()}>Refresh</button>
            </div>

            <motion.div className="card overflow-hidden" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                {loading ? (
                    <div className="flex items-center justify-center p-10">
                        <Loader2 className="w-5 h-5 animate-spin text-[var(--accent)]" />
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center p-10 text-[var(--text-muted)]">
                        <FileText className="w-7 h-7 mx-auto mb-3 opacity-40" />
                        <p className="text-sm">{t("noReports")}</p>
                    </div>
                ) : (
                    <>
                        <div className="md:hidden p-3 space-y-2">
                            {filtered.map((r) => (
                                <div key={r.id} className="rounded-lg border border-[var(--bg-border)] bg-[var(--bg-surface-2)] p-3">
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="text-sm font-medium text-[var(--text-primary)] truncate">{r.file_name}</p>
                                        <StatusBadge status={r.processed_status} />
                                    </div>
                                    <p className="text-xs text-[var(--text-secondary)] mt-1">{r.state}</p>
                                    <p className="text-xs text-[var(--text-muted)]">{r.reporting_month} · {formatDate(r.uploaded_at)}</p>
                                    <div className="flex items-center gap-3 mt-2">
                                        <button
                                            onClick={() => void openDetail(r.id)}
                                            className="text-xs text-[var(--accent)] hover:underline flex items-center gap-1"
                                        >
                                            {loadingDetail ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
                                            {t("viewDetails")}
                                        </button>
                                        <button
                                            onClick={() => void deleteReport(r.id)}
                                            disabled={deleting === r.id}
                                            className="text-[var(--text-muted)] hover:text-red-500 transition-colors"
                                            aria-label={t("delete")}
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="hidden md:block overflow-x-auto">
                            <table className="w-full text-sm" role="table">
                                <thead>
                                    <tr className="border-b border-[var(--bg-border)]">
                                        <th className="text-left px-4 py-3 label">{t("columns.name")}</th>
                                        <th className="text-left px-4 py-3 label">{t("columns.state")}</th>
                                        <th className="text-left px-4 py-3 label">{t("columns.month")}</th>
                                        <th className="text-left px-4 py-3 label">{t("columns.uploadDate")}</th>
                                        <th className="text-left px-4 py-3 label">{t("columns.status")}</th>
                                        <th className="text-left px-4 py-3 label">{t("columns.actions")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((r) => (
                                        <tr key={r.id} className="border-b border-[var(--bg-border)] last:border-0 hover:bg-[var(--bg-surface-2)] transition-colors">
                                            <td className="px-4 py-3 text-[var(--text-primary)] truncate max-w-[180px] font-medium">{r.file_name}</td>
                                            <td className="px-4 py-3 text-[var(--text-secondary)]">{r.state}</td>
                                            <td className="px-4 py-3 text-[var(--text-secondary)]">{r.reporting_month}</td>
                                            <td className="px-4 py-3 text-[var(--text-muted)]">{formatDate(r.uploaded_at)}</td>
                                            <td className="px-4 py-3"><StatusBadge status={r.processed_status} /></td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => void openDetail(r.id)}
                                                        className="text-xs text-[var(--accent)] hover:underline flex items-center gap-1"
                                                    >
                                                        {loadingDetail ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
                                                        {t("viewDetails")}
                                                    </button>
                                                    <button
                                                        onClick={() => void deleteReport(r.id)}
                                                        disabled={deleting === r.id}
                                                        className="text-[var(--text-muted)] hover:text-red-500 transition-colors"
                                                        aria-label={t("delete")}
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </motion.div>

            <AnimatePresence>
                {selected && (
                    <motion.div
                        className="fixed inset-y-0 right-0 w-full max-w-xl shadow-2xl z-50 flex flex-col"
                        style={{ backgroundColor: "var(--bg-surface)", borderLeft: "1px solid var(--bg-border)" }}
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "tween", duration: 0.25 }}
                    >
                        <div className="flex items-center justify-between p-4 border-b border-[var(--bg-border)]">
                            <span className="font-medium text-sm text-[var(--text-primary)]">{t("detail.title")}</span>
                            <button onClick={() => setSelected(null)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="p-4 overflow-y-auto space-y-5 flex-1">
                            <div className="space-y-2">
                                <p className="label">{t("detail.metadata")}</p>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    {[
                                        ["State", selected.report.state],
                                        ["Month", selected.report.reporting_month],
                                        ["Scheme", selected.report.scheme || "—"],
                                        ["Status", selected.report.processed_status],
                                        ["Chunks", String(selected.chunk_count)],
                                        ["Uploaded", new Date(selected.report.uploaded_at).toLocaleDateString("en-IN")],
                                    ].map(([key, val]) => (
                                        <div key={key} className="rounded-lg bg-[var(--bg-surface-2)] px-3 py-2">
                                            <p className="text-[var(--text-muted)] mb-0.5">{key}</p>
                                            <p className="font-medium text-[var(--text-primary)]">{val}</p>
                                        </div>
                                    ))}
                                </div>
                                {selected.report.error_message && (
                                    <div className="flex items-start gap-2 text-xs text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
                                        <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                                        {selected.report.error_message}
                                    </div>
                                )}
                            </div>

                            <div>
                                <p className="label mb-3">{t("detail.extractedText")} ({selected.chunk_count})</p>
                                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                                    {selected.chunks.map((chunk) => (
                                        <div key={chunk.id} className="rounded-lg bg-[var(--bg-surface-2)] p-3 text-xs">
                                            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                                <span className="font-medium text-[var(--accent)]">#{chunk.chunk_index + 1}</span>
                                                {chunk.section_type && <span className="text-[var(--text-secondary)]">§ {chunk.section_type}</span>}
                                                {chunk.page_number && <span className="text-[var(--text-muted)]">p.{chunk.page_number}</span>}
                                            </div>
                                            <p className="text-[var(--text-secondary)] leading-relaxed line-clamp-4">{chunk.chunk_text}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
