import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { ThemeProvider } from "next-themes";
import "../globals.css";

// Increment this string whenever the favicon asset changes.
// Browsers key their favicon cache on the full URL, so a version suffix
// forces an immediate refresh even on clients that had the old Vercel favicon
// cached from a previous deployment.
const ASSET_VERSION = "20260305";

export const metadata: Metadata = {
    metadataBase: new URL("https://negd-digital-governance-intelligence.netlify.app"),
    title: "Digital Governance Intelligence Portal | NeGD, MeitY",
    description:
        "AI-powered Governance Intelligence Portal for the National e-Governance Division (NeGD), MeitY, Government of India. Upload state reports, perform RAG-based analysis, and compare month-wise governance data.",
    keywords: ["NeGD", "MeitY", "Digital India", "Governance", "AI", "RAG", "State Reports"],
    // Explicitly declare all icon variants so Next.js generates the correct
    // <link> elements and never falls back to a vercel-default favicon.
    icons: {
        icon: [
            { url: `/icon.png?v=${ASSET_VERSION}`, type: "image/png", sizes: "any" },
        ],
        shortcut: `/icon.png?v=${ASSET_VERSION}`,
        apple: [
            { url: `/icon.png?v=${ASSET_VERSION}`, type: "image/png" },
        ],
    },
    // Prevent search-engine bots from indexing internal portal pages
    robots: { index: false, follow: false },
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
                {/* Explicit link tags override any browser-cached favicon from a
                    prior hosting provider (e.g. Vercel defaults). The ?v= suffix
                    forces cache invalidation. */}
                <link rel="icon" type="image/png" href={`/icon.png?v=${ASSET_VERSION}`} />
                <link rel="apple-touch-icon" href={`/icon.png?v=${ASSET_VERSION}`} />
                <link rel="shortcut icon" href={`/icon.png?v=${ASSET_VERSION}`} />
            </head>
            <body 
                className="min-h-screen antialiased bg-gray-50 dark:bg-gray-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-100 via-gray-50 to-white dark:from-slate-900 dark:via-gray-950 dark:to-gray-950" 
                suppressHydrationWarning
            >
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