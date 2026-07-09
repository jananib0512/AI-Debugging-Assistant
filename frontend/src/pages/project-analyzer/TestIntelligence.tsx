import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  ChevronDown,
  FileText,
  FlaskConical,
  Lightbulb,
  RefreshCw,
  Search,
  ShieldCheck,
  TestTube,
  XCircle,
} from "lucide-react";
import { getTestIntelligence } from "@/lib/project-analyzer";
import type {
  TestIntelligenceResponse,
  TestScore,
  TestSummary,
  UntestedComponent,
  MissingTestCase,
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

const riskColors: Record<string, string> = {
  critical: "bg-red-50 text-red-700 border-red-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-blue-50 text-blue-700 border-blue-200",
};

const qualityColors: Record<string, string> = {
  good: "bg-green-50 text-green-700 border-green-200",
  average: "bg-yellow-50 text-yellow-700 border-yellow-200",
  poor: "bg-red-50 text-red-700 border-red-200",
  unknown: "bg-gray-50 text-gray-600 border-gray-200",
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


function TestIntelligenceInner() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<TestIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [sortBy, setSortBy] = useState("priority");
  const [selectedItem, setSelectedItem] = useState<UntestedComponent | MissingTestCase | null>(null);
  const [viewMode, setViewMode] = useState<"untested" | "missing" | "files" | "recommendations">("untested");

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getTestIntelligence(Number(projectId));
      setData(res);
    } catch {
      setError("Failed to load test intelligence.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const score: TestScore = (data?.test_score || {}) as TestScore;
  const summary: TestSummary = (data?.summary || {}) as TestSummary;

  const gaugeConfigs = useMemo(() => [
    { label: "Test Score", value: score.overall_test_score ?? 0, stroke: "#2563EB" },
    { label: "Coverage", value: score.test_coverage ?? 0, stroke: "#059669" },
    { label: "Health", value: score.testing_health ?? 0, stroke: "#7C3AED" },
    { label: "Regression Readiness", value: score.regression_readiness ?? 0, stroke: "#D97706" },
    { label: "AI Confidence", value: score.ai_confidence ?? 0, stroke: "#0891B2" },
  ], [score]);

  const filteredUntested = useMemo(() => {
    if (!data) return [];
    let list = [...(data.untested_components || [])];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((u) =>
        (u.name || "").toLowerCase().includes(q) ||
        (u.path || "").toLowerCase().includes(q) ||
        (u.reason || "").toLowerCase().includes(q),
      );
    }
    if (filterSeverity !== "all") {
      list = list.filter((u) => u.risk === filterSeverity);
    }
    if (sortBy === "priority") {
      list.sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99));
    } else if (sortBy === "name") {
      list.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    } else if (sortBy === "risk") {
      const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
      list.sort((a, b) => (order[a.risk] ?? 4) - (order[b.risk] ?? 4));
    }
    return list;
  }, [data, search, filterSeverity, sortBy]);

  const filteredMissing = useMemo(() => {
    if (!data) return [];
    let list = [...(data.missing_test_cases || [])];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((m) =>
        (m.name || "").toLowerCase().includes(q) ||
        (m.module || "").toLowerCase().includes(q) ||
        (m.suggestion || "").toLowerCase().includes(q),
      );
    }
    if (filterSeverity !== "all") {
      list = list.filter((m) => m.severity === filterSeverity);
    }
    if (sortBy === "priority") {
      const order: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
      list.sort((a, b) => (order[a.severity] ?? 4) - (order[b.severity] ?? 4));
    } else if (sortBy === "name") {
      list.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    }
    return list;
  }, [data, search, filterSeverity, sortBy]);

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

  return (
    <div className="space-y-6">
      <div className="rounded-xl bg-gradient-to-br from-[#0F172A] via-[#1E293B] to-[#0F172A] p-6 text-white shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#059669]/20">
            <FlaskConical className="h-6 w-6 text-[#34D399]" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Testing</h1>
            <p className="mt-1 text-xs text-[#94A3B8]">
              Enterprise test coverage analysis, quality metrics, and gap detection
            </p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#94A3B8]">
          <span className="rounded-md bg-white/5 px-2 py-1">
            Score: {score.overall_test_score.toFixed(0)}/100
          </span>
          <span className="rounded-md bg-white/5 px-2 py-1">
            Frameworks: {summary.detected_frameworks?.join(", ") || "none detected"}
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
            <TestTube className="h-3.5 w-3.5 text-[#2563EB]" /> Test Files
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.total_test_files}</p>
          <p className="text-[10px] text-[#9CA3AF]">{summary.total_test_functions} test functions</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" /> Assertions
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{summary.total_assertions ?? 0}</p>
          <p className="text-[10px] text-[#9CA3AF]">{summary.total_fixtures} fixtures, {summary.total_mocks} mocks</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <Bug className="h-3.5 w-3.5 text-orange-500" /> Untested Components
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{(data.untested_components || []).length}</p>
          <p className="text-[10px] text-[#9CA3AF]">{summary.untested_functions} functions uncovered</p>
        </div>
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-[#6B7280]">
            <XCircle className="h-3.5 w-3.5 text-red-500" /> Missing Test Cases
          </div>
          <p className="mt-1 text-2xl font-bold text-[#111827]">{(data.missing_test_cases || []).length}</p>
          <p className="text-[10px] text-[#9CA3AF]">high-priority gaps</p>
        </div>
      </div>

      {summary.summary_text && (
        <div className="flex items-start gap-3 rounded-xl border border-[#E5E7EB] bg-gradient-to-r from-[#ECFDF5] to-white p-4 shadow-sm">
          <Lightbulb className="mt-0.5 h-5 w-5 text-[#059669]" />
          <div>
            <p className="text-sm font-medium text-[#111827]">AI Test Summary</p>
            <p className="mt-1 text-xs text-[#4B5563]">{summary.summary_text}</p>
          </div>
        </div>
      )}

      {data.detected_frameworks && data.detected_frameworks.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#9CA3AF]">
            Detected Testing Frameworks
          </p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {data.detected_frameworks.map((fw, i) => (
              <div key={i} className="rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-[#111827]">{fw.name}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[9px] font-medium ${qualityColors[fw.reliability] || qualityColors.unknown}`}>
                    {fw.reliability}
                  </span>
                </div>
                <p className="mt-1 text-[10px] text-[#6B7280]">
                  {fw.type} {fw.version ? `v${fw.version}` : ""}
                </p>
                {fw.config_file && (
                  <p className="text-[10px] text-[#9CA3AF]">Config: {fw.config_file}</p>
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
            placeholder="Search by name, path, or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-[#E5E7EB] py-2 pl-9 pr-3 text-xs outline-none focus:border-[#2563EB]"
          />
        </div>
        <button
          onClick={() => setViewMode("untested")}
          className={`rounded-lg border px-3 py-2 text-xs font-medium ${viewMode === "untested" ? "border-[#2563EB] bg-[#EFF6FF] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]"}`}
        >
          Untested
        </button>
        <button
          onClick={() => setViewMode("missing")}
          className={`rounded-lg border px-3 py-2 text-xs font-medium ${viewMode === "missing" ? "border-[#2563EB] bg-[#EFF6FF] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]"}`}
        >
          Missing Tests
        </button>
        <button
          onClick={() => setViewMode("files")}
          className={`rounded-lg border px-3 py-2 text-xs font-medium ${viewMode === "files" ? "border-[#2563EB] bg-[#EFF6FF] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]"}`}
        >
          Test Files
        </button>
        <button
          onClick={() => setViewMode("recommendations")}
          className={`rounded-lg border px-3 py-2 text-xs font-medium ${viewMode === "recommendations" ? "border-[#2563EB] bg-[#EFF6FF] text-[#2563EB]" : "border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]"}`}
        >
          Recommendations
        </button>
        {viewMode !== "files" && viewMode !== "recommendations" && (
          <>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs outline-none focus:border-[#2563EB]"
            >
              <option value="all">All Risks</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] px-3 py-2 text-xs outline-none focus:border-[#2563EB]"
            >
              <option value="priority">Sort: Priority</option>
              <option value="name">Sort: Name</option>
              <option value="risk">Sort: Risk</option>
            </select>
          </>
        )}
      </div>

      <RelatedAnalysisNav projectId={projectId!} currentPage="test-intelligence" />

      {/* Untested Components */}
      {viewMode === "untested" && (
        <>
          {filteredUntested.length > 0 ? (
            <div className="space-y-2">
              {filteredUntested.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="cursor-pointer rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition-all hover:shadow-md"
                  onClick={() => setSelectedItem(selectedItem === item ? null : item)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`rounded-md border px-2 py-0.5 text-[10px] font-medium ${riskColors[item.risk] || severityColors.medium}`}>
                          {(item.risk || "medium").toUpperCase()}
                        </span>
                        <span className="rounded-md bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">
                          {item.type}
                        </span>
                        <span className="truncate text-sm font-medium text-[#111827]">{item.name}</span>
                      </div>
                      <p className="mt-1 text-xs text-[#6B7280] line-clamp-2">{item.reason || ""}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className="rounded-md bg-[#F0FDF4] px-2 py-0.5 text-[10px] font-medium text-[#166534]">
                        {item.suggested_test_type || "unit"}
                      </span>
                      <ChevronDown className={`h-4 w-4 text-[#9CA3AF] transition-transform ${selectedItem === item ? "rotate-180" : ""}`} />
                    </div>
                  </div>

                  {selectedItem === item && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      transition={{ duration: 0.2 }}
                      className="mt-4 space-y-3 border-t border-[#E5E7EB] pt-4"
                    >
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Path</p>
                          <p className="mt-1 text-xs text-[#374151]">{item.path || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Priority</p>
                          <p className="mt-1 text-xs font-medium text-[#111827]">P{item.priority}</p>
                        </div>
                      </div>
                      <div className="rounded-lg bg-[#F9FAFB] p-3">
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Suggestion</p>
                        <p className="mt-1 text-xs font-medium text-[#2563EB]">
                          Write {item.suggested_test_type || "unit"} tests for {item.name}
                        </p>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <CheckCircle2 className="h-8 w-8 text-[#059669]" />
              <p className="text-sm font-medium text-[#6B7280]">All components have test coverage.</p>
            </div>
          )}
        </>
      )}

      {/* Missing Test Cases */}
      {viewMode === "missing" && (
        <>
          {filteredMissing.length > 0 ? (
            <div className="space-y-2">
              {filteredMissing.map((mc, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="cursor-pointer rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm transition-all hover:shadow-md"
                  onClick={() => setSelectedItem(selectedItem === mc ? null : mc)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`rounded-md border px-2 py-0.5 text-[10px] font-medium ${riskColors[mc.severity] || severityColors.medium}`}>
                          {(mc.severity || "medium").toUpperCase()}
                        </span>
                        <span className="rounded-md bg-[#EEF2FF] px-2 py-0.5 text-[10px] font-medium text-[#4338CA]">
                          {mc.type || "unit"}
                        </span>
                        <span className="truncate text-sm font-medium text-[#111827]">{mc.name}</span>
                      </div>
                      {mc.module && (
                        <p className="mt-1 text-xs text-[#6B7280]">Module: {mc.module}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {mc.estimated_impact && (
                        <span className="rounded-md bg-[#F0FDF4] px-2 py-0.5 text-[10px] font-medium text-[#166534]">
                          {mc.estimated_impact}
                        </span>
                      )}
                      <ChevronDown className={`h-4 w-4 text-[#9CA3AF] transition-transform ${selectedItem === mc ? "rotate-180" : ""}`} />
                    </div>
                  </div>

                  {selectedItem === mc && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      transition={{ duration: 0.2 }}
                      className="mt-4 space-y-3 border-t border-[#E5E7EB] pt-4"
                    >
                      {mc.affected_file && (
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Affected File</p>
                          <p className="mt-1 text-xs text-[#374151]">{mc.affected_file}</p>
                        </div>
                      )}
                      {mc.suggestion && (
                        <div className="rounded-lg bg-[#F9FAFB] p-3">
                          <p className="text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Suggestion</p>
                          <p className="mt-1 text-xs text-[#2563EB]">{mc.suggestion}</p>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <CheckCircle2 className="h-8 w-8 text-[#059669]" />
              <p className="text-sm font-medium text-[#6B7280]">No missing test cases identified.</p>
            </div>
          )}
        </>
      )}

      {/* Test Files */}
      {viewMode === "files" && (
        <>
          {data.test_files && data.test_files.length > 0 ? (
            <div className="space-y-2">
              {data.test_files.map((tf, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <FileText className="h-3.5 w-3.5 text-[#6B7280]" />
                        <span className="text-sm font-medium text-[#111827]">{tf.file_name}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[9px] font-medium ${qualityColors[tf.naming_quality] || qualityColors.unknown}`}>
                          {tf.naming_quality}
                        </span>
                      </div>
                      <p className="mt-0.5 text-[10px] text-[#6B7280]">{tf.path}</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[#6B7280]">
                      <span title="Framework">{tf.framework}</span>
                      <span title="Tests">{tf.test_count} tests</span>
                      <span title="Assertions">{tf.assertion_count} asserts</span>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(tf.test_types || []).map((tt, ti) => (
                      <span key={ti} className="rounded-md bg-[#F3F4F6] px-2 py-0.5 text-[9px] font-medium text-[#6B7280]">
                        {tt}
                      </span>
                    ))}
                    {tf.has_failures && (
                      <span className="rounded-md bg-red-50 px-2 py-0.5 text-[9px] font-medium text-red-600">
                        has failures
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <AlertTriangle className="h-8 w-8 text-orange-400" />
              <p className="text-sm font-medium text-[#6B7280]">No test files detected in the project.</p>
            </div>
          )}
        </>
      )}

      {/* Recommendations */}
      {viewMode === "recommendations" && (
        <>
          {data.recommendations && data.recommendations.length > 0 ? (
            <div className="space-y-2">
              {data.recommendations.map((rec, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="rounded-xl border border-[#E5E7EB] bg-white p-4 shadow-sm"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#ECFDF5]">
                      <ShieldCheck className="h-4 w-4 text-[#059669]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="rounded-md bg-[#F3F4F6] px-2 py-0.5 text-[10px] font-medium text-[#6B7280]">
                          P{rec.priority}
                        </span>
                        <span className="text-sm font-medium text-[#111827]">{rec.title}</span>
                      </div>
                      <p className="mt-1 text-xs text-[#6B7280]">{rec.description}</p>
                      {rec.suggested_framework && (
                        <p className="mt-1 text-[10px] text-[#2563EB]">
                          Suggested: {rec.suggested_framework}
                          {rec.estimated_coverage_improvement > 0 && ` (+${rec.estimated_coverage_improvement.toFixed(0)}% coverage)`}
                        </p>
                      )}
                      {rec.affected_modules && rec.affected_modules.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {rec.affected_modules.map((m, mi) => (
                            <span key={mi} className="rounded bg-[#F3F4F6] px-2 py-0.5 text-[9px] text-[#6B7280]">
                              {m}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <CheckCircle2 className="h-8 w-8 text-[#059669]" />
              <p className="text-sm font-medium text-[#6B7280]">No recommendations at this time.</p>
            </div>
          )}
        </>
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

export function TestIntelligence() {
  return (
    <ErrorBoundary>
      <TestIntelligenceInner />
    </ErrorBoundary>
  );
}
