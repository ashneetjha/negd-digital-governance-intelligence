"use client";

import { useTranslations } from "next-intl";
import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload as UploadIcon, File, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { clsx } from "clsx";
import { INDIAN_STATES, getApiBase } from "@/lib/utils";
import MonthYearPicker from "@/components/ui/MonthYearPicker";

const API_BASE = getApiBase();

type UploadStatus = "idle" | "uploading" | "success" | "error";

export default function UploadPage() {
    const t = useTranslations("upload");
    const [file, setFile] = useState<File | null>(null);
    const [state, setState] = useState("");
    const [month, setMonth] = useState("");
    const [scheme, setScheme] = useState("");
    const [status, setStatus] = useState<UploadStatus>("idle");
    const [message, setMessage] = useState("");
    const [dragOver, setDragOver] = useState(false);
    const [reportId, setReportId] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped && (dropped.type === "application/pdf" || dropped.name.endsWith(".docx"))) {
            setFile(dropped);
        }
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !state || !month) {
            setMessage(t("required"));
            return;
        }

        setStatus("uploading");
        setMessage("");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("state", state);
        formData.append("reporting_month", month);
        if (scheme) formData.append("scheme", scheme);

        try {
            const res = await fetch(`${API_BASE}/api/ingest`, {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Upload failed.");
            }
            const data = await res.json();
            setReportId(data.report_id);
            setStatus("success");
            setMessage(t("success"));
            setFile(null);
            setState("");
            setMonth("");
            setScheme("");
        } catch (err: unknown) {
            setStatus("error");
            setMessage(err instanceof Error ? err.message : t("error"));
        }
    };

    return (
        <div className="max-w-2xl space-y-6 animate-fade-in">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <motion.form
                className="card p-6 space-y-5"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                {/* File Dropzone */}
                <div>
                    <label className="label">Document</label>
                    <div
                        className={clsx(
                            "relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
                            dragOver
                                ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                                : file
                                    ? "border-green-400 bg-green-50 dark:bg-green-900/10"
                                    : "border-[var(--bg-border)] hover:border-[var(--accent)] hover:bg-[var(--accent-subtle)]"
                        )}
                        onDrop={handleDrop}
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf,.docx"
                            className="hidden"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                        />
                        {file ? (
                            <div className="flex items-center justify-center gap-3">
                                <File className="w-6 h-6 text-green-600" />
                                <div className="text-left">
                                    <p className="text-sm font-medium text-[var(--text-primary)]">{file.name}</p>
                                    <p className="text-xs text-[var(--text-muted)]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                    className="ml-4 text-[var(--text-muted)] hover:text-red-500 transition-colors"
                                    aria-label="Remove file"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <UploadIcon className="w-8 h-8 text-[var(--text-muted)] mx-auto" />
                                <p className="text-sm text-[var(--text-secondary)]">{t("dragDrop")}</p>
                                <p className="text-xs text-[var(--text-muted)]">{t("fileTypes")}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* State & Month */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="label" htmlFor="state-select">{t("selectState")}</label>
                        <select
                            id="state-select"
                            className="input-field"
                            value={state}
                            onChange={(e) => setState(e.target.value)}
                            required
                        >
                            <option value="">— Select State / UT —</option>
                            {INDIAN_STATES.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <MonthYearPicker
                            id="month-select"
                            label={t("selectMonth")}
                            value={month}
                            onChange={setMonth}
                            placeholder="— Select Month —"
                            required
                        />
                    </div>
                </div>

                {/* Scheme (optional) */}
                <div>
                    <label className="label" htmlFor="scheme-input">{t("scheme")}</label>
                    <input
                        id="scheme-input"
                        type="text"
                        className="input-field"
                        placeholder={t("schemePlaceholder")}
                        value={scheme}
                        onChange={(e) => setScheme(e.target.value)}
                    />
                </div>

                {/* Submit */}
                <div className="flex items-center gap-4 pt-1">
                    <button
                        type="submit"
                        className="btn-primary flex items-center gap-2"
                        disabled={status === "uploading"}
                    >
                        {status === "uploading" ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> {t("uploading")}</>
                        ) : (
                            <><UploadIcon className="w-4 h-4" /> {t("submit")}</>
                        )}
                    </button>

                    {/* Status message */}
                    {message && (
                        <div className={clsx("flex items-center gap-2 text-sm", status === "success" ? "text-green-600" : "text-red-500")}>
                            {status === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                            {message}
                        </div>
                    )}
                </div>
            </motion.form>

            {/* Report ID after success */}
            {reportId && (
                <motion.div
                    className="card p-4 bg-[var(--accent-subtle)] border-[var(--accent)]"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <p className="text-xs text-[var(--text-secondary)]">Report ID (for tracking)</p>
                    <p className="text-sm font-mono text-[var(--text-primary)] mt-1 break-all">{reportId}</p>
                    <p className="text-xs text-[var(--text-muted)] mt-2">
                        The report is being processed in the background. Check the Reports page for indexing status.
                    </p>
                </motion.div>
            )}
        </div>
    );
}
