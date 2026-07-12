import type {
  PrioritizedIssueInfo,
  PrioritizationResponse,
  StaticCodeAnalysisResponse,
  SecurityAnalysisResponse,
  PerformanceAnalysisResponse,
} from "@/types/project-analyzer";

export interface BugSummaryStats {
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  files_affected: number;
  functions_affected: number;
  modules_affected: number;
}

export interface HealthScores {
  overall_bug_score: number;
  project_health: string;
  security_health: number;
  performance_health: number;
  maintainability_health: number;
  overall_readiness: string;
}

export interface TopIssue {
  bug_title: string;
  severity: string;
  affected_file: string;
  function_name: string;
  description: string;
  confidence: number;
  suggested_action: string;
  source_engine: string;
}

export interface CategoryDistribution {
  name: string;
  count: number;
  percentage: number;
}

export interface ExecutiveSummary {
  summary: string;
  detail: string;
}

export interface RepairEstimate {
  complexity: string;
  time: string;
}

export interface ChartData {
  label: string;
  value: number;
  color: string;
}

export function computeBugStats(
  issues: PrioritizedIssueInfo[],
): BugSummaryStats {
  const total_issues = issues.length;
  const critical_count = issues.filter((i) => i.severity === "Critical").length;
  const high_count = issues.filter((i) => i.severity === "High").length;
  const medium_count = issues.filter((i) => i.severity === "Medium").length;
  const low_count = issues.filter((i) => i.severity === "Low").length;
  const files = new Set(issues.map((i) => i.affected_file));
  const functions = new Set(
    issues.map((i) => i.function_name).filter(Boolean),
  );
  const modules = new Set(
    issues.map((i) => getModuleFromPath(i.affected_file)).filter(Boolean),
  );
  return {
    total_issues,
    critical_count,
    high_count,
    medium_count,
    low_count,
    files_affected: files.size,
    functions_affected: functions.size,
    modules_affected: modules.size,
  };
}

export function getModuleFromPath(filePath: string): string {
  const parts = filePath.replace(/\\/g, "/").split("/");
  return parts.length > 1 && parts[0] ? parts[0] : "root";
}

export function computeHealthScores(
  _issues: PrioritizedIssueInfo[] | undefined,
  stats: BugSummaryStats,
  securityData?: SecurityAnalysisResponse | null,
  performanceData?: PerformanceAnalysisResponse | null,
  staticData?: StaticCodeAnalysisResponse | null,
): HealthScores {
  const maxScore = 100;
  if (stats.total_issues === 0) {
    return {
      overall_bug_score: 100,
      project_health: "Excellent",
      security_health: 100,
      performance_health: 100,
      maintainability_health: 100,
      overall_readiness: "Ready",
    };
  }

  const severityWeights = { Critical: 10, High: 5, Medium: 2, Low: 1 };
  const weightedSum =
    stats.critical_count * severityWeights.Critical +
    stats.high_count * severityWeights.High +
    stats.medium_count * severityWeights.Medium +
    stats.low_count * severityWeights.Low;

  const densityFactor = Math.min(stats.files_affected / Math.max(stats.total_issues, 1), 1);
  const rawScore = Math.max(
    0,
    maxScore - (weightedSum / Math.max(stats.total_issues, 1)) * densityFactor * 8,
  );
  const overall_bug_score = Math.round(rawScore);

  let project_health: string;
  if (overall_bug_score >= 90) project_health = "Excellent";
  else if (overall_bug_score >= 70) project_health = "Good";
  else if (overall_bug_score >= 50) project_health = "Fair";
  else project_health = "Poor";

  const riskCount = stats.critical_count + stats.high_count;
  let overall_readiness: string;
  if (riskCount === 0 && overall_bug_score >= 80) overall_readiness = "Ready";
  else if (riskCount <= 3 && overall_bug_score >= 50) overall_readiness = "Conditional";
  else overall_readiness = "Not Ready";

  const security_health = securityData?.security_score ?? 100;
  const performance_health = performanceData
    ? Math.round(
        Math.max(
          0,
          100 - (performanceData.critical_count * 15 + performanceData.high_count * 8),
        ),
      )
    : 100;
  const maintainability_health = staticData
    ? Math.round(
        Math.max(
          0,
          100 - (staticData.critical_count * 8 + staticData.high_count * 4),
        ),
      )
    : 100;

  return {
    overall_bug_score,
    project_health,
    security_health,
    performance_health,
    maintainability_health,
    overall_readiness,
  };
}

