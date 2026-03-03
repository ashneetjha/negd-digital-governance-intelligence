"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useParams, usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { Sun, Moon, Monitor, Languages, Menu } from "lucide-react";
import { useSidebar } from "./SidebarContext";

export default function Header() {
    const t = useTranslations("header");
    const { theme, setTheme } = useTheme();
    const params = useParams();
    const pathname = usePathname();
    const router = useRouter();
    const locale = (params?.locale as string) || "en";
    const { toggle } = useSidebar();

    const toggleLanguage = () => {
        const newLocale = locale === "en" ? "hi" : "en";
        const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
        router.push(newPath);
    };

    const cycleTheme = () => {
        if (theme === "light") setTheme("dark");
        else if (theme === "dark") setTheme("system");
        else setTheme("light");
    };

    const resolvedTheme = theme ?? "system";
    const ThemeIcon = resolvedTheme === "light" ? Sun : resolvedTheme === "dark" ? Moon : Monitor;

    return (
        <header
            className="sticky top-0 z-50 flex items-center gap-3 px-4 h-14"
            style={{ backgroundColor: "var(--header-bg)", color: "var(--header-text)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}
        >
            <button
                onClick={toggle}
                className="lg:hidden p-1.5 -ml-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                aria-label="Toggle menu"
            >
                <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 flex-1 min-w-0">
                <div className="h-8 w-8 rounded bg-white/90 p-1 hidden sm:flex items-center justify-center">
                    <Image
                        src="/Ministry_of_Electronics_and_Information_Technology_Logo.png"
                        alt="Ministry of Electronics and Information Technology"
                        width={26}
                        height={26}
                        className="object-contain"
                    />
                </div>
                <div className="h-8 w-8 rounded bg-white/90 p-1 flex items-center justify-center">
                    <Image
                        src="/NeGD_Logo.png"
                        alt="National e-Governance Division"
                        width={26}
                        height={26}
                        className="object-contain"
                    />
                </div>
                <div className="w-px h-7 bg-white/20 flex-shrink-0 hidden sm:block" />
                <div className="h-8 w-8 rounded bg-white/90 p-1 hidden sm:flex items-center justify-center">
                    <Image
                        src="/IIT_RPR_Logo.png"
                        alt="IIT Ropar"
                        width={24}
                        height={24}
                        className="object-contain"
                    />
                </div>
                <div className="w-px h-7 bg-white/20 flex-shrink-0 hidden md:block" />

                <div className="min-w-0 hidden md:block">
                    <p className="text-white font-semibold text-sm leading-tight truncate">{t("title")}</p>
                    <p className="text-white/55 text-[10px] leading-tight truncate hidden lg:block">{t("subtitle")}</p>
                </div>
                <div className="min-w-0 md:hidden">
                    <p className="text-white font-semibold text-xs leading-tight truncate">DGIP</p>
                </div>
            </div>

            <div className="flex items-center gap-1 flex-shrink-0">
                <button
                    onClick={toggleLanguage}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                    aria-label="Toggle language"
                    title={locale === "en" ? "Switch to Hindi" : "Switch to English"}
                >
                    <Languages className="w-3.5 h-3.5" />
                    <span>{locale === "en" ? "हिं" : "EN"}</span>
                </button>

                <button
                    onClick={cycleTheme}
                    className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                    aria-label="Toggle theme"
                    title={`Current theme: ${resolvedTheme}`}
                >
                    <ThemeIcon className="w-4 h-4" />
                </button>
            </div>
        </header>
    );
}
