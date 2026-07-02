import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/sidebar";
import { TopNavbar } from "@/components/layout/top-navbar";

export function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <TopNavbar onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="pt-[72px] lg:pl-[260px] px-6 lg:px-8 pb-6 lg:pb-8">
        <Outlet />
      </main>
    </div>
  );
}
