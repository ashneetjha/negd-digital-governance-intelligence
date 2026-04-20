"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";
import { clsx } from "clsx";
import { useLocale } from "next-intl";

interface MonthYearPickerProps {
    value: string;
    onChange: (value: string) => void;
    label?: string;
    placeholder?: string;
    required?: boolean;
    id?: string;
}

const MIN_YEAR = 1947;

function buildMonthLabels(locale: string) {
    const staticMonths = [
      "Jan","Feb","Mar","Apr","May","Jun",
      "Jul","Aug","Sep","Oct","Nov","Dec"
    ];
    const fullFmt = new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", { month: "long" });
    const full: string[] = [];
    for (let i = 0; i < 12; i++) {
        const d = new Date(2020, i, 1);
        full.push(fullFmt.format(d));
    }
    return { short: staticMonths, full };
}

function parseValue(value: string): { year: number | null; monthIndex: number | null } {
    if (!value || !/^\d{4}-\d{2}$/.test(value)) {
        return { year: null, monthIndex: null };
    }
    return {
        year: Number(value.slice(0, 4)),
        monthIndex: Number(value.slice(5, 7)) - 1,
    };
}

export default function MonthYearPicker({
    value,
    onChange,
    label,
    placeholder = "Select month",
    required,
    id,
}: MonthYearPickerProps) {
    const locale = useLocale();
    const { short: monthShort, full: monthFull } = useMemo(() => buildMonthLabels(locale), [locale]);

    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
    }, []);

    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();
    const parsed = parseValue(value);

    const [open, setOpen] = useState(false);
    const [viewYear, setViewYear] = useState(parsed.year ?? currentYear);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);

    const yearOptions = useMemo(() => {
        const years: number[] = [];
        for (let y = currentYear; y >= MIN_YEAR; y--) years.push(y);
        return years;
    }, [currentYear]);

    useEffect(() => {
        const onDocClick = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", onDocClick);
        return () => document.removeEventListener("mousedown", onDocClick);
    }, []);

    useEffect(() => {
        if (!open || !panelRef.current) return;

        const focusables = panelRef.current.querySelectorAll<HTMLElement>(
            "button:not([disabled]), select:not([disabled])",
        );
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        first?.focus();

        const panel = panelRef.current;
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setOpen(false);
                return;
            }
            if (event.key === "Tab" && focusables.length > 1) {
                if (event.shiftKey && document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                    event.preventDefault();
                    first.focus();
                }
            }
        };

        panel.addEventListener("keydown", onKeyDown);
        return () => panel.removeEventListener("keydown", onKeyDown);
    }, [open]);

    const selectMonth = (monthIdx: number) => {
        const next = `${viewYear}-${String(monthIdx + 1).padStart(2, "0")}`;
        onChange(next);
        setOpen(false);
    };

    const displayValue = parsed.year != null && parsed.monthIndex != null
        ? `${monthFull[parsed.monthIndex]} ${parsed.year}`
        : "";

    const onMonthKeyNav = (event: React.KeyboardEvent<HTMLButtonElement>, monthIdx: number) => {
        const stepMap: Record<string, number> = {
            ArrowLeft: -1,
            ArrowRight: 1,
            ArrowUp: -3,
            ArrowDown: 3,
        };
        if (!(event.key in stepMap)) return;
        event.preventDefault();

        const nextIdx = monthIdx + stepMap[event.key];
        if (nextIdx < 0 || nextIdx > 11) return;

        const btn = panelRef.current?.querySelector<HTMLButtonElement>(`button[data-month-index="${nextIdx}"]`);
        btn?.focus();
    };

    if (!mounted) return null;

    return (
        <div className="relative w-full" ref={wrapperRef}>
            {label && (
                <label className="label" htmlFor={id}>
                    {label}
                </label>
            )}

            <div className="relative w-full">
                <button
                    type="button"
                    id={id}
                    onClick={() => setOpen((prev) => !prev)}
                    className={clsx("input-field flex items-center gap-2 text-left w-full", !value && "text-[var(--text-muted)]")}
                    aria-haspopup="dialog"
                    aria-expanded={open}
                >
                    <Calendar className="w-3.5 h-3.5 flex-shrink-0 text-[var(--text-muted)]" />
                    <span className="flex-1 truncate">{displayValue || placeholder}</span>
                </button>

                {open && (
                    <div className="w-full sm:w-[280px]">
                        <div
                            ref={panelRef}
                            className="absolute left-0 mt-2 w-full bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-[9999] max-h-[300px] overflow-y-auto p-3 animate-fade-in"
                            role="dialog"
                            aria-label="Month year picker"
                        >
                            <div className="flex items-center justify-between mb-3 gap-1">
                                <button
                                    type="button"
                                    onClick={() => setViewYear((prev) => prev - 1)}
                                    className="p-1 rounded-lg hover:bg-[var(--bg-surface-2)] text-[var(--text-secondary)] transition-colors"
                                    aria-label="Previous year"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>

                                <select
                                    value={viewYear}
                                    onChange={(e) => setViewYear(Number(e.target.value))}
                                    className="input-field py-1.5 px-2 text-xs font-semibold max-w-[110px]"
                                    aria-label="Select year"
                                >
                                    {yearOptions.map((year) => (
                                        <option key={year} value={year}>
                                            {year}
                                        </option>
                                    ))}
                                </select>

                                <button
                                    type="button"
                                    onClick={() => setViewYear((prev) => prev + 1)}
                                    className="p-1 rounded-lg hover:bg-[var(--bg-surface-2)] text-[var(--text-secondary)] transition-colors"
                                    aria-label="Next year"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-[200px] overflow-y-auto">
                                {monthShort.map((monthLabel, idx) => {
                                    const selected = parsed.year === viewYear && parsed.monthIndex === idx;
                                    const current = viewYear === currentYear && idx === currentMonth;

                                    return (
                                        <button
                                            key={`${monthLabel}-${idx}`}
                                            data-month-index={idx}
                                            type="button"
                                            onClick={() => selectMonth(idx)}
                                            onKeyDown={(event) => onMonthKeyNav(event, idx)}
                                            className={clsx(
                                                "px-2 py-2 rounded-lg text-xs font-medium transition-all duration-150",
                                                selected
                                                    ? "bg-[var(--accent)] text-white shadow-sm"
                                                    : current
                                                        ? "bg-[var(--accent-subtle)] text-[var(--accent)] ring-1 ring-[var(--accent)]"
                                                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-surface-2)] hover:text-[var(--text-primary)]",
                                            )}
                                        >
                                            {monthLabel}
                                        </button>
                                    );
                                })}
                            </div>

                            <div className="flex items-center gap-2 mt-3 pt-2 border-t border-[var(--bg-border)]">
                                <button
                                    type="button"
                                    className="text-2xs text-[var(--accent)] hover:underline"
                                    onClick={() => {
                                        onChange(`${currentYear}-${String(currentMonth + 1).padStart(2, "0")}`);
                                        setOpen(false);
                                    }}
                                >
                                    {locale === "hi" ? "इस महीने" : "This month"}
                                </button>
                                <span className="text-[var(--text-muted)]">·</span>
                                <button
                                    type="button"
                                    className="text-2xs text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                    onClick={() => {
                                        onChange("");
                                        setOpen(false);
                                    }}
                                >
                                    {locale === "hi" ? "साफ करें" : "Clear"}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {required && !value && (
                <input
                    tabIndex={-1}
                    className="opacity-0 absolute bottom-0 left-0 w-0 h-0"
                    required
                    value={value}
                    onChange={() => {}}
                />
            )}
        </div>
    );
}
