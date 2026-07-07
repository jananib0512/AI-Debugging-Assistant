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
  Shield,
  ShieldCheck,
  ShieldAlert,
  X,
} from "lucide-react";
import { getSecurityIntelligence } from "@/lib/project-analyzer";
import type {
  SecurityIntelligenceResponse,
  SecurityFinding,
} from "@/types/project-analyzer";
import { RelatedAnalysisNav } from "@/components/project-analyzer/RelatedAnalysisNav";

const sectionClass = "rounded-xl border border-[#E5E7EB] bg-white";

const severityBadge: Record<string, string> = {
  critical: "bg-[#FEF2F2] text-[#991B1B]",
  high: "bg-[#FFFBEB] text-[#92400E]",
  medium: "bg-[#EFF6FF] text-[#1E40AF]",
  low: "bg-[#ECFDF5] text-[#065F46]",
  informational: "bg-[#F3F4F6] text-[#6B7280]",
};

const scoreColor = (v: number) =>
  v >= 70 ? "text-[#059669]" : v >= 40 ? "text-[#D97706]" : "text-[#DC2626]";

const scoreBg = (v: number) =>
  v >= 70 ? "bg-[#059669]" : v >= 40 ? "bg-[#D97706]" : "bg-[#DC2626]";

const typeLabels: Record<string, string> = {
  api_key: "Hardcoded API Key",
  password: "Hardcoded Password",
  token: "Hardcoded Token/Secret",
  aws_key: "AWS Access Key",
  private_key: "Private Key",
  connection_string: "Connection String",
  jwt_secret: "JWT Secret",
  npm_token: "NPM Auth Token",
  ssh_key_path: "SSH Key Reference",
  eval_usage: "Unsafe eval() Usage",
  exec_usage: "Unsafe exec() Usage",
  shell_injection: "Command Injection Risk",
  sql_injection: "SQL Injection Risk",
  xss_risk: "XSS Risk",
  path_traversal: "Path Traversal Risk",
  insecure_deserialization: "Unsafe Deserialization",
  debug_enabled: "Debug Mode Enabled",
  "insecure-configuration": "Insecure Configuration",
  "insecure-env": "Insecure Environment Variable",
  "env-file": "Environment File Detected",
  "missing-authentication": "Missing Authentication",
  "weak-authentication": "Weak Authentication",
  "missing-https": "Missing HTTPS",
  "missing-input-validation": "Missing Input Validation",
  "call-graph-security": "Call Graph Security Issue",
  "quality-security": "Code Quality Security",
};

