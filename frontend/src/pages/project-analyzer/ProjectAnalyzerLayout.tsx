import { useParams, useNavigate, useLocation, Outlet, Link } from "react-router-dom";
import {
  Award,
  BarChart3,
  Box,
  Brain,
  Building2,
  ChevronLeft,
  Cpu,
  FileCode,
  FileSearch,
  FolderKanban,
  FunctionSquare,
  GitBranch,
  GitMerge,
  Package,
  Radar,
  Server,
  Settings,
  Share2,
  Shield,
  ShieldAlert,
  Wrench,
  Zap,
} from "lucide-react";
import { AnalysisProvider } from "@/contexts/AnalysisContext";

const navItems = [
  { path: "", label: "Overview", icon: BarChart3 },
  { path: "framework", label: "Framework", icon: Cpu },
  { path: "technology", label: "Technology", icon: Server },
  { path: "folders", label: "Folders", icon: FolderKanban },
  { path: "modules", label: "Modules", icon: Box },
  { path: "architecture", label: "Architecture", icon: Building2 },
  { path: "entry-points", label: "Entry Points", icon: GitBranch },
  { path: "configuration", label: "Configuration", icon: Settings },
  { path: "dependencies", label: "Dependencies", icon: Package },
  { path: "code-intelligence", label: "Code Intelligence", icon: FileCode },
  { path: "code-quality", label: "Code Quality", icon: Award },
  { path: "recommendations", label: "Recommendations", icon: Shield },
  { path: "file-analysis", label: "File Analysis", icon: FileCode },
  { path: "file-intelligence", label: "File Intelligence", icon: FileSearch },
  { path: "function-class", label: "Function & Class", icon: FunctionSquare },
  { path: "function-class-intelligence", label: "Func/Class Intelligence", icon: Brain },
  { path: "call-graph", label: "Call Graph", icon: Share2 },
  { path: "import-dependency", label: "Dependencies", icon: GitMerge },
  { path: "semantic-intelligence", label: "Semantic Intel", icon: Brain },
  { path: "unified-intelligence", label: "Unified Dashboard", icon: Radar },
  { path: "risk-intelligence", label: "Risk Intelligence", icon: ShieldAlert },
  { path: "security-intelligence", label: "Security Intel", icon: Shield },
  { path: "performance-intelligence", label: "Performance Intel", icon: Zap },
  { path: "maintainability-intelligence", label: "Maintainability Intel", icon: Wrench },
];

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const basePath = location.pathname.split("/").slice(0, 4).join("/");
  const currentPath = location.pathname.replace(/\/+$/, "").split("/").pop() || "";

  return (
    <aside className="fixed left-0 top-[72px] z-30 h-[calc(100vh-72px)] w-[240px] border-r border-[#E5E7EB] bg-white overflow-y-auto">
      <div className="p-4">
        <button
          onClick={() => navigate("/projects")}
          className="mb-4 flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827] transition-colors"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          Back to Projects
        </button>
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
        <nav className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = item.path === "" ? currentPath === "" || currentPath === "analyzer" : currentPath === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={`${basePath}${item.path ? "/" + item.path : ""}`}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#2563EB] text-white"
                    : "text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827]"
                }`}
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}

function AnalyzerContent({ children }: { children: React.ReactNode }) {
  return (
    <div className="pl-[240px] lg:pl-0">
      <div className="min-h-[calc(100vh-72px)] w-full bg-[#F8FAFC] px-0 py-4 lg:py-6">
        {children}
      </div>
    </div>
  );
}

export function ProjectAnalyzerLayout() {
  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return (
      <AnalyzerContent>
        <div className="flex items-center justify-center py-20">
          <p className="text-sm text-[#6B7280]">Project ID is required.</p>
        </div>
      </AnalyzerContent>
    );
  }

  return (
    <AnalysisProvider projectId={projectId}>
      <Sidebar />
      <AnalyzerContent>
        <Outlet />
      </AnalyzerContent>
    </AnalysisProvider>
  );
}
