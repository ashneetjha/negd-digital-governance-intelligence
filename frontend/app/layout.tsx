import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Digital Governance Intelligence Portal | NeGD, MeitY",
  description:
    "AI-powered Governance Intelligence Portal — National e-Governance Division (NeGD), MeitY, Government of India.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