function ScoreGauge({ value, label }: { value: number; label: string }) {
  const color = scoreColor(value);
  const bg = scoreBg(value);
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

export function SecurityIntelligence() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SecurityIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedFinding, setSelectedFinding] = useState<SecurityFinding | null>(null);
  const [showDeps, setShowDeps] = useState(false);
  const fetchedRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getSecurityIntelligence(Number(projectId));
      setData(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load security intelligence",
      );
    } finally {
      setLoading(false);
      fetchedRef.current = true;
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && !fetchedRef.current) fetchData();
  }, [projectId, fetchData]);

  const filteredFindings = useMemo(() => {
    if (!data) return [];
    let list = [...data.findings];
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.type.toLowerCase().includes(q) ||
          f.detail.toLowerCase().includes(q) ||
          f.affected_files.some((f2) => f2.toLowerCase().includes(q)),
      );
    }
    if (severityFilter !== "all") {
      list = list.filter((f) => f.severity === severityFilter);
    }
    if (typeFilter !== "all") {
      list = list.filter((f) => f.type === typeFilter);
    }
    const sortOrder: Record<string, number> = {
      critical: 0, high: 1, medium: 2, low: 3, informational: 4,
    };
    list.sort((a, b) => (sortOrder[a.severity] ?? 5) - (sortOrder[b.severity] ?? 5));
    return list;
  }, [data, searchQuery, severityFilter, typeFilter]);

  const uniqueTypes = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.findings.map((f) => f.type))].sort();
  }, [data]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading security intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Failed to load</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={fetchData} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <ShieldAlert className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No security data</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run project analysis to generate security intelligence.</p>
      </div>
    );
  }

  const ss = data.security_score;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5"
    >
      <div className="flex items-center gap-2">
        {projectId && (
          <>
            <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
              ← Back to Overview
            </button>
            <span className="text-[#D1D5DB]">|</span>
            <button onClick={() => navigate(`/projects/${projectId}/analyzer/unified-intelligence`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#2563EB] hover:text-[#1D4ED8]">
              Back to Unified Dashboard
            </button>
          </>
        )}
      </div>

      {/* Hero */}
      <div className="overflow-hidden rounded-xl bg-gradient-to-br from-[#1E40AF] to-[#1E3A5F]">
        <div className="px-6 py-8 text-white">
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-white/70">
            <Shield className="h-3.5 w-3.5" /> Security Intelligence Engine
          </div>
          <p className="mt-1 text-2xl font-bold">Security Intelligence</p>
          <p className="mt-1 text-sm text-white/80">
            Enterprise-grade security vulnerability detection, dependency auditing, and configuration analysis.
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className={`text-lg font-bold ${scoreColor(ss.overall_security_score)}`}>{Math.round(ss.overall_security_score)}</p>
          <p className="text-[9px] text-[#6B7280] font-medium">Security Score</p>
          <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[ss.risk_level] || severityBadge.low}`}>{ss.risk_level}</span>
        </div>
        <div className="rounded-lg border border-[#E5E7EB] p-3 text-center bg-white">
          <p className="text-lg font-bold text-[#991B1B]">{data.summary.critical_count}</p>
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

      {/* Score Breakdown + Finding Types */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className={sectionClass + " p-4"}>
          <p className="text-xs font-semibold text-[#374151] mb-3">Security Score Breakdown</p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <ScoreGauge value={ss.overall_security_score} label="Overall Score" />
            <ScoreGauge value={ss.security_health} label="Health" />
            <ScoreGauge value={ss.security_confidence} label="Confidence" />
            <ScoreGauge value={ss.security_readiness} label="Readiness" />
          </div>
        </div>

        <div className={sectionClass + " p-4"}>
          <p className="text-xs font-semibold text-[#374151] mb-3">Findings by Type</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {(function () {
              if (!data) return null;
              const byType: Record<string, SecurityFinding[]> = {};
              const findings = data.findings;
              findings.forEach((f) => {
                if (!byType[f.type]) byType[f.type] = [];
                byType[f.type]!.push(f);
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
          <span className="text-xs font-semibold text-[#374151]">AI Security Summary</span>
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

      {/* Dependency Security */}
      {data.dependency_issues.length > 0 && (
        <div className={sectionClass + " p-4"}>
          <button
            onClick={() => setShowDeps(!showDeps)}
            className="flex items-center gap-2 w-full"
          >
            {showDeps ? <ChevronDown className="h-3.5 w-3.5 text-[#6B7280]" /> : <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />}
            <Bug className="h-3.5 w-3.5 text-[#6B7280]" />
            <span className="text-xs font-semibold text-[#374151]">Dependency Security ({data.dependency_issues.length})</span>
          </button>
          {showDeps && (
            <div className="mt-3 space-y-1">
              {data.dependency_issues.map((dep, idx) => (
                <div key={idx} className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] px-3 py-2">
                  <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[dep.severity] || severityBadge.low}`}>
                    {dep.severity}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-medium text-[#111827]">{dep.name}</p>
                    <p className="text-[8px] text-[#6B7280]">{dep.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Findings List */}
      <div className={sectionClass + " p-4"}>
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert className="h-3.5 w-3.5 text-[#6B7280]" />
          <p className="text-xs font-semibold text-[#374151]">Security Findings ({filteredFindings.length})</p>
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-1 min-w-[200px] rounded-lg border border-[#E5E7EB] px-2.5 py-1.5">
            <Search className="h-3 w-3 text-[#9CA3AF]" />
            <input
              type="text"
              placeholder="Search by name, type, file..."
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
          <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none">
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-[#E5E7EB] px-2.5 py-1.5 text-[10px] font-medium text-[#374151] bg-white outline-none">
            <option value="all">All Types</option>
            {uniqueTypes.map((t) => (
              <option key={t} value={t}>{typeLabels[t] || t}</option>
            ))}
          </select>
        </div>

        {filteredFindings.length > 0 ? (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {filteredFindings.map((finding, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedFinding(selectedFinding === finding ? null : finding)}
                className={`w-full flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-colors ${
                  selectedFinding === finding
                    ? "border-[#1E40AF] bg-[#EFF6FF]"
                    : "border-[#E5E7EB] hover:bg-[#FAFAFA]"
                }`}
              >
                <div className="shrink-0">
                  {selectedFinding === finding ? (
                    <ChevronDown className="h-3 w-3 text-[#6B7280]" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-[#6B7280]" />
                  )}
                </div>
                <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[finding.severity] || severityBadge.low}`}>
                  {finding.severity}
                </span>
                <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                  {typeLabels[finding.type] || finding.type}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-medium text-[#111827] truncate">{finding.name}</p>
                  {finding.affected_files.length > 0 && (
                    <p className="text-[8px] text-[#6B7280] truncate">
                      {finding.affected_files.slice(0, 2).join(", ")}
                      {finding.affected_files.length > 2 && ` +${finding.affected_files.length - 2} more`}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center py-8 text-xs text-[#9CA3AF]">
            <ShieldCheck className="mb-2 h-6 w-6" />
            {searchQuery || severityFilter !== "all" || typeFilter !== "all"
              ? "No findings match your search/filter criteria."
              : "No security findings detected — project is in good security posture."}
          </div>
        )}

        {/* Detail Panel */}
        {selectedFinding && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-3 rounded-lg border border-[#1E40AF] bg-[#EFF6FF] p-4"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[8px] font-semibold uppercase ${severityBadge[selectedFinding.severity] || severityBadge.low}`}>
                    {selectedFinding.severity}
                  </span>
                  <span className="rounded bg-[#F3F4F6] px-1.5 py-0.5 text-[8px] font-medium text-[#6B7280]">
                    {typeLabels[selectedFinding.type] || selectedFinding.type}
                  </span>
                </div>
                <p className="mt-1 text-xs font-semibold text-[#111827]">{selectedFinding.name}</p>
              </div>
              <button onClick={() => setSelectedFinding(null)} className="rounded p-1 text-[#6B7280] hover:text-[#DC2626] hover:bg-[#FEF2F2]">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="space-y-2 text-[10px] text-[#374151]">
              {selectedFinding.detail && <p className="leading-relaxed">{selectedFinding.detail}</p>}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                <div className="rounded-lg bg-white/60 p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Business Impact</p>
                  <p className="text-[10px] leading-relaxed">{selectedFinding.business_impact}</p>
                </div>
                <div className="rounded-lg bg-white/60 p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">Technical Impact</p>
                  <p className="text-[10px] leading-relaxed">{selectedFinding.technical_impact}</p>
                </div>
              </div>

              {selectedFinding.affected_files.length > 0 && (
                <div>
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                    Affected Files ({selectedFinding.affected_files.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedFinding.affected_files.map((f) => (
                      <span key={f} className="rounded bg-white/60 px-2 py-1 text-[9px] font-mono text-[#1E40AF]">{f}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedFinding.affected_functions.length > 0 && (
                <div>
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#9CA3AF] mb-1">
                    Affected Functions ({selectedFinding.affected_functions.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedFinding.affected_functions.map((fn) => (
                      <span key={fn} className="rounded bg-white/60 px-2 py-1 text-[9px] font-mono text-[#6B7280]">{fn}</span>
                    ))}
                  </div>
                </div>
              )}

              {selectedFinding.recommended_fix && (
                <div className="rounded-lg bg-[#ECFDF5] border border-[#A7F3D0] p-2.5">
                  <p className="text-[8px] font-semibold uppercase tracking-wider text-[#059669] mb-0.5">Recommended Fix</p>
                  <p className="text-[10px] text-[#065F46]">{selectedFinding.recommended_fix}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>

      {projectId && (
        <RelatedAnalysisNav projectId={projectId} currentPage="security-intelligence" />
      )}
    </motion.div>
  );
}

export default SecurityIntelligence;
