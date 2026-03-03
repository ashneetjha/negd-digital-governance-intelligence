"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useParams, usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Upload,
    Search,
    GitCompare,
    FileText,
    Settings,
    X,
} from "lucide-react";
import { clsx } from "clsx";
import { useSidebar } from "./SidebarContext";

const navItems = [
    { key: "dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { key: "upload", icon: Upload, href: "/upload" },
    { key: "analysis", icon: Search, href: "/analysis" },
    { key: "compare", icon: GitCompare, href: "/compare" },
    { key: "reports", icon: FileText, href: "/reports" },
];

const bottomItems = [
    { key: "settings", icon: Settings, href: "/settings" },
];

export default function Sidebar() {
    const t = useTranslations("nav");
    const pathname = usePathname();
    const params = useParams();
    const locale = (params?.locale as string) || "en";
    const { isOpen, close } = useSidebar();

    const isActive = (href: string) => pathname.includes(href);

    const NavLink = ({ item }: { item: typeof navItems[0] }) => {
        const active = isActive(item.href);
        const Icon = item.icon;
        return (
            <Link
                href={`/${locale}${item.href}`}
                onClick={close}
                className={clsx(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group",
                    active
                        ? "text-[var(--sidebar-active-text)] bg-[var(--sidebar-active)]"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-2)]"
                )}
                aria-current={active ? "page" : undefined}
            >
                <Icon className={clsx(
                    "w-4 h-4 flex-shrink-0 transition-colors duration-200",
                    active ? "text-[var(--accent)]" : "group-hover:text-[var(--text-primary)]"
                )} />
                <span className="truncate">{t(item.key as "dashboard" | "upload" | "analysis" | "compare" | "reports" | "settings")}</span>
                {active && <div className="ml-auto w-1 h-4 rounded-full bg-[var(--accent)]" />}
            </Link>
        );
    };

    return (
        <>
            {/* Mobile overlay */}
            {isOpen && (
                <div
                    className="sidebar-overlay lg:hidden"
                    onClick={close}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar */}
            <aside
                className={clsx(
                    "flex flex-col border-r h-[calc(100vh-3.5rem)] overflow-y-auto transition-transform duration-300 ease-out",
                    // Desktop: always visible
                    "lg:relative lg:translate-x-0 lg:w-56 lg:flex-shrink-0",
                    // Mobile: sliding drawer
                    "fixed top-14 left-0 z-50 w-64",
                    isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
                )}
                style={{
                    backgroundColor: "var(--sidebar-bg)",
                    borderColor: "var(--sidebar-border)",
                }}
            >
                {/* Mobile close button */}
                <div className="flex items-center justify-between p-3 lg:hidden border-b border-[var(--sidebar-border)]">
                    <span className="text-sm font-medium text-[var(--text-primary)]">Menu</span>
                    <button
                        onClick={close}
                        className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-2)] transition-colors"
                        aria-label="Close menu"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-0.5" aria-label="Main navigation">
                    <div className="section-label px-3 pt-2 pb-3">Navigation</div>
                    {navItems.map((item) => (
                        <NavLink key={item.key} item={item} />
                    ))}
                </nav>

                {/* Bottom */}
                <div className="p-3 border-t border-[var(--sidebar-border)] space-y-0.5">
                    {bottomItems.map((item) => (
                        <NavLink key={item.key} item={item} />
                    ))}
                    <div className="px-3 pt-3 pb-1">
                        <p className="text-2xs text-[var(--text-muted)] leading-relaxed">
                            NeGD Digital Governance Intelligence Portal
                        </p>
                        <p className="text-2xs text-[var(--text-muted)]">v1.0 · IIT Ropar × NeGD</p>
                    </div>
                </div>
            </aside>
        </>
    );
}
