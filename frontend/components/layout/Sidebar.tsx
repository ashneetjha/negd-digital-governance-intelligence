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
                    // Added ambient-glow right here! 👇
                    "ambient-glow flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group",
                    active
                        ? "text-blue-700 dark:text-blue-400 bg-blue-50/80 dark:bg-blue-900/30 shadow-sm"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200/50 dark:hover:bg-white/10"
                )}
                aria-current={active ? "page" : undefined}
            >
                <Icon className={clsx(
                    "w-4 h-4 flex-shrink-0 transition-colors duration-200",
                    active ? "text-blue-600 dark:text-blue-400" : "group-hover:text-gray-900 dark:group-hover:text-white"
                )} />
                <span className="truncate">{t(item.key as "dashboard" | "upload" | "analysis" | "compare" | "reports" | "settings")}</span>
                {active && <div className="ml-auto w-1 h-4 rounded-full bg-blue-600 dark:bg-blue-400 shadow-sm" />}
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
                    "flex flex-col border-r transition-transform duration-300 ease-out backdrop-blur-xl bg-white/60 dark:bg-gray-950/60 border-gray-200/50 dark:border-white/10",
                    "fixed top-16 left-0 z-[50] w-64 h-[calc(100vh-4rem)] shadow-2xl",
                    "lg:relative lg:top-0 lg:z-0 lg:h-screen lg:shadow-none lg:translate-x-0 lg:flex-shrink-0",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Mobile close button */}
                <div className="flex items-center justify-between p-3 lg:hidden border-b border-gray-200/50 dark:border-white/10">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Menu</span>
                    <button
                        onClick={close}
                        className="p-1 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                        aria-label="Close menu"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Main navigation">
                    <div className="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest px-3 pt-4 pb-3">Navigation</div>
                    {navItems.map((item) => (
                        <NavLink key={item.key} item={item} />
                    ))}
                </nav>

                {/* Bottom */}
                <div className="p-3 border-t border-gray-200/50 dark:border-white/10 space-y-1">
                    {bottomItems.map((item) => (
                        <NavLink key={item.key} item={item} />
                    ))}
                    <div className="px-3 pt-3 pb-2">
                        <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-relaxed font-semibold">
                            NeGD Digital Governance Intelligence Portal
                        </p>
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">IIT Ropar × NeGD</p>
                    </div>
                </div>
            </aside>
        </>
    );
}