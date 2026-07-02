import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Bell,
  BookOpen,
  ChevronDown,
  LifeBuoy,
  LogOut,
  Menu,
  MessageCircle,
  Search,
  Settings,
  Sliders,
  User,
} from "lucide-react";

import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/lib/utils";
import { NotificationsDropdown } from "@/components/layout/notifications-dropdown";

interface TopNavbarProps {
  onMenuClick: () => void;
}

const pageMeta: Record<string, { title: string; breadcrumb: string }> = {
  "/dashboard": { title: "Dashboard", breadcrumb: "Home / Dashboard" },
  "/projects": { title: "Projects", breadcrumb: "Home / Projects" },
  "/upload": { title: "Upload Project", breadcrumb: "Home / Upload" },
  "/workspace": { title: "Workspace", breadcrumb: "Home / Workspace" },
  "/scan-history": { title: "Scan History", breadcrumb: "Home / Scan History" },
  "/ai-status": { title: "AI Status", breadcrumb: "Home / AI Status" },
  "/settings": { title: "Settings", breadcrumb: "Home / Settings" },
  "/profile": { title: "Profile", breadcrumb: "Home / Profile" },
};

export function TopNavbar({ onMenuClick }: TopNavbarProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const userDropdownRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const helpRef = useRef<HTMLDivElement>(null);

  const meta = pageMeta[location.pathname] ?? {
    title: "AI Debugging Assistant",
    breadcrumb: "Home",
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        userDropdownRef.current &&
        !userDropdownRef.current.contains(event.target as Node)
      ) {
        setUserDropdownOpen(false);
      }
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(event.target as Node)
      ) {
        setNotificationsOpen(false);
      }
      if (
        helpRef.current &&
        !helpRef.current.contains(event.target as Node)
      ) {
        setHelpOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-40 flex h-[72px] items-center gap-4 border-b border-[#E5E7EB] bg-white px-4 lg:px-8">
      <button
        onClick={onMenuClick}
        className="lg:hidden text-[#6B7280] hover:text-[#111827] transition-colors -ml-1"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="hidden sm:block min-w-0">
        <p className="text-[11px] font-medium text-[#6B7280] tracking-wide">
          {meta.breadcrumb}
        </p>
        <h1 className="text-lg font-semibold tracking-tight text-[#111827] mt-0.5">
          {meta.title}
        </h1>
      </div>

      <div className="hidden md:flex flex-1 justify-center px-8">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B7280] pointer-events-none" />
          <input
            type="text"
            placeholder="Search projects, bugs, reports..."
            disabled
            className="flex h-9 w-full rounded-lg border border-[#E5E7EB] bg-white pl-9 pr-16 text-sm text-[#6B7280] placeholder:text-[#6B7280]/50 outline-none cursor-not-allowed"
          />
          <span className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5 rounded border border-[#E5E7EB] px-1.5 py-0.5 text-[10px] font-medium text-[#6B7280] pointer-events-none">
            <span>⌘</span>K
          </span>
        </div>
      </div>

      {user && (
        <div className="flex items-center gap-1.5 ml-auto sm:ml-0">
          <div className="relative" ref={notificationsRef}>
            <button
              onClick={() => {
                setNotificationsOpen(!notificationsOpen);
                setUserDropdownOpen(false);
                setHelpOpen(false);
              }}
              className="relative flex h-9 w-9 items-center justify-center rounded-lg text-[#6B7280] transition-colors hover:bg-[#F3F4F6]"
            >
              <Bell className="h-4 w-4" />
            </button>
            <NotificationsDropdown
              open={notificationsOpen}
              onClose={() => setNotificationsOpen(false)}
            />
          </div>

          <div className="relative" ref={helpRef}>
            <button
              onClick={() => {
                setHelpOpen(!helpOpen);
                setUserDropdownOpen(false);
                setNotificationsOpen(false);
              }}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-[#6B7280] transition-colors hover:bg-[#F3F4F6]"
            >
              <LifeBuoy className="h-4 w-4" />
            </button>
            <AnimatePresence>
              {helpOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setHelpOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.96 }}
                    transition={{ duration: 0.12 }}
                    className="absolute right-0 top-full mt-2 w-48 overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-dropdown z-50"
                  >
                    <div className="p-1.5">
                      <button
                        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]"
                        onClick={() => setHelpOpen(false)}
                      >
                        <BookOpen className="h-4 w-4" />
                        Documentation
                      </button>
                      <button
                        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]"
                        onClick={() => setHelpOpen(false)}
                      >
                        <MessageCircle className="h-4 w-4" />
                        Support
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          <div className="mx-2 h-6 w-px bg-[#E5E7EB] hidden sm:block" />

          <div className="relative" ref={userDropdownRef}>
            <button
              onClick={() => {
                setUserDropdownOpen(!userDropdownOpen);
                setNotificationsOpen(false);
                setHelpOpen(false);
              }}
              className="flex items-center gap-2.5 rounded-lg p-1.5 pr-2 transition-colors hover:bg-[#F3F4F6]"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#2563EB]/10 text-xs font-semibold text-[#2563EB] shrink-0">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <span className="hidden text-sm font-medium text-[#111827] sm:block">
                {user.full_name}
              </span>
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 text-[#6B7280] transition-transform duration-150",
                  userDropdownOpen && "rotate-180",
                )}
              />
            </button>

            {userDropdownOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 overflow-hidden rounded-xl border border-[#E5E7EB] bg-white shadow-dropdown animate-fade-in">
                <div className="border-b border-[#E5E7EB] p-3">
                  <p className="truncate text-sm font-medium text-[#111827]">
                    {user.full_name}
                  </p>
                  <p className="truncate text-xs text-[#6B7280]">
                    {user.email}
                  </p>
                </div>
                <div className="p-1.5">
                  <Link
                    to="/profile"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]"
                  >
                    <User className="h-4 w-4" />
                    Profile
                  </Link>
                  <Link
                    to="/settings"
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]"
                  >
                    <Settings className="h-4 w-4" />
                    Account Settings
                  </Link>
                  <button
                    onClick={() => setUserDropdownOpen(false)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#111827]"
                  >
                    <Sliders className="h-4 w-4" />
                    Preferences
                  </button>
                </div>
                <div className="border-t border-[#E5E7EB] p-1.5">
                  <button
                    onClick={async () => {
                      setUserDropdownOpen(false);
                      await logout();
                    }}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-[#6B7280] transition-colors hover:bg-[#F3F4F6] hover:text-[#EF4444]"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
