"use client";

import { createContext, useContext, useState, useCallback } from "react";
import { usePathname } from "next/navigation";

interface SidebarContextType {
    isOpen: boolean;
    toggle: () => void;
    close: () => void;
}

const SidebarContext = createContext<SidebarContextType>({
    isOpen: false,
    toggle: () => { },
    close: () => { },
});

export function useSidebar() {
    return useContext(SidebarContext);
}

export function SidebarProvider({ children }: { children: React.ReactNode }) {
    const [openForPath, setOpenForPath] = useState<string | null>(null);
    const pathname = usePathname();

    const isOpen = openForPath === pathname;
    const toggle = useCallback(() => {
        setOpenForPath((prev) => (prev === pathname ? null : pathname));
    }, [pathname]);
    const close = useCallback(() => setOpenForPath(null), []);

    return (
        <SidebarContext.Provider value={{ isOpen, toggle, close }}>
            {children}
        </SidebarContext.Provider>
    );
}
