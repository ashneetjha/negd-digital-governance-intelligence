"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronRight, Trash2, X, AlertCircle, FileText, Loader2, RefreshCw } from "lucide-react";
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
        <div className="max-w-7xl mx-auto space-y-6 animate-fade-in relative">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("subtitle")}</p>
            </div>

            <div className="flex flex-col sm:flex-row flex-wrap items-center gap-3">
                <div className="relative flex-1 w-full sm:min-w-[250px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input 
                        className="input-field pl-9 bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800 w-full" 
                        placeholder={t("search")} 
                        value={search} 
                        onChange={(e) => setSearch(e.target.value)} 
                    />
                </div>
                <div className="flex w-full sm:w-auto gap-3">
                    <select 
                        className="input-field w-full sm:w-44 bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800" 
                        value={stateFilter} 
                        onChange={(e) => setStateFilter(e.target.value)}
                    >
                        <option value="">All States</option>
                        {INDIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select 
                        className="input-field w-full sm:w-40 bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800" 
                        value={statusFilter} 
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="">All Statuses</option>
                        {["indexed", "processing", "pending", "failed"].map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <button 
                        className="ambient-glow bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 text-gray-700 dark:text-gray-300 font-medium text-xs py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm" 
                        onClick={() => void fetchReports()}
                    >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                </div>
            </div>

            <motion.div className="card overflow-hidden bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                {loading ? (
                    <div className="flex items-center justify-center p-12">
                        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center p-12 text-gray-500 dark:text-gray-400">
                        <FileText className="w-10 h-10 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                        <p className="text-sm font-medium">{t("noReports")}</p>
                    </div>
                ) : (
                    <>
                        <div className="md:hidden p-4 space-y-3">
                            {filtered.map((r) => (
                                <div key={r.id} className="rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/30 p-4 shadow-sm">
                                    <div className="flex items-start justify-between gap-3 mb-2">
                                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{r.file_name}</p>
                                        <div className="flex-shrink-0"><StatusBadge status={r.processed_status} /></div>
                                    </div>
                                    <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">{r.state}</p>
                                    <p className="text-xs text-gray-500 mt-1">{r.reporting_month} · {formatDate(r.uploaded_at)}</p>
                                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-200 dark:border-gray-700/50">
                                        <button
                                            onClick={() => void openDetail(r.id)}
                                            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 flex items-center gap-1.5 transition-colors"
                                        >
                                            {loadingDetail ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                            {t("viewDetails")}
                                        </button>
                                        <button
                                            onClick={() => void deleteReport(r.id)}
                                            disabled={deleting === r.id}
                                            className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors p-1"
                                            aria-label={t("delete")}
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="hidden md:block overflow-x-auto">
                            <table className="w-full text-sm" role="table">
                                <thead>
                                    <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/20">
                                        <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.name")}</th>
                                        <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.state")}</th>
                                        <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.month")}</th>
                                        <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.uploadDate")}</th>
                                        <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.status")}</th>
                                        <th className="text-right px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("columns.actions")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((r) => (
                                        <tr key={r.id} className="border-b border-gray-50 dark:border-gray-800/50 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors group">
                                            <td className="px-5 py-3.5 text-gray-900 dark:text-white truncate max-w-[200px] font-medium">{r.file_name}</td>
                                            <td className="px-5 py-3.5 text-gray-600 dark:text-gray-300">{r.state}</td>
                                            <td className="px-5 py-3.5 text-gray-600 dark:text-gray-300 font-mono text-xs">{r.reporting_month}</td>
                                            <td className="px-5 py-3.5 text-gray-500 dark:text-gray-500">{formatDate(r.uploaded_at)}</td>
                                            <td className="px-5 py-3.5"><StatusBadge status={r.processed_status} /></td>
                                            <td className="px-5 py-3.5">
                                                <div className="flex items-center justify-end gap-3 opacity-80 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => void openDetail(r.id)}
                                                        className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 bg-blue-50 dark:bg-blue-900/20 px-2.5 py-1.5 rounded-md flex items-center gap-1.5 transition-colors"
                                                    >
                                                        {loadingDetail ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                                        Details
                                                    </button>
                                                    <button
                                                        onClick={() => void deleteReport(r.id)}
                                                        disabled={deleting === r.id}
                                                        className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 p-1.5 rounded-md transition-colors"
                                                        aria-label={t("delete")}
                                                    >
                                                        <Trash2 className="w-4 h-4" />
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

            {/* Slide-out Report Detail Panel */}
            <AnimatePresence>
                {selected && (
                    <>
                        <motion.div 
                            className="fixed inset-0 z-40 bg-black/20 dark:bg-black/40 backdrop-blur-sm"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelected(null)}
                        />
                        <motion.div
                            className="fixed inset-y-0 right-0 w-full max-w-xl shadow-2xl z-50 flex flex-col backdrop-blur-2xl bg-white/95 dark:bg-gray-950/95 border-l border-gray-200/50 dark:border-gray-800/50"
                            initial={{ x: "100%" }}
                            animate={{ x: 0 }}
                            exit={{ x: "100%" }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        >
                            <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50">
                                <span className="font-bold text-lg text-gray-900 dark:text-white tracking-tight">{t("detail.title")}</span>
                                <button onClick={() => setSelected(null)} className="p-2 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-white dark:hover:bg-gray-800 transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="p-5 overflow-y-auto space-y-6 flex-1 scroll-smooth">
                                <div className="space-y-3">
                                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("detail.metadata")}</p>
                                    <div className="grid grid-cols-2 gap-3 text-xs">
                                        {[
                                            ["State", selected.report.state],
                                            ["Month", selected.report.reporting_month],
                                            ["Scheme", selected.report.scheme || "—"],
                                            ["Status", selected.report.processed_status],
                                            ["Chunks", String(selected.chunk_count)],
                                            ["Uploaded", new Date(selected.report.uploaded_at).toLocaleDateString("en-IN")],
                                        ].map(([key, val]) => (
                                            <div key={key} className="rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 px-4 py-3">
                                                <p className="text-gray-500 dark:text-gray-400 mb-1">{key}</p>
                                                <p className="font-semibold text-sm text-gray-900 dark:text-white">{val}</p>
                                            </div>
                                        ))}
                                    </div>
                                    {selected.report.error_message && (
                                        <div className="flex items-start gap-2.5 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-xl p-4 mt-2">
                                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                            <span className="font-medium">{selected.report.error_message}</span>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{t("detail.extractedText")}</p>
                                        <span className="text-xs font-mono bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full">{selected.chunk_count} Chunks</span>
                                    </div>
                                    <div className="space-y-3">
                                        {selected.chunks.map((chunk) => (
                                            <div key={chunk.id} className="rounded-xl bg-white dark:bg-gray-900/40 border border-gray-100 dark:border-gray-800 p-4 text-xs shadow-sm hover:shadow-md transition-shadow">
                                                <div className="flex items-center gap-2 mb-2.5 flex-wrap">
                                                    <span className="font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded">#{chunk.chunk_index + 1}</span>
                                                    {chunk.section_type && <span className="font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">§ {chunk.section_type}</span>}
                                                    {chunk.page_number && <span className="text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">p.{chunk.page_number}</span>}
                                                </div>
                                                <p className="text-gray-700 dark:text-gray-300 leading-relaxed sm:text-sm">{chunk.chunk_text}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}