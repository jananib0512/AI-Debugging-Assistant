import { useNavigate } from "react-router-dom";

interface RelatedLink {
  path: string;
  label: string;
  desc: string;
}

const relatedMap: Record<string, RelatedLink[]> = {
  "file-analysis": [
    { path: "function-class", label: "Function & Class", desc: "View functions and classes in related files" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores for these files" },
    { path: "code-intelligence", label: "Code Intelligence", desc: "View code metrics and structure" },
  ],
  "file-intelligence": [
    { path: "file-analysis", label: "File Analysis", desc: "View basic file-level metrics" },
    { path: "function-class", label: "Function & Class", desc: "View functions and classes" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores" },
  ],
  "function-class": [
    { path: "file-analysis", label: "File Analysis", desc: "View file-level metrics" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores" },
    { path: "dependencies", label: "Dependencies", desc: "View import dependencies" },
  ],
  "call-graph": [
    { path: "function-class-intelligence", label: "Functions & Classes", desc: "View function and class details" },
    { path: "import-dependency", label: "Import Dependency", desc: "View import relationships" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality impact" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic analysis" },
  ],
  "semantic-intelligence": [
    { path: "call-graph", label: "Call Graph", desc: "View call relationships" },
    { path: "function-class-intelligence", label: "Functions & Classes", desc: "View function details" },
    { path: "file-intelligence", label: "File Details", desc: "View file health scores" },
  ],
  "function-class-intelligence": [
    { path: "function-class", label: "Function & Class", desc: "View basic function/class analysis" },
    { path: "file-intelligence", label: "File Details", desc: "View file health scores" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
  ],
  "import-dependency": [
    { path: "file-analysis", label: "File Analysis", desc: "View affected files" },
    { path: "function-class", label: "Function & Class", desc: "View affected functions" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality impact" },
  ],
  "code-quality": [
    { path: "file-analysis", label: "File Analysis", desc: "View problematic files" },
    { path: "function-class", label: "Function & Class", desc: "View affected functions and classes" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency-related issues" },
  ],
  "code-intelligence": [
    { path: "code-quality", label: "Code Quality", desc: "View quality assessment" },
    { path: "file-analysis", label: "File Analysis", desc: "View file details" },
    { path: "function-class", label: "Function & Class", desc: "View function and class structure" },
  ],
  framework: [
    { path: "technology", label: "Technology Stack", desc: "View full technology inventory" },
    { path: "dependencies", label: "Dependencies", desc: "View framework-related dependencies" },
    { path: "code-quality", label: "Code Quality", desc: "View framework code quality" },
  ],
  technology: [
    { path: "framework", label: "Framework", desc: "View framework details" },
    { path: "dependencies", label: "Dependencies", desc: "View library dependencies" },
    { path: "code-intelligence", label: "Code Intelligence", desc: "View language distribution" },
  ],
  folders: [
    { path: "file-analysis", label: "File Analysis", desc: "View file-level metrics" },
    { path: "modules", label: "Module Detection", desc: "View module organization" },
    { path: "architecture", label: "Architecture", desc: "View architecture patterns" },
  ],
  modules: [
    { path: "folders", label: "Folder Structure", desc: "View directory organization" },
    { path: "architecture", label: "Architecture", desc: "View architecture alignment" },
    { path: "file-analysis", label: "File Analysis", desc: "View module file details" },
  ],
  architecture: [
    { path: "modules", label: "Module Detection", desc: "View detected modules" },
    { path: "folders", label: "Folder Structure", desc: "View folder layout" },
    { path: "code-quality", label: "Code Quality", desc: "View architecture quality" },
  ],
  "entry-points": [
    { path: "file-analysis", label: "File Analysis", desc: "View entry point files" },
    { path: "function-class", label: "Function & Class", desc: "View entry point functions" },
    { path: "framework", label: "Framework", desc: "View framework starters" },
  ],
  configuration: [
    { path: "dependencies", label: "Dependencies", desc: "View config-related dependencies" },
    { path: "code-quality", label: "Code Quality", desc: "View configuration quality" },
    { path: "file-analysis", label: "File Analysis", desc: "View config file details" },
  ],
  dependencies: [
    { path: "import-dependency", label: "Import Dependency", desc: "View detailed import analysis" },
    { path: "code-quality", label: "Code Quality", desc: "View dependency quality" },
    { path: "file-analysis", label: "File Analysis", desc: "View dependency file details" },
  ],
  recommendations: [
    { path: "code-quality", label: "Code Quality", desc: "View quality improvement areas" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency recommendations" },
    { path: "file-analysis", label: "File Analysis", desc: "View file-level recommendations" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View maintainability analysis" },
  ],
  "refactoring-intelligence": [
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View code smells and technical debt" },
    { path: "documentation-intelligence", label: "Documentation", desc: "View documentation quality" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores and issues" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency structure" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
  ],
  "documentation-intelligence": [
    { path: "test-intelligence", label: "Testing", desc: "View test coverage and quality" },
    { path: "refactoring-intelligence", label: "Code Improvement", desc: "View refactoring opportunities" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View code smells and technical debt" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores and issues" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
  ],
  "test-intelligence": [
    { path: "documentation-intelligence", label: "Documentation", desc: "View documentation quality" },
    { path: "refactoring-intelligence", label: "Code Improvement", desc: "View refactoring opportunities" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View code smells and technical debt" },
    { path: "code-quality", label: "Code Quality", desc: "View quality scores and issues" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
  ],
  "unified-intelligence": [
    { path: "architecture", label: "Architecture", desc: "View architecture health" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency health" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic understanding" },
    { path: "call-graph", label: "Call Graph", desc: "View execution flows" },
    { path: "function-class-intelligence", label: "Functions & Classes", desc: "View function details" },
    { path: "file-analysis", label: "File Analysis", desc: "View file health" },
    { path: "configuration", label: "Configuration", desc: "View config health" },
    { path: "risk-intelligence", label: "Project Risks", desc: "View project risk assessment" },
    { path: "security-intelligence", label: "Security", desc: "View security analysis" },
    { path: "performance-intelligence", label: "Performance", desc: "View performance analysis" },
  ],
  "risk-intelligence": [
    { path: "architecture", label: "Architecture", desc: "View architecture health" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency health" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic understanding" },
    { path: "call-graph", label: "Call Graph", desc: "View execution flows" },
    { path: "file-analysis", label: "File Analysis", desc: "View file health" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
    { path: "security-intelligence", label: "Security", desc: "View security analysis" },
    { path: "performance-intelligence", label: "Performance", desc: "View performance analysis" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View maintainability analysis" },
  ],
  "security-intelligence": [
    { path: "architecture", label: "Architecture", desc: "View architecture health" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency health" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic understanding" },
    { path: "call-graph", label: "Call Graph", desc: "View execution flows" },
    { path: "risk-intelligence", label: "Project Risks", desc: "View project risk assessment" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
    { path: "performance-intelligence", label: "Performance", desc: "View performance analysis" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View maintainability analysis" },
  ],
  "performance-intelligence": [
    { path: "architecture", label: "Architecture", desc: "View architecture health" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency health" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic understanding" },
    { path: "call-graph", label: "Call Graph", desc: "View execution flows" },
    { path: "risk-intelligence", label: "Project Risks", desc: "View project risk assessment" },
    { path: "security-intelligence", label: "Security", desc: "View security analysis" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
    { path: "maintainability-intelligence", label: "Maintainability", desc: "View maintainability analysis" },
  ],
  "maintainability-intelligence": [
    { path: "architecture", label: "Architecture", desc: "View architecture health" },
    { path: "dependencies", label: "Dependencies", desc: "View dependency health" },
    { path: "code-quality", label: "Code Quality", desc: "View code quality scores" },
    { path: "semantic-intelligence", label: "Semantic Analysis", desc: "View semantic understanding" },
    { path: "call-graph", label: "Call Graph", desc: "View execution flows" },
    { path: "risk-intelligence", label: "Project Risks", desc: "View project risk assessment" },
    { path: "security-intelligence", label: "Security", desc: "View security analysis" },
    { path: "performance-intelligence", label: "Performance", desc: "View performance analysis" },
    { path: "unified-intelligence", label: "Unified Dashboard", desc: "View analysis overview" },
  ],
};

const linkClass = "flex items-center gap-3 rounded-lg border border-[#E5E7EB] px-4 py-3 text-xs transition-colors hover:bg-[#F9FAFB] hover:border-[#2563EB]";

export function RelatedAnalysisNav({ projectId, currentPage }: { projectId: string; currentPage: string }) {
  const navigate = useNavigate();
  const links = relatedMap[currentPage];

  if (!links || links.length === 0) return null;

  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">Related Analysis</p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {links.map((link) => (
          <button
            key={link.path}
            onClick={() => navigate(`/projects/${projectId}/analyzer/${link.path}`)}
            className={linkClass}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#EFF6FF]">
              <span className="text-[10px] font-bold text-[#2563EB]">{link.label.charAt(0)}</span>
            </div>
            <div className="min-w-0 flex-1 text-left">
              <p className="font-medium text-[#111827]">{link.label}</p>
              <p className="mt-0.5 text-[10px] text-[#6B7280]">{link.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
