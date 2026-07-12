import type { ArchitectureIssueInfo } from "@/types/project-analyzer";

const BUSINESS_IMPACT_MAP: Record<string, string> = {
  god_class: "Increases maintenance cost, reduces team velocity, and makes the system harder to extend with new features",
  god_function: "Reduces code readability, increases defect risk, and makes business logic changes error-prone",
  excessive_params: "Creates confusing APIs, increases chance of parameter misordering bugs, and reduces developer productivity",
  long_function: "Makes business logic hard to understand, test, and maintain over time",
  deep_inheritance: "Creates fragile class hierarchies where changes in base classes can break derived business logic",
  tight_coupling: "Makes the system rigid and hard to modify, increasing the cost of business requirement changes",
  complex_conditional: "Increases risk of logic errors in business rules, making edge cases hard to identify",
  logic_duplication: "Leads to inconsistent business behavior when one copy is updated but others are missed",
  mixed_concerns: "Violates separation of concerns, making the system harder to debug, test, and evolve",
  business_logic_layer: "Business logic mixed with infrastructure concerns reduces maintainability and testability",
  missing_validation: "Can lead to data corruption, security vulnerabilities, and unexpected runtime failures",
  improper_global: "Introduces hidden state dependencies that make reasoning about program behavior difficult",
  exception_antipattern: "Can mask critical errors, making debugging difficult and potentially hiding production issues",
  dead_code: "Increases maintenance burden and confuses developers about which code paths are actually used",
  circular_dependency: "Creates initialization order problems and makes the dependency graph fragile",
};

const ARCHITECTURE_IMPACT_MAP: Record<string, string> = {
  god_class: "Violates Single Responsibility Principle; class handles too many responsibilities",
  god_function: "Violates function-level cohesion principles; function has too many responsibilities",
  excessive_params: "Indicates poor API design and lack of parameter object abstraction",
  long_function: "Exceeds recommended function length; makes code difficult to understand at a glance",
  deep_inheritance: "Excessive inheritance depth makes the type hierarchy hard to navigate",
  tight_coupling: "High module coupling reduces modularity and makes independent testing difficult",
  complex_conditional: "High cyclomatic complexity in conditionals makes test coverage difficult",
  logic_duplication: "Duplicated logic violates DRY principle and creates maintenance risk",
  mixed_concerns: "Layered architecture violation; different architectural layers are mixed together",
  business_logic_layer: "Architecture layer violation; business logic found outside appropriate layer",
  missing_validation: "Missing input validation creates architectural gaps in the defense-in-depth strategy",
  improper_global: "Global state usage violates encapsulation and creates implicit dependencies",
  exception_antipattern: "Improper exception handling breaks the architectural error handling strategy",
  dead_code: "Unreachable code indicates incomplete refactoring or leftover debugging artifacts",
  circular_dependency: "Circular dependencies violate acyclic dependency principles",
};

const ISSUE_TYPE_LABELS: Record<string, string> = {
  god_class: "God Class",
  god_function: "God Function",
  excessive_params: "Excessive Parameters",
  long_function: "Long Function",
  deep_inheritance: "Deep Inheritance",
  tight_coupling: "Tight Coupling",
  complex_conditional: "Complex Conditional",
  logic_duplication: "Duplicate Business Logic",
  mixed_concerns: "Mixed Concerns",
  business_logic_layer: "Business Logic Layer Violation",
  missing_validation: "Missing Validation",
  improper_global: "Improper Global State",
  exception_antipattern: "Improper Exception Flow",
  dead_code: "Unreachable Code",
  circular_dependency: "Circular Dependency",
};

export function getModuleFromPath(filePath: string): string {
  const parts = filePath.split("/");
  if (parts.length >= 2) {
    return parts.slice(0, -1).join("/") || "root";
  }
  return "root";
}

export function getBusinessImpact(category: string): string {
  return BUSINESS_IMPACT_MAP[category] || "Affects overall system maintainability and reliability";
}

export function getArchitectureImpact(category: string): string {
  return ARCHITECTURE_IMPACT_MAP[category] || "Violates software architecture best practices";
}

export function getIssueTypeLabel(category: string): string {
  return ISSUE_TYPE_LABELS[category] || category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function enhanceArchitectureBug(bug: ArchitectureIssueInfo): ArchitectureIssueInfo {
  return {
    ...bug,
    affected_module: bug.affected_module || getModuleFromPath(bug.affected_file),
    business_impact: bug.business_impact || getBusinessImpact(bug.architecture_category),
    architecture_impact: bug.architecture_impact || bug.impact_scope || getArchitectureImpact(bug.architecture_category),
  };
}

export function summarizeArchitectureFindings(bugs: ArchitectureIssueInfo[]): string[] {
  if (bugs.length === 0) return ["No architecture or logic issues detected."];

  const summaries: string[] = [];
  summaries.push(`Architecture analysis completed.`);

  const categories = bugs.map((b) => b.architecture_category);
  const layerViolations = categories.filter(
    (c) => ["tight_coupling", "mixed_concerns", "business_logic_layer", "improper_global"].includes(c),
  ).length;
  const logicErrors = categories.filter(
    (c) => ["logic_duplication", "complex_conditional", "missing_validation", "dead_code"].includes(c),
  ).length;
  const structureIssues = categories.filter(
    (c) => ["god_class", "god_function", "excessive_params", "long_function", "deep_inheritance"].includes(c),
  ).length;
  const flowIssues = categories.filter(
    (c) => ["exception_antipattern", "circular_dependency"].includes(c),
  ).length;

  if (layerViolations > 0) summaries.push(`${layerViolations} layer violation${layerViolations > 1 ? "s" : ""} detected.`);
  if (logicErrors > 0) summaries.push(`${logicErrors} business logic inconsistency${logicErrors > 1 ? "ies" : "y"} found.`);
  if (structureIssues > 0) summaries.push(`${structureIssues} code structure issue${structureIssues > 1 ? "s" : ""} identified.`);
  if (flowIssues > 0) summaries.push(`${flowIssues} ${flowIssues > 1 ? "flow" : ""} communication issue${flowIssues > 1 ? "s" : ""} identified.`);

  return summaries;
}

export function getArchitectureIssueTypes(bugs: ArchitectureIssueInfo[]): string[] {
  const types = new Set(bugs.map((b) => b.architecture_category));
  return Array.from(types).sort();
}

export function getArchitectureModules(bugs: ArchitectureIssueInfo[]): string[] {
  const modules = new Set(bugs.map((b) => getModuleFromPath(b.affected_file)));
  return Array.from(modules).sort();
}