export function getTopIssues(
  issues: PrioritizedIssueInfo[],
  count: number = 10,
): TopIssue[] {
  return issues.slice(0, count).map((i) => ({
    bug_title: i.bug_title,
    severity: i.severity,
    affected_file: i.affected_file,
    function_name: i.function_name,
    description: i.description,
    confidence: i.confidence,
    suggested_action: i.recommended_action || i.suggested_fix || "",
    source_engine: i.source_engine,
  }));
}

export function computeCategoryDistribution(
  issues: PrioritizedIssueInfo[],
): CategoryDistribution[] {
  const engineMap = new Map<string, number>();
  for (const i of issues) {
    const e = i.source_engine || "unknown";
    engineMap.set(e, (engineMap.get(e) || 0) + 1);
  }
  const total = issues.length || 1;
  const order = [
    "syntax",
    "static",
    "dependency",
    "runtime",
    "security",
    "performance",
    "architecture",
  ];
  const nameMap: Record<string, string> = {
    syntax: "Syntax",
    static: "Static Analysis",
    dependency: "Dependency",
    runtime: "Runtime",
    security: "Security",
    performance: "Performance",
    architecture: "Architecture & Logic",
  };
  return order
    .filter((k) => engineMap.has(k))
    .map((k) => ({
      name: nameMap[k] || k,
      count: engineMap.get(k) || 0,
      percentage: Math.round(((engineMap.get(k) || 0) / total) * 100),
    }));
}

