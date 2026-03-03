/**
 * Shared utilities: API client, constants, and helper functions.
 */

const DEFAULT_API_URL = "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 12000;

function resolveApiBase(rawBase: string | undefined): string {
    const base = (rawBase || DEFAULT_API_URL).trim().replace(/\/+$/, "");
    return base.endsWith("/api") ? base.slice(0, -4) : base;
}

const API_BASE = resolveApiBase(process.env.NEXT_PUBLIC_API_URL);

export class ApiError extends Error {
    status?: number;
    code?: string;
    constructor(message: string, status?: number, code?: string) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.code = code;
    }
}

function parseError(payload: unknown, fallback: string): { message: string; code?: string } {
    if (
        payload &&
        typeof payload === "object" &&
        "detail" in payload
    ) {
        const detail = (payload as { detail?: unknown }).detail;
        if (typeof detail === "string") {
            return { message: detail };
        }
        if (detail && typeof detail === "object") {
            const obj = detail as { message?: string; code?: string };
            return {
                message: obj.message || fallback,
                code: obj.code,
            };
        }
    }
    return { message: fallback };
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
        const res = await fetch(`${API_BASE}/api${path}`, {
            method,
            headers: body ? { "Content-Type": "application/json" } : undefined,
            body: body ? JSON.stringify(body) : undefined,
            signal: controller.signal,
        });

        let payload: unknown = null;
        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            payload = await res.json();
        }

        if (!res.ok) {
            const parsed = parseError(payload, `HTTP ${res.status}`);
            throw new ApiError(parsed.message, res.status, parsed.code);
        }

        return payload as T;
    } catch (error: unknown) {
        if (error instanceof ApiError) {
            throw error;
        }
        if (error instanceof DOMException && error.name === "AbortError") {
            throw new ApiError("Request timed out. Please retry.");
        }
        throw new ApiError(
            error instanceof Error ? error.message : "Unknown request failure.",
        );
    } finally {
        clearTimeout(timeoutId);
    }
}

export const apiClient = {
    get: <T>(path: string) => request<T>("GET", path),
    post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
    delete: <T>(path: string) => request<T>("DELETE", path),
};

export const INDIAN_STATES: string[] = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
];

function generateMonths(): Array<{ value: string; label: string }> {
    const months: Array<{ value: string; label: string }> = [];
    const now = new Date();
    for (let i = 0; i < 24; i++) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
        const label = d.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
        months.push({ value, label });
    }
    return months;
}

export const MONTHS = generateMonths();

export function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
    return classes.filter(Boolean).join(" ");
}

export function getApiBase(): string {
    return API_BASE;
}
