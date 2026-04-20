"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Bot, Send, User, AlertCircle, Loader2 } from "lucide-react";

import { apiClient, ApiError } from "@/lib/utils";

type Role = "user" | "assistant";

interface Message {
    role: Role;
    content: string;
}

interface ChatApiResponse {
    data: {
        answer: string;
        metadata?: {
            latency_ms?: number;
        };
    };
}

export default function ChatPage() {
    const t = useTranslations("chat");

    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);

    const renderMessageContent = (content: string) => {
        const lines = content.split("\n").filter((line) => line.trim().length > 0);
        return (
            <div className="max-w-3xl">
                <div className="space-y-2 text-sm leading-relaxed">
                    {lines.map((line, i) => {
                        const trimmed = line.trim();
                        if (trimmed.startsWith("•")) {
                            return (
                                <ul key={i} className="list-disc ml-5">
                                    <li className="ml-4 list-disc text-gray-200">{trimmed.replace(/^•\s*/, "")}</li>
                                </ul>
                            );
                        }
                        return (
                            <p key={i} className="text-gray-200">
                                {trimmed}
                            </p>
                        );
                    })}
                </div>
            </div>
        );
    };

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        const userMessage = input.trim();
        if (!userMessage || loading) return;

        const nextMessages: Message[] = [...messages, { role: "user", content: userMessage }];
        setMessages(nextMessages);
        setInput("");
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<ChatApiResponse>("/chat", {
                message: userMessage,
                history: nextMessages.slice(-10),
            });

            const answer = response.data?.answer || t("fallback");
            setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
        } catch (err: unknown) {
            const msg = err instanceof ApiError ? err.message : t("fallback");
            setError(msg);
            setMessages((prev) => [...prev, { role: "assistant", content: msg }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="page-title">{t("title")}</h1>
                <p className="page-subtitle">{t("subtitle")}</p>
            </div>

            <div className="card p-5 space-y-4 min-h-[420px]">
                <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                    {messages.length === 0 && (
                        <div className="text-sm text-[var(--text-muted)] text-center py-16">{t("empty")}</div>
                    )}

                    {messages.map((m, idx) => (
                        <div key={idx} className={`flex gap-2 ${m.role === "assistant" ? "justify-start" : "justify-end"}`}>
                            {m.role === "assistant" && (
                                <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                                </div>
                            )}
                            <div className={`rounded-xl p-3 max-w-3xl text-sm leading-relaxed ${m.role === "assistant" ? "bg-gray-800/60 border border-gray-700" : "bg-indigo-500/20 text-white"}`}>
                                {m.role === "assistant" ? renderMessageContent(m.content) : m.content}
                            </div>
                            {m.role === "user" && (
                                <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center">
                                    <User className="w-4 h-4 text-gray-700 dark:text-gray-200" />
                                </div>
                            )}
                        </div>
                    ))}

                    {loading && (
                        <div className="text-gray-400 text-sm animate-pulse">
                            Generating response...
                        </div>
                    )}
                </div>

                {error && (
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                    </div>
                )}

                <form onSubmit={submit} className="flex gap-2 pt-1">
                    <input
                        type="text"
                        className="input-field flex-1"
                        placeholder={t("placeholder")}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        maxLength={2000}
                    />
                    <button className="btn-primary flex items-center gap-2 disabled:opacity-50" type="submit" disabled={loading || !input.trim()}>
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        {loading ? t("sending") : t("send")}
                    </button>
                </form>
            </div>
        </div>
    );
}
