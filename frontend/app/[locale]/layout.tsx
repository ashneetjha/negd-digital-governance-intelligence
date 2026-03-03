import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { ThemeProvider } from "next-themes";
import "../globals.css";

export const metadata: Metadata = {
    title: "Digital Governance Intelligence Portal | NeGD, MeitY",
    description:
        "AI-powered Governance Intelligence Portal for the National e-Governance Division (NeGD), MeitY, Government of India. Upload state reports, perform RAG-based analysis, and compare month-wise governance data.",
    keywords: ["NeGD", "MeitY", "Digital India", "Governance", "AI", "RAG", "State Reports"],
};

export default async function RootLayout({
    children,
    params,
}: {
    children: React.ReactNode;
    params: Promise<{ locale: string }>;
}) {
    const { locale } = await params;
    const messages = await getMessages();

    return (
        <html lang={locale} suppressHydrationWarning>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="icon" href="/favicon.ico" />
            </head>
            <body className="min-h-screen" suppressHydrationWarning>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange={false}
                    storageKey="negd-theme"
                >
                    <NextIntlClientProvider messages={messages}>
                        {children}
                    </NextIntlClientProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
