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
        <header className="sticky top-0 z-[60] flex items-center justify-between px-3 sm:px-4 h-16 backdrop-blur-xl bg-white/70 dark:bg-gray-950/70 border-b border-gray-200/50 dark:border-white/10 shadow-sm transition-colors duration-300">
            {/* Left Section: Mobile Menu Toggle (Fluid Width) */}
            <div className="flex items-center justify-start w-auto sm:w-[150px] flex-shrink-0">
                <button
                    onClick={toggle}
                    className="lg:hidden p-2 -ml-2 rounded-lg text-gray-700 dark:text-white/80 hover:text-black dark:hover:text-white hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                    aria-label="Toggle menu"
                >
                    <Menu className="w-6 h-6 sm:w-5 sm:h-5" />
                </button>
            </div>

            {/* Center Section: Symmetrical Logos and Title */}
            <div className="flex flex-1 items-center justify-center min-w-0 px-2">
                
                {/* Left Side: MeitY & NeGD */}
                <div className="hidden xl:flex flex-1 items-center justify-end gap-6">
                    <div className="relative flex items-center justify-center group">
                        <div className="absolute -inset-4 bg-white/40 blur-2xl rounded-full opacity-0 dark:opacity-100 transition-all duration-700 group-hover:bg-white/50 pointer-events-none"></div>
                        <Image
                            src="/Ministry_of_Electronics_and_Information_Technology_Logo.png"
                            alt="MeitY"
                            width={140}
                            height={36}
                            className="relative z-10 object-contain h-8 w-auto dark:drop-shadow-[0_0_2px_rgba(255,255,255,0.8)]"
                            priority
                        />
                    </div>
                    <div className="relative flex items-center justify-center group">
                        <div className="absolute -inset-2 bg-white/30 blur-xl rounded-full opacity-0 dark:opacity-100 transition-all duration-700 group-hover:bg-white/40 pointer-events-none"></div>
                        <Image
                            src="/NeGD_Logo.png"
                            alt="NeGD"
                            width={38}
                            height={38}
                            className="relative z-10 object-contain dark:drop-shadow-[0_0_2px_rgba(255,255,255,0.5)]"
                            priority
                        />
                    </div>
                </div>

                {/* Dead Center: Responsive Title */}
                <div className="flex flex-col items-center text-center min-w-0 flex-shrink">
                    {/* Shows only on screens larger than 'sm' */}
                    <h1 className="hidden sm:block text-gray-900 dark:text-white font-bold text-sm md:text-base lg:text-lg xl:text-xl leading-tight tracking-tight truncate">
                        Digital Governance Intelligence Portal
                    </h1>
                    {/* Shows only on tiny mobile screens to prevent overlap */}
                    <h1 className="sm:hidden text-gray-900 dark:text-white font-bold text-lg tracking-wider leading-tight truncate">
                        DGIP
                    </h1>
                </div>

                {/* Right Side: IIT Ropar */}
                <div className="hidden xl:flex flex-1 items-center justify-start">
                    <div className="relative flex items-center justify-center group">
                        <div className="absolute -inset-3 bg-white/40 blur-2xl rounded-full opacity-0 dark:opacity-100 transition-all duration-700 group-hover:bg-white/50 pointer-events-none"></div>
                        <Image
                            src="/IIT_RPR_Logo.png"
                            alt="IIT Ropar"
                            width={38}
                            height={38}
                            className="relative z-10 object-contain dark:drop-shadow-[0_0_2px_rgba(255,255,255,0.8)]"
                            priority
                        />
                    </div>
                </div>
            </div>

            {/* Right Section: Controls (Fluid Width) */}
            <div className="flex items-center justify-end w-auto sm:w-[150px] gap-1 flex-shrink-0">
                <button
                    onClick={toggleLanguage}
                    className="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-sm font-medium text-gray-700 dark:text-white/80 hover:text-black dark:hover:text-white hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                    aria-label="Toggle language"
                >
                    <Languages className="w-4 h-4" />
                    <span className="hidden sm:inline">{locale === "en" ? "हिं" : "EN"}</span>
                </button>

                <button
                    onClick={cycleTheme}
                    className="p-2 rounded-lg text-gray-700 dark:text-white/80 hover:text-black dark:hover:text-white hover:bg-gray-200/50 dark:hover:bg-white/10 transition-colors"
                    aria-label="Toggle theme"
                >
                    <ThemeIcon className="w-5 h-5" />
                </button>
            </div>
        </header>
    );
}