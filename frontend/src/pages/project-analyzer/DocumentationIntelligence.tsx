import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  BookOpen,
  ChevronDown,
  Code2,
  FileText,
  Lightbulb,
  RefreshCw,
  Search,
} from "lucide-react";
import { getDocumentationIntelligence } from "@/lib/project-analyzer";
import type {
  DocumentationIntelligenceResponse,
  DocFinding,
  DocumentationScore,
  DocumentationSummary,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";
import { ErrorBoundary } from "@/components/project-analyzer/ErrorBoundary";


const severityColors: Record<string, string> = {
  critical: "bg-red-50 text-red-700 border-red-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-blue-50 text-blue-700 border-blue-200",
  informational: "bg-gray-50 text-gray-600 border-gray-200",
};

const qualityColors: Record<string, string> = {
  excellent: "bg-green-50 text-green-700 border-green-200",
  good: "bg-emerald-50 text-emerald-700 border-emerald-200",
  average: "bg-yellow-50 text-yellow-700 border-yellow-200",
  poor: "bg-orange-50 text-orange-700 border-orange-200",
  missing: "bg-red-50 text-red-700 border-red-200",
  found: "bg-blue-50 text-blue-700 border-blue-200",
  comprehensive: "bg-green-50 text-green-700 border-green-200",
  partial: "bg-yellow-50 text-yellow-700 border-yellow-200",
  minimal: "bg-orange-50 text-orange-700 border-orange-200",
};


function GaugeCard({ label, value, stroke }: { label: string; value: number; stroke: string }) {
  const r = 32;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(value, 100) / 100) * circ;
  return (
    <div className="flex flex-col items-center rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
      <svg width="80" height="80" viewBox="0 0 80 80" className="-rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#F3F4F6" strokeWidth="6" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={stroke} strokeWidth="6" strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <span className="mt-1 text-lg font-bold text-[#111827]">{value.toFixed(0)}</span>
      <span className="text-[10px] font-medium text-[#6B7280] text-center leading-tight">{label}</span>
    </div>
  );
}


