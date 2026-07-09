import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ChevronDown,
  ChevronRight,
  Code2,
  GitCompare,
  Lightbulb,
  RefreshCw,
  Search,
} from "lucide-react";
import { getRefactoringIntelligence } from "@/lib/project-analyzer";
import type { RefactoringIntelligenceResponse, RefactoringOpportunity, RefactoringScore, RefactoringSummary } from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";
import { ErrorBoundary } from "@/components/project-analyzer/ErrorBoundary";

const severityColors: Record<string, string> = {
  critical: "bg-red-50 text-red-700 border-red-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-blue-50 text-blue-700 border-blue-200",
  informational: "bg-gray-50 text-gray-600 border-gray-200",
};

const typeLabels: Record<string, string> = {
  "extract-class": "Extract Class",
  "extract-method": "Extract Method",
  "extract-interface": "Extract Interface",
  "split-service": "Split Service",
  "split-controller": "Split Controller",
  "split-module": "Split Module",
  "merge-duplicate": "Merge Duplicate",
  "remove-dead-code": "Remove Dead Code",
  "rename-identifier": "Rename Identifier",
  "reduce-coupling": "Reduce Coupling",
  "increase-cohesion": "Increase Cohesion",
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

function OppCard({ opp, selected, onToggle }: { opp: RefactoringOpportunity; selected: boolean; onToggle: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition-all hover:shadow-md cursor-pointer"
      onClick={onToggle}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`rounded-md border px-2 py-0.5 text-[10px] font-medium ${severityColors[opp.severity] || severityColors.low}`}>
              {(opp.severity || "low").toUpperCase()}
            </span>
            <span className="rounded-md bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">
              {typeLabels[opp.type] || opp.type || "unknown"}
            </span>
            <span className="truncate text-sm font-medium text-[#111827]">{opp.name || "Unnamed"}</span>
          </div>
          <p className="mt-1 text-xs text-[#6B7280] line-clamp-2">{opp.description || ""}</p>
        </div>
        <ChevronDown className={`mt-1 h-4 w-4 flex-shrink-0 text-[#9CA3AF] transition-transform ${selected ? "rotate-180" : ""}`} />
      </div>

      {selected && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="mt-4 space-y-3 border-t border-[#E5E7EB] pt-4"
        >
          {opp.reason && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Reason</p>
              <p className="mt-1 text-xs text-[#4B5563]">{opp.reason}</p>
            </div>
          )}
          {(opp.affected_files || []).length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Files</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {(opp.affected_files || []).map((f, fi) => (
                  <span key={fi} className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[10px] text-[#6B7280]">{f}</span>
                ))}
              </div>
            </div>
          )}
          {(opp.affected_classes || []).length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Classes</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {(opp.affected_classes || []).map((c, ci) => (
                  <span key={ci} className="rounded bg-[#EEF2FF] px-2 py-0.5 text-[10px] text-[#4338CA]">{c}</span>
                ))}
              </div>
            </div>
          )}
          {(opp.affected_functions || []).length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected Functions</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {(opp.affected_functions || []).map((fn, fi) => (
                  <span key={fi} className="rounded bg-[#F0FDF4] px-2 py-0.5 text-[10px] text-[#166534]">{fn}</span>
                ))}
              </div>
            </div>
          )}
          {opp.recommendation && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Recommendation</p>
              <p className="mt-1 text-xs text-[#2563EB]">{opp.recommendation}</p>
            </div>
          )}
          {opp.impact && (
            <div className="grid gap-3 sm:grid-cols-2">
              {opp.expected_benefit && (
                <div className="rounded-lg bg-[#F9FAFB] p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Expected Benefits</p>
                  <p className="mt-1 text-xs text-[#4B5563]">{opp.expected_benefit}</p>
                </div>
              )}
              <div className="rounded-lg bg-[#F9FAFB] p-3">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Impact Estimate</p>
                <div className="mt-1 space-y-0.5 text-xs text-[#4B5563]">
                  <p>Files changed: {opp.impact.estimated_files_changed ?? 0}</p>
                  <p>Complexity reduction: {opp.impact.estimated_complexity_reduction || "N/A"}</p>
                  <p>Maintainability: {opp.impact.estimated_maintainability_improvement || "N/A"}</p>
                  <p>Risk: {opp.impact.estimated_risk || "N/A"}</p>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}

function RefactoringIntelligenceInner() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<RefactoringIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortBy, setSortBy] = useState("severity");
  const [selectedOpp, setSelectedOpp] = useState<RefactoringOpportunity | null>(null);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getRefactoringIntelligence(Number(projectId));
      console.debug("RefactoringIntelligence data:", res);
      setData(res);
    } catch (err) {
      console.error("RefactoringIntelligence fetch error:", err);
      setError("Failed to load refactoring intelligence.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const uniqueTypes = useMemo(() => {
    if (!data) return [];
    const types = new Set((data.opportunities || []).map((o) => o.type));
    return Array.from(types).sort();
  }, [data]);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const o of (data?.opportunities || [])) {
      const t = o.type || "unknown";
      counts[t] = (counts[t] || 0) + 1;
    }
    return counts;
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let list = [...(data.opportunities || [])];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (o) =>
          (o.name || "").toLowerCase().includes(q) ||
          (o.description || "").toLowerCase().includes(q) ||
          (o.affected_files || []).some((f) => (f || "").toLowerCase().includes(q)) ||
          (o.affected_classes || []).some((c) => (c || "").toLowerCase().includes(q)) ||
          (o.affected_functions || []).some((f) => (f || "").toLowerCase().includes(q)),
      );
    }
    if (severityFilter !== "all") {
      list = list.filter((o) => o.severity === severityFilter);
    }
    if (typeFilter !== "all") {
      list = list.filter((o) => o.type === typeFilter);
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

  const score: RefactoringScore = (data?.refactoring_score || {}) as RefactoringScore;
  const summary: RefactoringSummary = (data?.summary || {}) as RefactoringSummary;

  const gaugeConfigs = [
    { label: "Refactoring Score", value: score.refactoring_score ?? 0, stroke: "#2563EB" },
    { label: "Cleanliness", value: score.project_cleanliness ?? 0, stroke: "#059669" },
    { label: "Code Organization", value: score.code_organization ?? 0, stroke: "#7C3AED" },
    { label: "Debt Reduction Potential", value: score.debt_reduction_potential ?? 0, stroke: "#DC2626" },
    { label: "Refactoring Readiness", value: score.refactoring_readiness ?? 0, stroke: "#D97706" },
    { label: "AI Confidence", value: score.ai_confidence ?? 0, stroke: "#0891B2" },
  ];

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

  if (!data.opportunities || data.opportunities.length === 0) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 text-white shadow-lg">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#2563EB]/20">
              <GitCompare className="h-6 w-6 text-[#60A5FA]" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Code Improvement</h1>
              <p className="mt-1 text-xs text-[#94A3B8]">
                Automated structural improvement analysis and refactoring recommendations
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-center gap-3 rounded-xl border border-[#E5E7EB] bg-white py-16 text-center shadow-sm">
          <Code2 className="h-10 w-10 text-[#D1D5DB]" />
          <p className="text-sm font-medium text-[#6B7280]">No refactoring opportunities detected.</p>
          <p className="text-xs text-[#9CA3AF]">Run project analysis to generate refactoring intelligence.</p>
        </div>
        <RelatedAnalysisNav projectId={projectId!} currentPage="refactoring-intelligence" />
        <div className="flex items-center gap-1 text-[10px] text-[#9CA3AF]">
          <span>Back to:</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="font-medium text-[#2563EB] hover:underline">Overview</button>
          <span>|</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Unified Dashboard</button>
          <span>|</span>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer/maintainability-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Maintainability Intel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 text-white shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#2563EB]/20">
            <GitCompare className="h-6 w-6 text-[#60A5FA]" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Code Improvement</h1>
            <p className="mt-1 text-xs text-[#94A3B8]">
              Automated structural improvement analysis and refactoring recommendations
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#94A3B8]">
          <span className="rounded-md bg-white/5 px-2 py-1">
            {(data.opportunities || []).length} opportunities found
          </span>
          <span className="rounded-md bg-white/5 px-2 py-1">
            Score: {(score.refactoring_score ?? 0).toFixed(0)}/100
          </span>
          <span className="rounded-md bg-white/5 px-2 py-1">
            Risk: {score.risk_level || "unknown"}
          </span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {gaugeConfigs.map((g) => (
          <GaugeCard key={g.label} label={g.label} value={g.value} stroke={g.stroke} />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <AlertTriangle className="h-3.5 w-3.5 text-red-500" /> Critical
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.critical_count ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <ArrowUp className="h-3.5 w-3.5 text-orange-500" /> High Priority
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.high_count ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <ChevronRight className="h-3.5 w-3.5 text-yellow-500" /> Medium
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.medium_count ?? 0}</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <ArrowDown className="h-3.5 w-3.5 text-blue-500" /> Low Priority
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.low_count ?? 0}</p>
        </div>
      </div>

      {summary.summary_text && (
        <div className="flex items-start gap-3 rounded-xl border border-[#E5E7EB] bg-gradient-to-r from-[#EFF6FF] to-white p-4 shadow-sm">
          <Lightbulb className="mt-0.5 h-5 w-5 text-[#2563EB]" />
          <div>
            <p className="text-sm font-medium text-[#111827]">AI Refactoring Summary</p>
            <p className="mt-1 text-xs text-[#4B5563]">{summary.summary_text}</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Refactoring by Type
          </p>
          <div className="space-y-2">
            {Object.entries(typeCounts).slice(0, 8).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between rounded-lg bg-[#F9FAFB] px-3 py-2">
                <span className="text-xs font-medium text-[#374151]">
                  {typeLabels[type] || type.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
                <span className="rounded bg-[#EFF6FF] px-2 py-0.5 text-[10px] font-medium text-[#2563EB]">
                  {count}
                </span>
              </div>
            ))}
            {Object.keys(typeCounts).length === 0 && (
              <p className="text-xs text-[#9CA3AF]">No refactoring opportunities detected.</p>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Refactoring Roadmap
          </p>
          <div className="max-h-64 space-y-1.5 overflow-y-auto">
            {(summary.roadmap || []).map((item, i) => (
              <div key={i} className="rounded bg-[#F9FAFB] px-3 py-2 text-[11px] leading-relaxed text-[#4B5563]">
                {item}
              </div>
            ))}
            {(summary.roadmap || []).length === 0 && (
              <p className="text-xs text-[#9CA3AF]">No roadmap items.</p>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
        <div className="relative flex-1" style={{ minWidth: "200px" }}>
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#9CA3AF]" />
          <input
            type="text"
            placeholder="Search by name, file, class, function..."
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
            <option key={t} value={t}>{typeLabels[t] || t}</option>
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

      <RelatedAnalysisNav projectId={projectId!} currentPage="refactoring-intelligence" />

      {filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map((opp, i) => (
            <OppCard
              key={i}
              opp={opp}
              selected={selectedOpp === opp}
              onToggle={() => setSelectedOpp(selectedOpp === opp ? null : opp)}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-12 text-center">
          <Code2 className="h-8 w-8 text-[#D1D5DB]" />
          <p className="text-sm text-[#6B7280]">No refactoring opportunities match your filters.</p>
        </div>
      )}

      <div className="flex items-center gap-1 text-[10px] text-[#9CA3AF]">
        <span>Back to:</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="font-medium text-[#2563EB] hover:underline">Overview</button>
        <span>|</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Unified Dashboard</button>
        <span>|</span>
        <button onClick={() => navigate(`/projects/${projectId}/analyzer/maintainability-intelligence`)} className="font-medium text-[#2563EB] hover:underline">Maintainability Intel</button>
      </div>
    </div>
  );
}

export function RefactoringIntelligence() {
  return (
    <ErrorBoundary>
      <RefactoringIntelligenceInner />
    </ErrorBoundary>
  );
}
