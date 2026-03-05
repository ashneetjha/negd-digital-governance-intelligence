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
        <header className="sticky top-0 z-[60] flex items-center justify-between px-4 h-16 backdrop-blur-xl bg-white/70 dark:bg-gray-950/70 border-b border-gray-200/50 dark:border-white/10 shadow-sm transition-colors duration-300">
            
            {/* Left Section: Mobile Menu Toggle */}
            <div className="flex items-center justify-start w-auto sm:w-[120px] lg:w-[150px] flex-shrink-0">
                <button
                    onClick={toggle}
                    className="lg:hidden p-2 rounded-lg text-gray-700 dark:text-white/80 hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                    aria-label="Toggle menu"
                >
                    <Menu className="w-6 h-6" />
                </button>
            </div>

            {/* Center Section: Symmetrical Logos and Title */}
            <div className="flex flex-1 items-center justify-center min-w-0 px-2 gap-4 lg:gap-8">
                
                {/* Left Side: MeitY & NeGD (Hidden on smaller mobile) */}
                <div className="hidden md:flex items-center gap-4 lg:gap-6">
                    <img
                        src="/Ministry_of_Electronics_and_Information_Technology_Logo.png"
                        alt="MeitY"
                        className="h-7 lg:h-8 w-auto object-contain dark:brightness-200 transition-all"
                    />
                    <img
                        src="/NeGD_Logo.png"
                        alt="NeGD"
                        className="h-7 lg:h-8 w-auto object-contain dark:brightness-200 transition-all border-l border-gray-200 dark:border-gray-800 pl-4"
                    />
                </div>

                {/* Dead Center: Responsive Title */}
                <div className="flex flex-col items-center text-center px-2">
                    <h1 className="hidden sm:block text-gray-900 dark:text-white font-bold text-sm md:text-base lg:text-lg xl:text-xl tracking-tight truncate">
                        Digital Governance Intelligence Portal
                    </h1>
                    <h1 className="sm:hidden text-gray-900 dark:text-white font-bold text-lg tracking-wider truncate">
                        DGIP
                    </h1>
                </div>

                {/* Right Side: IIT Ropar (Hidden on smaller mobile) */}
                <div className="hidden md:flex items-center">
                    <img
                        src="/IIT_RPR_Logo.png"
                        alt="IIT Ropar"
                        className="h-7 lg:h-8 w-auto object-contain dark:brightness-200 transition-all border-l border-gray-200 dark:border-gray-800 pl-4"
                    />
                </div>
            </div>

            {/* Right Section: Language & Theme Controls */}
            <div className="flex items-center justify-end w-auto sm:w-[120px] lg:w-[150px] gap-1 flex-shrink-0">
                <button
                    onClick={toggleLanguage}
                    className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs lg:text-sm font-medium text-gray-700 dark:text-white/80 hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                >
                    <Languages className="w-4 h-4" />
                    <span className="hidden sm:inline">{locale === "en" ? "हिं" : "EN"}</span>
                </button>

                <button
                    onClick={cycleTheme}
                    className="p-2 rounded-lg text-gray-700 dark:text-white/80 hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                >
                    <ThemeIcon className="w-5 h-5" />
                </button>
            </div>
        </header>
    );
}