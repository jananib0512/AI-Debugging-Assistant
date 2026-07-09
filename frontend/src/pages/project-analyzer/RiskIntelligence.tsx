import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Bug,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  X,
} from "lucide-react";
import { getRiskIntelligence } from "@/lib/project-analyzer";
import type {
  RiskIntelligenceResponse,
  RiskItem,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const riskColor = (v: number) =>
  v >= 70 ? "text-[#DC2626]" : v >= 40 ? "text-[#D97706]" : v >= 20 ? "text-[#2563EB]" : "text-[#059669]";

const riskBg = (v: number) =>
  v >= 70 ? "bg-[#DC2626]" : v >= 40 ? "bg-[#D97706]" : v >= 20 ? "bg-[#2563EB]" : "bg-[#059669]";

const riskLevelBadge: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFFBEB] text-[#92400E]",
  medium: "bg-[#EFF6FF] text-[#1E40AF]",
  low: "bg-[#ECFDF5] text-[#065F46]",
  informational: "bg-[#F3F4F6] text-[#6B7280]",
};

const typeLabels: Record<string, string> = {
  "circular-dependency": "Circular Dependency",
  "broken-dependency": "Broken Dependency",
  "dead-code": "Dead Code",
  "deep-call-chain": "Deep Call Chain",
  "high-coupling": "High Coupling",
  "low-cohesion": "Low Cohesion",
  "large-function": "Large Function",
  "large-class": "Large Class",
  "high-complexity": "High Complexity",
  "configuration-risk": "Configuration Risk",
  "entry-point-risk": "Entry Point Risk",
  "security-hotspot": "Security Hotspot",
  "performance-hotspot": "Performance Hotspot",
  "architecture-risk": "Architecture Risk",
};