function DocumentationIntelligenceInner() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<DocumentationIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortBy, setSortBy] = useState("severity");
  const [selectedFinding, setSelectedFinding] = useState<DocFinding | null>(null);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getDocumentationIntelligence(Number(projectId));
      setData(res);
    } catch {
      setError("Failed to load documentation intelligence.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const score: DocumentationScore = (data?.documentation_score || {}) as DocumentationScore;
  const summary: DocumentationSummary = (data?.summary || {}) as DocumentationSummary;

  const gaugeConfigs = useMemo(() => [
    { label: "Documentation Score", value: score.overall_documentation_score ?? 0, stroke: "#2563EB" },
    { label: "Coverage", value: score.documentation_coverage ?? 0, stroke: "#059669" },
    { label: "Quality", value: score.documentation_quality ?? 0, stroke: "#7C3AED" },
    { label: "Developer Readiness", value: score.developer_readiness ?? 0, stroke: "#D97706" },
    { label: "AI Confidence", value: score.ai_confidence ?? 0, stroke: "#0891B2" },
  ], [score]);

  const uniqueTypes = useMemo(() => {
    if (!data) return [];
    const types = new Set((data.findings || []).map((f) => f.type));
    return Array.from(types).sort();
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let list = [...(data.findings || [])];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (f) =>
          (f.name || "").toLowerCase().includes(q) ||
          (f.description || "").toLowerCase().includes(q) ||
          (f.affected_files || []).some((file) => (file || "").toLowerCase().includes(q)) ||
          (f.affected_functions || []).some((fn) => (fn || "").toLowerCase().includes(q)) ||
          (f.affected_classes || []).some((c) => (c || "").toLowerCase().includes(q)),
      );
    }
    if (severityFilter !== "all") {
      list = list.filter((f) => f.severity === severityFilter);
    }
    if (typeFilter !== "all") {
      list = list.filter((f) => f.type === typeFilter);
    }
    if (sortBy === "severity") {
      const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
      list.sort((a, b) => (order[a.severity] || 4) - (order[b.severity] || 4));
    } else if (sortBy === "name") {
      list.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    } else if (sortBy === "type") {
      list.sort((a, b) => (a.type || "").localeCompare(b.type || ""));
    }
    return list;
  }, [data, searchQuery, severityFilter, typeFilter, sortBy]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="h-8 w-8 animate-spin text-[#2563EB]" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-center">
        <AlertTriangle className="h-8 w-8 text-red-500" />
        <p className="text-sm text-red-600">{error || "No data available."}</p>
        <button onClick={fetchData} className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!data.findings || data.findings.length === 0) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 text-white shadow-lg">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#2563EB]/20">
              <BookOpen className="h-6 w-6 text-[#60A5FA]" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Documentation Intelligence</h1>
              <p className="mt-1 text-xs text-[#94A3B8]">
                Automated documentation quality analysis and coverage assessment
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-center gap-3 rounded-xl border border-[#E5E7EB] bg-white py-16 text-center shadow-sm">
          <FileText className="h-10 w-10 text-[#D1D5DB]" />
          <p className="text-sm font-medium text-[#6B7280]">All documentation requirements are met.</p>
          <p className="text-xs text-[#9CA3AF]">No documentation gaps detected.</p>
        </div>
        <RelatedAnalysisNav projectId={projectId!} currentPage="documentation-intelligence" />
        <div className="flex items-center gap-1 text-[10px] text-[#9CA3AF]">
          <span>Back to:</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="font-medium text-[#2563EB] hover:underline">Overview</button>
          <span>|</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Unified Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 text-white shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#2563EB]/20">
            <BookOpen className="h-6 w-6 text-[#60A5FA]" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Documentation Intelligence</h1>
            <p className="mt-1 text-xs text-[#94A3B8]">
              Automated documentation quality analysis and coverage assessment
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#94A3B8]">
          <span className="rounded-md bg-white/5 px-2 py-1">
            Score: {score.overall_documentation_score.toFixed(0)}/100
          </span>
          <span className="rounded-md bg-white/5 px-2 py-1">
            Coverage: {score.documentation_coverage.toFixed(0)}%
          </span>
          <span className="rounded-md bg-white/5 px-2 py-1">
            Risk: {score.risk_level || "unknown"}
          </span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-5">
        {gaugeConfigs.map((g) => (
          <GaugeCard key={g.label} label={g.label} value={g.value} stroke={g.stroke} />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <Code2 className="h-3.5 w-3.5 text-[#2563EB]" /> Documented Functions
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.documented_functions}</p>
          {summary.undocumented_functions > 0 && (
            <p className="text-[10px] text-red-500">{summary.undocumented_functions} undocumented</p>
          )}
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <Code2 className="h-3.5 w-3.5 text-[#7C3AED]" /> Documented Classes
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.documented_classes}</p>
          {summary.undocumented_classes > 0 && (
            <p className="text-[10px] text-red-500">{summary.undocumented_classes} undocumented</p>
          )}
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <FileText className="h-3.5 w-3.5 text-[#059669]" /> Files with Comments
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.files_with_comments ?? 0}</p>
          <p className="text-[10px] text-[#9CA3AF]">{summary.files_without_comments ?? 0} without</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <AlertTriangle className="h-3.5 w-3.5 text-orange-500" /> Missing Project Docs
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">
            {[
              summary.missing_readme,
              summary.missing_license,
              summary.missing_contributing,
              summary.missing_changelog,
              summary.missing_architecture_docs,
            ].filter(Boolean).length}
          </p>
        </div>
      </div>

      {summary.summary_text && (
        <div className="flex items-start gap-3 rounded-xl border border-[#E5E7EB] bg-gradient-to-r from-[#EFF6FF] to-white p-4 shadow-sm">
          <Lightbulb className="mt-0.5 h-5 w-5 text-[#2563EB]" />
          <div>
            <p className="text-sm font-medium text-[#111827]">AI Documentation Summary</p>
            <p className="mt-1 text-xs text-[#4B5563]">{summary.summary_text}</p>
          </div>
        </div>
      )}

      {data.project_docs && data.project_docs.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Project Documentation Files
          </p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data.project_docs.map((doc, i) => (
              <div key={i} className={`rounded-lg border px-3 py-2 ${doc.present ? "bg-[#F0FDF4] border-[#BBF7D0]" : "bg-[#FEF2F2] border-[#FECACA]"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-[#374151]">{doc.name}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[9px] font-medium ${qualityColors[doc.quality] || qualityColors.missing}`}>
                    {doc.quality}
                  </span>
                </div>
                {doc.present && (
                  <p className="mt-0.5 text-[10px] text-[#6B7280]">{doc.path} &middot; {doc.completeness}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
        <div className="relative flex-1" style={{ minWidth: "200px" }}>
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search by name, file, function, class..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-[#E5E7EB] py-2 pl-9 pr-3 text-xs outline-none focus:border-[#2563EB]"
          />
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs outline-none focus:border-[#2563EB]"
        >
          <option value="all">All Types</option>
          {uniqueTypes.map((t) => (
            <option key={t} value={t}>{t.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs outline-none focus:border-[#2563EB]"
        >
          <option value="severity">Sort: Severity</option>
          <option value="name">Sort: Name</option>
          <option value="type">Sort: Type</option>
        </select>
      </div>

      <RelatedAnalysisNav projectId={projectId!} currentPage="documentation-intelligence" />

      {filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((finding, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02 }}
              className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition-all hover:shadow-md cursor-pointer"
              onClick={() => setSelectedFinding(selectedFinding === finding ? null : finding)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`rounded-md border px-2 py-0.5 text-[10px] font-medium ${severityColors[finding.severity] || severityColors.low}`}>
                      {(finding.severity || "low").toUpperCase()}
                    </span>
                    <span className="rounded-md bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">
                      {finding.type.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </span>
                    <span className="truncate text-sm font-medium text-[#111827]">{finding.name || "Unnamed"}</span>
                  </div>
                  <p className="mt-1 text-xs text-[#6B7280] line-clamp-2">{finding.description || ""}</p>
                </div>
                <ChevronDown className={`mt-1 h-4 w-4 flex-shrink-0 text-[#9CA3AF] transition-transform ${selectedFinding === finding ? "rotate-180" : ""}`} />
              </div>

              {selectedFinding === finding && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  transition={{ duration: 0.2 }}
                  className="mt-4 space-y-3 border-t border-[#E5E7EB] pt-4"
                >
                  {(finding.affected_files || []).length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Files</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {(finding.affected_files || []).map((f, fi) => (
                          <span key={fi} className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#6B7280]">{f}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {(finding.affected_functions || []).length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Functions</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {(finding.affected_functions || []).map((fn, fi) => (
                          <span key={fi} className="rounded bg-[#F0FDF4] px-2 py-0.5 text-[10px] text-[#166534]">{fn}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {(finding.affected_classes || []).length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Classes</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {(finding.affected_classes || []).map((c, ci) => (
                          <span key={ci} className="rounded bg-[#EEF2FF] px-2 py-0.5 text-[10px] text-[#4338CA]">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {finding.recommendation && (
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Recommendation</p>
                      <p className="mt-1 text-xs text-[#2563EB]">{finding.recommendation}</p>
                    </div>
                  )}
                  {finding.estimated_improvement && (
                    <div className="rounded-lg bg-[#F9FAFB] p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Estimated Improvement</p>
                      <p className="mt-1 text-xs font-medium text-[#059669]">{finding.estimated_improvement}</p>
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-12 text-center">
          <FileText className="h-8 w-8 text-[#D1D5DB]" />
          <p className="text-sm text-[#6B7280]">No documentation findings match your filters.</p>
        </div>
      )}

      <div className="flex items-center gap-1 text-[10px] text-[#9CA3AF]">
        <span>Back to:</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="font-medium text-[#2563EB] hover:underline">Overview</button>
        <span>|</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Unified Dashboard</button>
      </div>
    </div>
  );
}

export function DocumentationIntelligence() {
  return (
    <ErrorBoundary>
      <DocumentationIntelligenceInner />
    </ErrorBoundary>
  );
}
