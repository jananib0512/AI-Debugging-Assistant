import type { ElementType } from "react";
import {
  BarChart3,
  Bug,
  LayoutDashboard,
  Layers,
  LogOut,
  FolderKanban,
  Radio,
  ScrollText,
  Settings,
  Shield,
  User,
  Workflow,
} from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/lib/utils";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

interface NavItem {
  href?: string;
  label: string;
  icon: ElementType;
  disabled?: boolean;
}

const mainNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/workspace", label: "Workspace", icon: Layers },
];

const comingSoonNav: NavItem[] = [
  { label: "Bug Detection", icon: Bug, disabled: true },
  { label: "Runtime Monitor", icon: Radio, disabled: true },
  { label: "Performance", icon: BarChart3, disabled: true },
  { label: "Security", icon: Shield, disabled: true },
  { label: "AI Suggestions", icon: Workflow, disabled: true },
  { label: "Reports", icon: ScrollText, disabled: true },
];

const bottomNav: NavItem[] = [
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/profile", label: "Profile", icon: User },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const NavLink = ({ href, label, icon: Icon, disabled }: NavItem) => {
    const isActive = href ? location.pathname === href : false;

    if (disabled) {
      return (
        <div className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#6B7280]/40 cursor-not-allowed select-none transition-colors duration-200"
          style={{ height: 44 }}
        >
          <Icon className="h-[18px] w-[18px] shrink-0 opacity-50" />
          <span className="flex-1">{label}</span>
          <span className="rounded-full bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">
            Coming Soon
          </span>
        </div>
      );
    }

    return (
      <Link
        to={href!}
        onClick={onClose}
        className={cn(
          "relative flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-all duration-200 rounded-[10px]",
          isActive
            ? "bg-[#EFF6FF] text-[#2563EB]"
            : "text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]",
        )}
        style={{ height: 44 }}
      >
        {isActive && (
          <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-[#2563EB]" />
        )}
        <Icon
          className={cn(
            "h-[18px] w-[18px] shrink-0",
            isActive ? "text-[#2563EB]" : "text-[#6B7280]",
          )}
        />
        <span className="flex-1">{label}</span>
      </Link>
    );
  };

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          "fixed top-[72px] left-0 z-30 flex h-[calc(100vh-72px)] w-[260px] flex-col border-r border-[#E5E7EB] bg-white transition-transform duration-300 lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {mainNav.map((item) => (
            <NavLink key={item.label} {...item} />
          ))}

          <div className="pt-4 pb-1">
            <p className="px-4 pb-1 text-[10px] font-semibold uppercase tracking-widest text-[#6B7280]/50">
              AI Features
            </p>
            <div className="space-y-0">
              {comingSoonNav.map((item) => (
                <NavLink key={item.label} {...item} />
              ))}
            </div>
          </div>
        </div>

        <div className="border-t border-[#E5E7EB] px-3 py-3 space-y-0">
          {bottomNav.map((item) => (
            <NavLink key={item.label} {...item} />
          ))}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-[#6B7280] rounded-[10px] transition-colors duration-200 hover:bg-[#F3F4F6] hover:text-[#EF4444] cursor-pointer"
            style={{ height: 44 }}
          >
            <LogOut className="h-[18px] w-[18px] shrink-0" />
            <span>Logout</span>
          </button>
        </div>

        {user && (
          <div className="border-t border-[#E5E7EB] px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F3F4F6] text-xs font-semibold text-[#6B7280] shrink-0">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="truncate text-sm font-medium text-[#111827]">
                  {user.full_name}
                </p>
                <p className="truncate text-xs text-[#6B7280]">
                  {user.email}
                </p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