function RiskGauge({ value, label }: { value: number; label: string }) {
  const color = riskColor(value);
  const bg = riskBg(value);
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-20 w-20">
        <svg className="h-20 w-20 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="34" fill="none" stroke="#F3F4F6" strokeWidth="6" />
          <circle
            cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="6"
            strokeDasharray={`${2 * Math.PI * 34}`}
            strokeDashoffset={`${2 * Math.PI * 34 * (1 - value / 100)}`}
            strokeLinecap="round" className={bg.replace("bg-", "text-")}
          />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center text-lg font-bold ${color}`}>
          {Math.round(value)}
        </span>
      </div>
      <p className="text-[9px] font-medium text-[#6B7280] text-center">{label}</p>
    </div>
  );
}

function RiskBar({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-32 text-[10px] font-medium text-[#6B7280] truncate">{label}</span>
      <div className="h-2 flex-1 rounded-full bg-[#F3F4F6] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${riskBg(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`w-8 text-right text-[10px] font-semibold ${riskColor(value)}`}>
        {Math.round(value)}
      </span>
    </div>
  );
}

export function RiskIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<RiskIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedRisk, setSelectedRisk] = useState<RiskItem | null>(null);
  const [sortBy, setSortBy] = useState<string>("severity");
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getRiskIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load risk intelligence",
      );
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const filteredRisks = useMemo(() => {
    if (!data) return [];
    let list = [...data.risks];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.type.toLowerCase().includes(q) ||
          r.detail.toLowerCase().includes(q) ||
          r.affected_files.some((f) => f.toLowerCase().includes(q)) ||
          r.affected_classes.some((c) => c.toLowerCase().includes(q)),
      );
    }
    if (severityFilter !== "all") {
      list = list.filter((r) => r.severity === severityFilter);
    }
    if (typeFilter !== "all") {
      list = list.filter((r) => r.type === typeFilter);
    }
    const sortOrder: Record<string, number> = {
      critical: 0, high: 1, medium: 2, low: 3, informational: 4,
    };
    if (sortBy === "severity") {
      list.sort((a, b) => (sortOrder[a.severity] ?? 5) - (sortOrder[b.severity] ?? 5));
    } else if (sortBy === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === "type") {
      list.sort((a, b) => a.type.localeCompare(b.type));
    }
    return list;
  }, [data, searchQuery, severityFilter, typeFilter, sortBy]);

  const uniqueTypes = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.risks.map((r) => r.type))].sort();
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading risk intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Failed to load</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button
          onClick={fetchData}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <ShieldAlert className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No risk data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to generate risk intelligence.</p>
      </div>
    );
  }

  const rs = data.risk_score;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      <div className="flex items-center gap-2">
        {projectId && (
          <>
            <button
              onClick={() => navigate(`/projects/${projectId}/analyzer`)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]"
            >
              ← Back to Overview
            </button>
            <span className="text-[#D1D5DB]">|</span>
            <button
              onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]"
            >
              Back to Unified Dashboard
            </button>
          </>
        )}
      </div>

      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#DC2626] to-[#991B1B]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <ShieldAlert className="h-3.5 w-3.5" /> Project Risk Analysis
          </div>
          <p className="mt-1 text-2xl font-bold">Project Risks</p>
          <p className="mt-1 text-sm text-white/80">
            Enterprise-grade risk scoring, heatmaps, AI summaries, and prioritized recommendations.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className={`rounded-lg border p-3 text-center ${riskLevelBadge[rs.risk_level] || "bg-[#F3F4F6]"}`}>
          <p className={`text-lg font-bold ${riskColor(rs.overall_risk)}`}>{Math.round(rs.overall_risk)}</p>
          <p className="text-[9px] font-medium opacity-70">Risk Score</p>
          <span className="mt-1 inline-block rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase">
            {rs.risk_level}
          </span>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className="text-lg font-bold text-[#111827]">{data.summary.critical_count}</p>
          <p className="text-[9px] text-[#DC2626] font-medium">Critical</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className="text-lg font-bold text-[#111827]">{data.summary.high_count}</p>
          <p className="text-[9px] text-[#D97706] font-medium">High</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className="text-lg font-bold text-[#111827]">{data.summary.medium_count}</p>
          <p className="text-[9px] text-[#2563EB] font-medium">Medium</p>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className="text-lg font-bold text-[#111827]">{data.summary.low_count}</p>
          <p className="text-[9px] text-[#059669] font-medium">Low</p>
        </div>
      </div>

      {/* Risk Score Gauges + Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className={sectionClass + " p-4"}>
          <p className="text-xs font-semibold text-[#374151] mb-3">Risk Score Breakdown</p>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <RiskGauge value={rs.overall_risk} label="Overall Risk" />
            <RiskGauge value={rs.project_stability} label="Stability" />
            <RiskGauge value={rs.confidence_score} label="Confidence" />
          </div>
          <div className="space-y-1.5">
            <RiskBar value={rs.maintainability_risk} label="Maintainability" />
            <RiskBar value={rs.architecture_risk} label="Architecture" />
            <RiskBar value={rs.dependency_risk} label="Dependency" />
            <RiskBar value={rs.security_risk} label="Security" />
            <RiskBar value={rs.performance_risk} label="Performance" />
          </div>
        </div>

        <div className={sectionClass + " p-4"}>
          <p className="text-xs font-semibold text-[#374151] mb-3">Risk by Type</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(function () {
              if (!data) return null;
              const byType: Record<string, RiskItem[]> = {};
              const risks = data.risks;
              risks.forEach((r) => {
                if (!byType[r.type]) byType[r.type] = [];
                byType[r.type]!.push(r);
              });
              return Object.entries(byType)
                .sort(([, a], [, b]) => b.length - a.length)
                .map(([type, items]) => (
                  <div key={type} className="flex items-center justify-between rounded-lg bg-[#FAFAFA] px-3 py-2">
                    <div className="flex items-center gap-2">
                      <span className={`h-2 w-2 rounded-full ${
                        items.some((i) => i.severity === "critical") ? "bg-[#DC2626]"
                        : items.some((i) => i.severity === "high") ? "bg-[#D97706]"
                        : "bg-[#2563EB]"
                      }`} />
                      <span className="text-[10px] font-medium text-[#374151]">{typeLabels[type] || type}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] text-[#6B7280]">{items.length}</span>
                      {items.some((i) => i.severity === "critical") && (
                        <span className="h-1.5 w-1.5 rounded-full bg-[#DC2626]" />
                      )}
                    </div>
                  </div>
                ));
            })()}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      <div className={sectionClass + " p-4"}>
        <div className="flex items-center gap-1.5 mb-2">
          <Lightbulb className="h-3.5 w-3.5 text-[#D97706]" />
          <span className="text-xs font-semibold text-[#374151]">AI Risk Summary</span>
        </div>
        <p className="text-[10px] text-[#6B7280] leading-relaxed">{data.summary.summary_text}</p>
        {data.summary.prioritized_recommendations.length > 0 && (
          <div className="mt-3 space-y-1">
            <p className="text-[9px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Prioritized Recommendations</p>
            <div className="space-y-1">
              {data.summary.prioritized_recommendations.slice(0, 8).map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2 text-[9px] text-[#6B7280]">
                  <span className={`mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                    rec.startsWith("[CRITICAL]") ? "bg-[#DC2626]"
                    : rec.startsWith("[HIGH]") ? "bg-[#D97706]"
                    : "bg-[#2563EB]"
                  }`} />
                  {rec}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Heatmap */}
      {data.heatmap.length > 0 && (
        <div className={sectionClass + " p-4"}>
          <p className="text-xs font-semibold text-[#374151] mb-3">Risk Heatmap ({data.heatmap.length} items)</p>
          <div className="flex flex-wrap gap-1.5 mb-3">
            <span className="flex items-center gap-1 text-[9px]"><span className="h-2.5 w-2.5 rounded-full bg-[#DC2626]" /> Critical</span>
            <span className="flex items-center gap-1 text-[9px]"><span className="h-2.5 w-2.5 rounded-full bg-[#D97706]" /> High</span>
            <span className="flex items-center gap-1 text-[9px]"><span className="h-2.5 w-2.5 rounded-full bg-[#2563EB]" /> Medium</span>
            <span className="flex items-center gap-1 text-[9px]"><span className="h-2.5 w-2.5 rounded-full bg-[#059669]" /> Low</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {data.heatmap.slice(0, 30).map((item) => (
              <div
                key={item.path}
                className={`rounded-lg border p-2 text-center transition-colors ${
                  item.risk_level === "critical" ? "border-[#FECACA] bg-[#FEF2F2]"
                  : item.risk_level === "high" ? "border-[#FDE68A] bg-[#FFFBEB]"
                  : item.risk_level === "medium" ? "border-[#BFDBFE] bg-[#EFF6FF]"
                  : "border-[#E5E7EB] bg-[#FAFAFA]"
                }`}
              >
                <p className="text-[9px] font-medium text-[#111827] truncate" title={item.name}>
                  {item.name}
                </p>
                <p className={`text-[10px] font-bold ${riskColor(item.risk_score)}`}>
                  {Math.round(item.risk_score)}
                </p>
                <span className="inline-block mt-0.5 rounded px-1 py-0.5 text-[7px] font-medium uppercase tracking-wider bg-white/60">
                  {item.risk_level}
                </span>
                {item.top_risks.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-0.5 justify-center">
                    {item.top_risks.slice(0, 3).map((tr) => (
                      <span key={tr} className="rounded bg-white/40 px-1 py-0.5 text-[7px] text-[#6B7280]">
                        {typeLabels[tr] || tr}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search, Filter, Sort */}
      <div className={sectionClass + " p-4"}>
        <div className="flex items-center gap-2 mb-3">
          <Bug className="h-3.5 w-3.5 text-[#6B7280]" />
          <p className="text-xs font-semibold text-[#374151]">Risk List ({filteredRisks.length})</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-1 min-w-[200px] rounded-lg border border-[#E5E7EB] px-2.5 py-1.5">
            <Search className="h-3 w-3 text-[#9CA3AF]" />
            <input
              type="text"
              placeholder="Search risks by name, type, file, class..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 border-0 bg-transparent text-[10px] text-[#111827] placeholder-[#9CA3AF] outline-none"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="text-[#9CA3AF] hover:text-[#DC2626]">
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Informational</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none"
          >
            <option value="all">All Types</option>
            {uniqueTypes.map((t) => (
              <option key={t} value={t}>{typeLabels[t] || t}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none"
          >
            <option value="severity">Sort: Severity</option>
            <option value="name">Sort: Name</option>
            <option value="type">Sort: Type</option>
          </select>
        </div>

        {/* Risk List */}
        {filteredRisks.length > 0 ? (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {filteredRisks.map((risk, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedRisk(selectedRisk === risk ? null : risk)}
                className={`w-full flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-colors ${
                  selectedRisk === risk
                    ? "border-[#2563EB] bg-[#EFF6FF]"
                    : "border-[#E5E7EB] hover:bg-[#FAFAFA]"
                }`}
              >
                <div className="shrink-0">
                  {selectedRisk === risk ? (
                    <ChevronDown className="h-3 w-3 text-[#6B7280]" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-[#6B7280]" />
                  )}
                </div>
                <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${
                  riskLevelBadge[risk.severity] || riskLevelBadge.low
                }`}>
                  {risk.severity}
                </span>
                <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                  {typeLabels[risk.type] || risk.type}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-medium text-[#111827] truncate">{risk.name}</p>
                  {risk.affected_files.length > 0 && (
                    <p className="text-[8px] text-[#6B7280] truncate">
                      {risk.affected_files.slice(0, 2).join(", ")}
                      {risk.affected_files.length > 2 && ` +${risk.affected_files.length - 2} more`}
                    </p>
                  )}
                </div>
                {risk.affected_files.length > 0 && (
                  <span className="text-[8px] text-[#9CA3AF] shrink-0">{risk.affected_files.length} file(s)</span>
                )}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
            <ShieldCheck className="mb-2 h-6 w-6" />
            {searchQuery || severityFilter !== "all" || typeFilter !== "all"
              ? "No risks match your search/filter criteria."
              : "No risks detected — project is in good health."}
          </div>
        )}

        {/* Detail Panel */}
        {selectedRisk && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-3 rounded-lg border border-[#2563EB] bg-[#EFF6FF] p-4"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${
                    riskLevelBadge[selectedRisk.severity] || riskLevelBadge.low
                  }`}>
                    {selectedRisk.severity}
                  </span>
                  <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                    {typeLabels[selectedRisk.type] || selectedRisk.type}
                  </span>
                </div>
                <p className="mt-1 text-xs font-semibold text-[#111827]">{selectedRisk.name}</p>
              </div>
              <button
                onClick={() => setSelectedRisk(null)}
                className="rounded p-1 text-[#6B7280] hover:text-[#DC2626] hover:bg-[#FEF2F2]"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="space-y-2 text-[10px] text-[#374151]">
              {selectedRisk.detail && (
                <p className="leading-relaxed">{selectedRisk.detail}</p>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                <div className="rounded-lg bg-white/60 p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Business Impact</p>
                  <p className="text-[10px] leading-relaxed">{selectedRisk.impact.business_impact}</p>
                </div>
                <div className="rounded-lg bg-white/60 p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Technical Impact</p>
                  <p className="text-[10px] leading-relaxed">{selectedRisk.impact.technical_impact}</p>
                </div>
              </div>

              {selectedRisk.affected_files.length > 0 && (
                <div>
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                    Affected Files ({selectedRisk.affected_files.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedRisk.affected_files.map((f) => (
                      <span key={f} className="rounded bg-white/60 px-2 py-1 text-[9px] font-mono text-[#1E40AF]">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedRisk.affected_classes.length > 0 && (
                <div>
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                    Affected Classes ({selectedRisk.affected_classes.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedRisk.affected_classes.map((c) => (
                      <span key={c} className="rounded bg-white/60 px-2 py-1 text-[9px] font-medium text-[#6B7280]">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedRisk.affected_functions.length > 0 && (
                <div>
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                    Affected Functions ({selectedRisk.affected_functions.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedRisk.affected_functions.map((fn) => (
                      <span key={fn} className="rounded bg-white/60 px-2 py-1 text-[9px] font-mono text-[#6B7280]">
                        {fn}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedRisk.recommendation && (
                <div className="rounded-lg bg-[#ECFDF5] border border-[#A7F3D0] p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#059669] mb-0.5">Recommendation</p>
                  <p className="text-[10px] text-[#065F46]">{selectedRisk.recommendation}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>

      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="risk-intelligence" />
      )}
    </motion.div>
  );
}

export default RiskIntelligence;