export function computeAffectedModulesDistribution(
  issues: PrioritizedIssueInfo[],
): ChartData[] {
  const modMap = new Map<string, number>();
  for (const i of issues) {
    const mod = getModuleFromPath(i.affected_file);
    modMap.set(mod, (modMap.get(mod) || 0) + 1);
  }
  const sorted = [...modMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const colors = [
    "#2563EB", "#059669", "#DC2626", "#EA580C", "#7C3AED",
    "#0891B2", "#D97706", "#8B5CF6", "#EC4899", "#6B7280",
  ];
  return sorted.map(([label, value], i) => ({
    label,
    value,
    color: colors[i % colors.length] ?? "#6B7280",
  }));
}

export function computeAffectedFilesDistribution(
  issues: PrioritizedIssueInfo[],
): ChartData[] {
  const fileMap = new Map<string, number>();
  for (const i of issues) {
    fileMap.set(i.affected_file, (fileMap.get(i.affected_file) || 0) + 1);
  }
  const sorted = [...fileMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const colors = [
    "#2563EB", "#059669", "#DC2626", "#EA580C", "#7C3AED",
    "#0891B2", "#D97706", "#8B5CF6", "#EC4899", "#6B7280",
  ];
  return sorted.map(([label, value], i) => ({
    label,
    value,
    color: colors[i % colors.length] ?? "#6B7280",
  }));
}

export function generateExecutiveSummary(
  stats: BugSummaryStats,
  health: HealthScores,
  prioritization: PrioritizationResponse,
): ExecutiveSummary {
  const parts: string[] = [];
  const detailParts: string[] = [];

  parts.push(
    `The AI Software Engineer completed bug detection successfully.`,
  );

  if (stats.total_issues === 0) {
    parts.push(`No issues were detected. The project is in excellent shape.`);
    return {
      summary: parts.join(" "),
      detail:
        "All detection modules completed successfully with zero issues found across all categories.",
    };
  }

  parts.push(
    `${stats.total_issues} ${stats.total_issues === 1 ? "issue was" : "issues were"} detected.`,
  );

  const sevParts: string[] = [];
  if (stats.critical_count > 0)
    sevParts.push(`${stats.critical_count} Critical`);
  if (stats.high_count > 0) sevParts.push(`${stats.high_count} High`);
  if (stats.medium_count > 0) sevParts.push(`${stats.medium_count} Medium`);
  if (stats.low_count > 0) sevParts.push(`${stats.low_count} Low`);
  if (sevParts.length > 0) {
    parts.push(`${sevParts.join(", ")}.`);
    detailParts.push(
      `Severity breakdown: ${sevParts.join(", ")} across ${stats.files_affected} file(s) and ${stats.modules_affected} module(s).`,
    );
  }

  const topCritical = prioritization.prioritized_issues
    .filter((i) => i.severity === "Critical")
    .slice(0, 3);
  if (topCritical.length > 0) {
    const areas = [
      ...new Set(topCritical.map((i) => i.source_engine)),
    ];
    detailParts.push(
      `Critical issues found in: ${areas.join(", ")}. ` +
        `Immediate attention required for: ${topCritical.map((i) => i.bug_title).join(", ")}.`,
    );
  }

  const topCategories = computeCategoryDistribution(
    prioritization.prioritized_issues,
  );
  const worstCategory = topCategories
    .filter((c) => c.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, 2);
  if (worstCategory.length > 0) {
    detailParts.push(
      `Most issues found in: ${worstCategory.map((c) => `${c.name} (${c.count})`).join(", ")}.`,
    );
  }

  if (health.overall_readiness === "Ready") {
    detailParts.push(
      `The project is ready for Root Cause Analysis.`,
    );
  } else if (health.overall_readiness === "Conditional") {
    detailParts.push(
      `The project is conditionally ready for Root Cause Analysis after addressing critical and high priority issues.`,
    );
  } else {
    detailParts.push(
      `Resolve critical and high severity issues before proceeding to Root Cause Analysis.`,
    );
  }

  return {
    summary: parts.join(" "),
    detail: detailParts.join(" "),
  };
}

export function generateRecommendations(
  stats: BugSummaryStats,
  _health: HealthScores,
  prioritization: PrioritizationResponse,
): {
  immediate: string[];
  highPriority: string[];
  recommendedOrder: string[];
  estimatedComplexity: string;
  estimatedTime: string;
} {
  const immediate: string[] = [];
  const highPriority: string[] = [];
  const recommendedOrder: string[] = [];

  const critical = prioritization.prioritized_issues.filter(
    (i) => i.severity === "Critical",
  );
  const high = prioritization.prioritized_issues.filter(
    (i) => i.severity === "High",
  );

  if (critical.length > 0) {
    const files = [...new Set(critical.map((i) => i.affected_file))].slice(0, 5);
    immediate.push(
      `Fix ${critical.length} Critical issue(s) in ${files.length} file(s): ${files.slice(0, 3).join(", ")}${files.length > 3 ? "..." : ""}.`,
    );
    recommendedOrder.push("Fix all Critical severity issues first");
  }

  if (high.length > 0) {
    const files = [...new Set(high.map((i) => i.affected_file))].slice(0, 5);
    highPriority.push(
      `Resolve ${high.length} High severity issue(s) across ${files.length} file(s): ${files.slice(0, 3).join(", ")}${files.length > 3 ? "..." : ""}.`,
    );
    recommendedOrder.push("Address High severity issues next");
  }

  if (stats.medium_count > 0) {
    recommendedOrder.push("Review and fix Medium severity issues");
  }

  if (stats.low_count > 0) {
    recommendedOrder.push("Address Low severity issues as time permits");
  }

  recommendedOrder.push("Run Root Cause Analysis for deeper investigation");

  const totalWeight =
    stats.critical_count * 10 + stats.high_count * 5 + stats.medium_count * 2 + stats.low_count * 1;
  let complexity: string;
  if (totalWeight <= 10) complexity = "Low";
  else if (totalWeight <= 30) complexity = "Medium";
  else if (totalWeight <= 60) complexity = "High";
  else complexity = "Very High";

  const hoursPerWeight = 0.5;
  const estimatedHours = Math.round(totalWeight * hoursPerWeight);
  let time: string;
  if (estimatedHours <= 4) time = `${estimatedHours} hour(s)`;
  else if (estimatedHours <= 24) time = `${Math.round(estimatedHours / 8)} day(s)`;
  else time = `${Math.round(estimatedHours / 40)} week(s)`;

  return {
    immediate,
    highPriority,
    recommendedOrder,
    estimatedComplexity: complexity,
    estimatedTime: time,
  };
}

export function generateExportData(
  stats: BugSummaryStats,
  health: HealthScores,
  prioritization: PrioritizationResponse,
) {
  return {
    exported_at: new Date().toISOString(),
    project_name: prioritization.project_name,
    project_id: prioritization.project_id,
    summary: {
      total_issues: stats.total_issues,
      critical_count: stats.critical_count,
      high_count: stats.high_count,
      medium_count: stats.medium_count,
      low_count: stats.low_count,
      files_affected: stats.files_affected,
      functions_affected: stats.functions_affected,
      modules_affected: stats.modules_affected,
    },
    health: {
      overall_bug_score: health.overall_bug_score,
      project_health: health.project_health,
      security_health: health.security_health,
      performance_health: health.performance_health,
      maintainability_health: health.maintainability_health,
      overall_readiness: health.overall_readiness,
    },
    issues: prioritization.prioritized_issues.map((i) => ({
      bug_title: i.bug_title,
      severity: i.severity,
      affected_file: i.affected_file,
      function_name: i.function_name,
      description: i.description,
      confidence: i.confidence,
      source_engine: i.source_engine,
    suggested_action: i.recommended_action || i.suggested_fix || "",
    })),
    recommendations: prioritization.ai_recommendations,
  };
}

export function generateBugReportText(
  stats: BugSummaryStats,
  health: HealthScores,
  prioritization: PrioritizationResponse,
) {
  const lines: string[] = [];
  lines.push("=".repeat(60));
  lines.push("AI BUG DETECTION REPORT");
  lines.push("=".repeat(60));
  lines.push("");
  lines.push(`Project: ${prioritization.project_name}`);
  lines.push(`Reported: ${new Date().toLocaleString()}`);
  lines.push("");
  lines.push("--- BUG STATISTICS ---");
  lines.push(`Total Issues: ${stats.total_issues}`);
  lines.push(`  Critical: ${stats.critical_count}`);
  lines.push(`  High: ${stats.high_count}`);
  lines.push(`  Medium: ${stats.medium_count}`);
  lines.push(`  Low: ${stats.low_count}`);
  lines.push(`Files Affected: ${stats.files_affected}`);
  lines.push(`Functions Affected: ${stats.functions_affected}`);
  lines.push(`Modules Affected: ${stats.modules_affected}`);
  lines.push("");
  lines.push("--- HEALTH SCORES ---");
  lines.push(`Overall Bug Score: ${health.overall_bug_score}/100`);
  lines.push(`Project Health: ${health.project_health}`);
  lines.push(`Security Health: ${health.security_health}/100`);
  lines.push(`Performance Health: ${health.performance_health}/100`);
  lines.push(`Maintainability Health: ${health.maintainability_health}/100`);
  lines.push(`Overall Readiness: ${health.overall_readiness}`);
  lines.push("");
  lines.push("--- TOP ISSUES ---");
  const top = getTopIssues(prioritization.prioritized_issues, 10);
  top.forEach((issue, i) => {
    lines.push(`${i + 1}. [${issue.severity}] ${issue.bug_title}`);
    lines.push(`   File: ${issue.affected_file}`);
    if (issue.function_name) lines.push(`   Function: ${issue.function_name}`);
    lines.push(`   Confidence: ${issue.confidence}%`);
    if (issue.suggested_action) lines.push(`   Action: ${issue.suggested_action}`);
    lines.push("");
  });
  return lines.join("\n");
}
