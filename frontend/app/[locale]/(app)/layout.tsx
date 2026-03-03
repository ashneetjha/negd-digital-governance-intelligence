import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { SidebarProvider } from "@/components/layout/SidebarContext";

export default function AppLayout({ children }: { children: React.ReactNode }) {
    return (
        <SidebarProvider>
            <div className="flex flex-col min-h-screen">
                <Header />
                <div className="flex flex-1">
                    <Sidebar />
                    <main className="flex-1 p-4 sm:p-6 overflow-y-auto" style={{ backgroundColor: "var(--bg-page)" }}>
                        {children}
                    </main>
                </div>
            </div>
        </SidebarProvider>
    );
}
