"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useParams, usePathname, useRouter } from "next/navigation";
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
        <header className="sticky top-0 z-[60] flex items-center justify-between px-4 h-16 
            backdrop-blur-2xl bg-white/80 
            dark:bg-indigo-950/40 border-b border-gray-200/50 
            dark:border-indigo-500/20 shadow-[0_4px_30px_rgba(0,0,0,0.1)] transition-all duration-500">
            
            {/* Left Section: Mobile Menu Toggle */}
            <div className="flex items-center justify-start w-auto sm:w-[120px] lg:w-[150px] flex-shrink-0">
                <button
                    onClick={toggle}
                    className="lg:hidden p-2 rounded-xl text-gray-700 dark:text-indigo-200 
                        hover:bg-gray-200/50 dark:hover:bg-indigo-500/20 transition-all"
                    aria-label="Toggle menu"
                >
                    <Menu className="w-6 h-6" />
                </button>
            </div>

            {/* Center Section: Symmetrical Logos and Stylized Title */}
            <div className="flex flex-1 items-center justify-center min-w-0 px-2 gap-4 lg:gap-10">
                
                {/* Branding Side (Hidden on smaller mobile) */}
                <div className="hidden md:flex items-center gap-5 lg:gap-7">
                    <img
                        src="/Ministry_of_Electronics_and_Information_Technology_Logo.png"
                        alt="MeitY"
                        className="h-7 lg:h-8 w-auto object-contain dark:brightness-110 dark:drop-shadow-[0_0_8px_rgba(255,255,255,0.3)] transition-all"
                    />
                    <img
                        src="/NeGD_Logo.png"
                        alt="NeGD"
                        className="h-7 lg:h-8 w-auto object-contain dark:brightness-125 dark:drop-shadow-[0_0_10px_rgba(255,255,255,0.4)]
                        border-l border-gray-200/50 dark:border-indigo-500/30 pl-5"
                    />
                </div>

                {/* Dead Center: Stylized Title */}
                <div className="flex flex-col items-center text-center px-2">
                    <h1 className="hidden sm:block text-gray-900 dark:text-transparent dark:bg-clip-text 
                        dark:bg-gradient-to-r dark:from-white dark:to-indigo-200 
                        font-extrabold text-sm md:text-base lg:text-lg xl:text-xl 
                        tracking-tight uppercase transition-all duration-300">
                        Digital Governance <span className="dark:text-indigo-400">Intelligence</span>
                    </h1>
                    <h1 className="sm:hidden text-gray-900 dark:text-indigo-300 font-black text-xl tracking-[0.2em]">
                        DGIP
                    </h1>
                </div>

                {/* Institution Side (Hidden on smaller mobile) */}
                <div className="hidden md:flex items-center">
                    <img
                        src="/IIT_RPR_Logo.png"
                        alt="IIT Ropar"
                        className="h-8 lg:h-9 w-auto object-contain dark:brightness-110 dark:drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]
                        border-l border-gray-200/50 dark:border-indigo-500/30 pl-5"
                    />
                </div>
            </div>

            {/* Right Section: Language & Theme Controls */}
            <div className="flex items-center justify-end w-auto sm:w-[120px] lg:w-[150px] gap-2 flex-shrink-0">
                <button
                    onClick={toggleLanguage}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs lg:text-sm font-semibold 
                        text-gray-700 dark:text-indigo-100 hover:bg-gray-200/50 dark:hover:bg-indigo-500/20 transition-all"
                >
                    <Languages className="w-4 h-4 text-indigo-500" />
                    <span className="hidden sm:inline">{locale === "en" ? "हिं" : "EN"}</span>
                </button>

                <button
                    onClick={cycleTheme}
                    className="p-2 rounded-lg text-gray-700 dark:text-indigo-200 hover:bg-gray-200/50 dark:hover:bg-indigo-500/20 transition-all"
                >
                    <ThemeIcon className="w-5 h-5" />
                </button>
            </div>
        </header>
    );
}