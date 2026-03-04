import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Digital Governance Intelligence Portal | NeGD, MeitY",
    description: "AI-powered Governance Intelligence Portal for the National e-Governance Division (NeGD), MeitY.",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    // We only pass children here. The <html> and <body> tags are handled in app/[locale]/layout.tsx
    return children; 
}