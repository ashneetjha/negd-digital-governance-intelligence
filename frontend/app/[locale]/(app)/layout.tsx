import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { SidebarProvider } from "@/components/layout/SidebarContext";
import BackendWakeup from "@/components/BackendWakeup";

export default function AppLayout({ children }: { children: React.ReactNode }) {
    return (
        <SidebarProvider>
            {/* Keep-alive ping warms up the Render free-tier container
                as soon as the app shell mounts, before the user clicks anything. */}
            <BackendWakeup />

            {/* Standard Dashboard Layout: Full-height Sidebar Left, Header + Content Right */}
            <div className="flex h-screen overflow-hidden bg-transparent">
                
                {/* Sidebar container - naturally full height */}
                <Sidebar />
                
                {/* Main content wrapper taking up the remaining width */}
                <div className="flex flex-col flex-1 min-w-0 overflow-hidden bg-transparent">
                    {/* Header stays pinned to the top of this right-side column */}
                    <Header />
                    
                    {/* ONLY this section scrolls, eliminating the double-scroll and blank space bug */}
                    <main className="flex-1 p-4 sm:p-6 overflow-y-auto bg-transparent transition-all duration-300">
                        <div className="mx-auto max-w-7xl h-full">
                            {children}
                        </div>
                    </main>
                </div>
                
            </div>
        </SidebarProvider>
    );
}