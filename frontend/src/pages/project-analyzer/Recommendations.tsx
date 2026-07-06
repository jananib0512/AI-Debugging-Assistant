import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, Shield, AlertTriangle, Award, CheckCircle, Lightbulb, Zap, RefreshCw
} from "lucide-react";
import { useAnalysis } from "@/contexts/AnalysisContext";

export function Recommendations() {
  const navigate = useNavigate();
  const analysis = useAnalysis();
  const { projectId } = useParams();
  const { projectInsights, loading, analyzing, error, refresh } = analysis;
  const [timedOut, setTimedOut] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (loading && !timerRef.current) {
      timerRef.current = setTimeout(() => {
        setTimedOut(true);
      }, 30000);
    }
    if (!loading && timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [loading]);

  // --- loading state (with timeout) ---
  if (loading && !timedOut) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#E5E7EB] border-t-[#2563EB]" />
        <p className="mt-4 text-sm font-medium text-[#6B7280]">Loading recommendations...</p>
      </div>
    );
  }

  // --- timed out ---
  if (timedOut) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Request timed out</p>
        <p className="mt-1 text-xs text-[#6B7280]">The analysis took too long to complete. Please try again.</p>
        <button onClick={() => { setTimedOut(false); refresh(true); }} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  // --- error state ---
  if (error && !projectInsights) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertTriangle className="mb-3 h-8 w-8 text-[#DC2626]" />
        <p className="text-sm font-medium text-[#111827]">Failed to load recommendations</p>
        <p className="mt-1 text-xs text-[#6B7280]">{error}</p>
        <button onClick={() => refresh(true)} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  // --- empty state (loaded but no insights) ---
  if (!loading && !projectInsights) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Lightbulb className="mb-3 h-8 w-8 text-[#9CA3AF]" />
        <p className="text-sm font-medium text-[#111827]">No recommendations available</p>
        <p className="mt-1 text-xs text-[#6B7280]">Run a project analysis first to generate recommendations.</p>
        <button onClick={() => refresh(true)} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-4 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB]">
          <RefreshCw className="h-3.5 w-3.5" /> Retry
        </button>
      </div>
    );
  }

  const insights = projectInsights!;
  const health = insights.health_score;
  const risks = insights.risk_analysis;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate(`/projects/${projectId}/analyzer`)} className="inline-flex items-center gap-1.5 text-xs font-medium text-[#6B7280] hover:text-[#111827]">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Overview
          </button>
          <p className="mt-2 text-[10px] font-semibold uppercase tracking-wider text-[#9CA3AF]">Project Analyzer</p>
          <h1 className="mt-0.5 text-xl font-bold text-[#111827]">AI Recommendations</h1>
        </div>
        <button
          onClick={() => refresh(true)}
          disabled={analyzing}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-xs font-medium text-[#374151] hover:bg-[#F9FAFB] disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? "animate-spin" : ""}`} />
          {analyzing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {health && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="text-sm font-semibold text-[#111827]">Project Health Score</p>
          <div className="mt-2 flex items-center gap-3">
            <span className="text-2xl font-bold text-[#111827]">{health.score}%</span>
            <div className="flex-1 h-3 w-full max-w-md rounded-full bg-[#F3F4F6] overflow-hidden">
              <div className={`h-full rounded-full ${
                health.score >= 70 ? "bg-[#059669]" : health.score >= 40 ? "bg-[#D97706]" : "bg-[#DC2626]"
              }`} style={{ width: `${health.score}%` }} />
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              health.classification === "good" || health.classification === "healthy"
                ? "bg-[#ECFDF5] text-[#065F46]"
                : health.classification === "fair" || health.classification === "average"
                ? "bg-[#FFFBEB] text-[#92400E]"
                : "bg-[#FEF2F2] text-[#991B1B]"
            }`}>{health.classification}</span>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2 mb-3">
            <Award className="h-4 w-4 text-[#2563EB]" />
            <p className="text-sm font-semibold text-[#111827]">Readiness Scores</p>
          </div>
          {insights.readiness_scores.length > 0 ? (
            <div className="space-y-2">
              {insights.readiness_scores.map((r, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-xs text-[#374151] capitalize">{r.category.replace(/_/g, " ")}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-24 rounded-full bg-[#F3F4F6] overflow-hidden">
                      <div className="h-full rounded-full bg-[#2563EB]" style={{ width: `${r.score}%` }} />
                    </div>
                    <span className="text-xs font-medium text-[#111827]">{r.score}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#6B7280]">No readiness data available.</p>
          )}
        </div>

        {risks && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-[#DC2626]" />
              <p className="text-sm font-semibold text-[#111827]">Risk Analysis</p>
            </div>
            <p className="text-xs text-[#6B7280]">Level: {risks.level}</p>
            <div className="mt-1 flex items-center gap-2">
              <span className="text-lg font-bold text-[#111827]">{risks.score}</span>
              <div className="h-2 w-24 rounded-full bg-[#F3F4F6] overflow-hidden">
                <div className="h-full rounded-full bg-[#DC2626]" style={{ width: `${risks.score}%` }} />
              </div>
            </div>
            <p className="mt-2 text-xs text-[#374151]">{risks.explanation}</p>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-2">
        {insights.strengths && insights.strengths.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <p className="mb-3 text-sm font-semibold text-[#059669]">Strengths</p>
            <div className="space-y-2">
              {insights.strengths.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#059669]" />
                  <span className="text-[#374151]"><strong>{s.category}:</strong> {s.detail}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {insights.weaknesses && insights.weaknesses.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <p className="mb-3 text-sm font-semibold text-[#DC2626]">Weaknesses</p>
            <div className="space-y-2">
              {insights.weaknesses.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#DC2626]" />
                  <span className="text-[#374151]"><strong>{w.category}:</strong> {w.detail}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {insights.performance_insights && insights.performance_insights.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="h-4 w-4 text-[#D97706]" />
              <p className="text-sm font-semibold text-[#111827]">Performance Insights</p>
            </div>
            <div className="space-y-1.5">
              {insights.performance_insights.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-[#374151] list-none">
                  <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-[#D97706]" />
                  {p.detail}
                </li>
              ))}
            </div>
          </div>
        )}

        {insights.security_insights && insights.security_insights.length > 0 && (
          <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="h-4 w-4 text-[#059669]" />
              <p className="text-sm font-semibold text-[#111827]">Security Insights</p>
            </div>
            <div className="space-y-1.5">
              {insights.security_insights.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#059669]" />
                  <span className="text-[#374151]">{s.detail}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    s.severity === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                    s.severity === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                    "bg-[#F3F4F6] text-[#374151]"
                  }`}>{s.severity}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {insights.recommended_actions && insights.recommended_actions.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="h-4 w-4 text-[#D97706]" />
            <p className="text-sm font-semibold text-[#111827]">Recommended Actions</p>
          </div>
          <div className="space-y-2">
            {insights.recommended_actions.map((ra, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-[#F9FAFB] px-4 py-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-[#2563EB]" />
                  <span className="text-sm text-[#374151]">{ra.action}</span>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                  ra.priority === "high" ? "bg-[#FEF2F2] text-[#991B1B]" :
                  ra.priority === "medium" ? "bg-[#FFFBEB] text-[#92400E]" :
                  "bg-[#F3F4F6] text-[#374151]"
                }`}>{ra.priority}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {insights.code_quality_insights && insights.code_quality_insights.length > 0 && (
        <div className="rounded-xl border border-[#E5E7EB] bg-white p-5">
          <p className="mb-3 text-sm font-semibold text-[#111827]">Code Quality Insights</p>
          <div className="space-y-1.5">
            {insights.code_quality_insights.map((cq, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-[#2563EB]" />
                <span className="text-[#374151]">{cq.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
