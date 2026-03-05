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
        // Added mx-auto here to perfectly center the container!
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{t("title")}</h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("subtitle")}</p>
            </div>

            <motion.form
                className="card p-6 space-y-5 bg-white dark:bg-gray-900/50 border-gray-100 dark:border-gray-800"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
            >
                {/* File Dropzone */}
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5 block">Document</label>
                    <div
                        className={clsx(
                            "relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors duration-200",
                            dragOver
                                ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                                : file
                                    ? "border-green-400 bg-green-50 dark:bg-green-900/10"
                                    : "border-gray-300 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-900/10"
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
                                <File className="w-6 h-6 text-green-500 dark:text-green-400" />
                                <div className="text-left">
                                    <p className="text-sm font-medium text-gray-900 dark:text-white">{file.name}</p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                    className="ml-4 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                                    aria-label="Remove file"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <UploadIcon className="w-8 h-8 text-gray-400 dark:text-gray-500 mx-auto" />
                                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">{t("dragDrop")}</p>
                                <p className="text-xs text-gray-400 dark:text-gray-500">{t("fileTypes")}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* State & Month */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5 block" htmlFor="state-select">{t("selectState")}</label>
                        <select
                            id="state-select"
                            className="input-field bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800"
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
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5 block" htmlFor="scheme-input">{t("scheme")}</label>
                    <input
                        id="scheme-input"
                        type="text"
                        className="input-field bg-white dark:bg-gray-950/50 border-gray-200 dark:border-gray-800"
                        placeholder={t("schemePlaceholder")}
                        value={scheme}
                        onChange={(e) => setScheme(e.target.value)}
                    />
                </div>

                {/* Submit */}
                <div className="flex items-center gap-4 pt-2">
                    {/* 👇 ambient-glow makes the upload button pop! */}
                    <button
                        type="submit"
                        className="ambient-glow btn-primary flex items-center gap-2"
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
                        <div className={clsx("flex items-center gap-2 text-sm font-medium", status === "success" ? "text-green-600 dark:text-green-400" : "text-red-500 dark:text-red-400")}>
                            {status === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                            {message}
                        </div>
                    )}
                </div>
            </motion.form>

            {/* Report ID after success */}
            {reportId && (
                <motion.div
                    className="card p-5 bg-blue-50/50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-900/30"
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">Report ID (for tracking)</p>
                    <p className="text-sm font-mono text-gray-900 dark:text-white mt-1.5 break-all">{reportId}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                        The report is being processed in the background. Check the Reports page for indexing status.
                    </p>
                </motion.div>
            )}
        </div>
    );
}