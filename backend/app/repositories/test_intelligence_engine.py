import json
import os
import re
from pathlib import Path
from typing import Any


TEST_FILE_PATTERNS = [
    re.compile(r"^test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.test\.(js|ts|jsx|tsx)$"),
    re.compile(r".*\.spec\.(js|ts|jsx|tsx)$"),
    re.compile(r".*\.test\.(java|kt)$"),
    re.compile(r".*Test\.java$"),
    re.compile(r".*Tests\.(php|rb)$"),
    re.compile(r".*_spec\.(rb|ex)$"),
    re.compile(r".*_test\.(go|rs)$"),
    re.compile(r"^test_.*\.(js|ts)$"),
]

FUNC_DEF_RE = re.compile(
    r"(?:def|async def|function|it\(|describe\(|test\s+|Test\s+)\s*(\w+)?\s*(?:\(|=>)",
)
CLASS_DEF_RE = re.compile(r"(?:class|interface)\s+(\w+)")
ASSERT_PATTERNS = [
    re.compile(r"\bassert\b"),
    re.compile(r"\bexpect\b"),
    re.compile(r"\bshould\b"),
    re.compile(r"\beq\b"),
    re.compile(r"\bassertEqual\b"),
    re.compile(r"\bassertTrue\b"),
    re.compile(r"\bassertFalse\b"),
    re.compile(r"\bassertRaises\b"),
    re.compile(r"\bassertIn\b"),
    re.compile(r"\bassertIs\b"),
    re.compile(r"\bassertIsNone\b"),
    re.compile(r"\bassertGreater\b"),
    re.compile(r"\bassertLess\b"),
    re.compile(r"\btoEq\b"),
    re.compile(r"\btoBe\b"),
    re.compile(r"\btoMatch\b"),
    re.compile(r"\btoThrow\b"),
    re.compile(r"\btoContain\b"),
    re.compile(r"\.should\."),
    re.compile(r"\bverify\b"),
]

FIXTURE_PATTERNS = [
    re.compile(r"@pytest\.fixture"),
    re.compile(r"@fixture"),
    re.compile(r"def setup"),
    re.compile(r"def setUp"),
    re.compile(r"def setUpClass"),
    re.compile(r"beforeEach"),
    re.compile(r"beforeAll"),
    re.compile(r"setup\(\)"),
    re.compile(r"before\(\)"),
    re.compile(r"@Before"),
    re.compile(r"@BeforeEach"),
    re.compile(r"@BeforeClass"),
]

MOCK_PATTERNS = [
    re.compile(r"mock\b"),
    re.compile(r"patch\b"),
    re.compile(r"Mock\(|Mock\("),
    re.compile(r"MagicMock"),
    re.compile(r"@patch|@mock"),
    re.compile(r"spy\b|Spy\("),
    re.compile(r"stub\b"),
    re.compile(r"jest\.fn|jest\.spy|vi\.fn|vi\.spy"),
    re.compile(r"\bcreateMock\b"),
]

FRAMEWORK_INDICATORS: dict[str, dict[str, Any]] = {
    "pytest": {"type": "python", "re": re.compile(r"pytest"), "conf": ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]},
    "unittest": {"type": "python", "re": re.compile(r"unittest|TestCase"), "conf": []},
    "nose": {"type": "python", "re": re.compile(r"nosetests|nose\.|from nose"), "conf": ["setup.cfg", ".noserc"]},
    "Jest": {"type": "javascript", "re": re.compile(r"jest"), "conf": ["jest.config.js", "jest.config.ts", "jest.config.json"]},
    "Mocha": {"type": "javascript", "re": re.compile(r"mocha"), "conf": [".mocharc.js", ".mocharc.json", ".mocharc.yml"]},
    "Vitest": {"type": "javascript", "re": re.compile(r"vitest"), "conf": ["vitest.config.js", "vitest.config.ts"]},
    "JUnit": {"type": "java", "re": re.compile(r"junit|@Test|@org\.junit"), "conf": []},
    "Cypress": {"type": "e2e", "re": re.compile(r"cypress"), "conf": ["cypress.json", "cypress.config.js"]},
    "Playwright": {"type": "e2e", "re": re.compile(r"playwright"), "conf": ["playwright.config.js", "playwright.config.ts"]},
    "Selenium": {"type": "e2e", "re": re.compile(r"selenium"), "conf": []},
    "Robot Framework": {"type": "e2e", "re": re.compile(r"robotframework|robot\b"), "conf": ["robot.yaml", "robot.conf"]},
}


class TestIntelligenceEngine:

    def analyze(self, workspace_path: Path | None = None,
                project_analysis: dict | None = None,
                code_intel: dict | None = None,
                code_quality: dict | None = None,
                file_analysis: dict | None = None,
                func_class: dict | None = None,
                dep_analysis: dict | None = None,
                call_graph: dict | None = None,
                semantic: dict | None = None,
                config_intel: dict | None = None,
                recommendations: dict | None = None) -> dict:
        all_files = self._collect_all_files(workspace_path)
        source_files = self._collect_source_files(workspace_path, code_intel)
        test_files = self._identify_test_files(all_files)
        frameworks = self._detect_frameworks(workspace_path, all_files, source_files)
        test_file_details = self._analyze_test_files(test_files)
        untested = self._find_untested_components(workspace_path, source_files, test_files, func_class, semantic)
        missing = self._identify_missing_test_cases(untested, semantic)
        quality = self._evaluate_test_quality(test_file_details, frameworks)
        score = self._compute_score(test_file_details, untested, quality, source_files, test_files)
        recommendations_list = self._generate_recommendations(untested, missing, frameworks, score)
        summary = self._generate_summary(test_file_details, frameworks, untested, missing, score, recommendations_list)
        return {
            "test_score": score,
            "detected_frameworks": frameworks,
            "test_files": test_file_details,
            "untested_components": untested,
            "missing_test_cases": missing,
            "quality_metrics": quality,
            "recommendations": recommendations_list,
            "summary": summary,
        }

    def _collect_all_files(self, workspace_path) -> list[dict]:
        if not workspace_path:
            return []
        result = []
        for root, dirs, filenames in os.walk(str(workspace_path)):
            for fn in filenames:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, str(workspace_path))
                try:
                    st = os.stat(full)
                    size = st.st_size
                except Exception:
                    size = 0
                result.append({
                    "path": rel,
                    "name": fn,
                    "full": full,
                })
        return result

    def _collect_source_files(self, workspace_path, code_intel) -> list[dict]:
        files = []
        if code_intel and isinstance(code_intel, dict):
            raw = code_intel.get("files", code_intel.get("raw_files", []))
            if isinstance(raw, list):
                for f in raw:
                    path = f.get("path", f.get("file", ""))
                    content = f.get("content", f.get("source", ""))
                    if path and content:
                        files.append({"path": path, "content": content, "size": len(content)})
        if workspace_path and not files:
            exts = (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php", ".rs", ".kt")
            for root, _, filenames in os.walk(str(workspace_path)):
                for fn in filenames:
                    if fn.endswith(exts):
                        fpath = os.path.join(root, fn)
                        rel = os.path.relpath(fpath, str(workspace_path))
                        try:
                            with open(fpath, "r", errors="ignore") as fh:
                                content = fh.read()
                            files.append({"path": rel, "content": content, "size": len(content)})
                        except Exception:
                            pass
        return files

    def _identify_test_files(self, all_files) -> list[dict]:
        test_files = []
        test_dir_patterns = [re.compile(r"(^|[/\\])(test|tests|spec|specs|__tests__)[/\\]", re.I)]
        for f in all_files:
            name = f["name"]
            rel = f["path"]
            is_test = False
            is_test = any(p.match(name) for p in TEST_FILE_PATTERNS)
            if not is_test:
                is_test = any(p.search(rel) for p in test_dir_patterns)
            if not is_test:
                ext = os.path.splitext(name)[1].lower()
                stem = os.path.splitext(name)[0].lower()
                if ext == ".py" and ("test" in stem or stem.startswith("conftest")):
                    is_test = True
                elif ext in (".js", ".ts", ".jsx", ".tsx") and "test" in stem.lower():
                    is_test = True
            if is_test:
                test_files.append(f)
        return test_files

    def _detect_frameworks(self, workspace_path, all_files, source_files) -> list[dict]:
        frameworks_map: dict[str, dict] = {}
        combined_text = ""

        config_files = {f["name"].lower(): f for f in all_files}

        for fn in ["package.json", "pyproject.toml", "setup.cfg", "requirements.txt", "Pipfile",
                     "build.gradle", "pom.xml", "go.mod", "Cargo.toml", "Gemfile"]:
            for f in all_files:
                if f["name"].lower() == fn.lower():
                    try:
                        with open(f["full"], "r", errors="ignore") as fh:
                            combined_text += fh.read() + "\n"
                    except Exception:
                        pass

        for sf in source_files:
            combined_text += sf.get("content", "") + "\n"

        for fw_name, info in FRAMEWORK_INDICATORS.items():
            if info["re"].search(combined_text):
                frameworks_map[fw_name] = {
                    "name": fw_name,
                    "type": info["type"],
                    "version": "",
                    "config_file": "",
                    "reliability": "high",
                }

        for fw_name, info in FRAMEWORK_INDICATORS.items():
            for conf_name in info["conf"]:
                for f in all_files:
                    if f["name"].lower() == conf_name.lower():
                        if fw_name not in frameworks_map:
                            frameworks_map[fw_name] = {
                                "name": fw_name,
                                "type": info["type"],
                                "version": "",
                                "config_file": f["path"],
                                "reliability": "high",
                            }
                        else:
                            frameworks_map[fw_name]["config_file"] = f["path"]

        if "pytest" in frameworks_map:
            for f in all_files:
                if f["name"] == "conftest.py":
                    frameworks_map["pytest"]["reliability"] = "high"

        if workspace_path:
            pkg_path = os.path.join(str(workspace_path), "package.json")
            if os.path.isfile(pkg_path):
                try:
                    with open(pkg_path, "r", errors="ignore") as fh:
                        pkg = json.load(fh)
                    all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    for dep, ver in all_deps.items():
                        dep_l = dep.lower()
                        for fw_name, info in FRAMEWORK_INDICATORS.items():
                            if info["re"].search(dep_l):
                                if fw_name not in frameworks_map:
                                    frameworks_map[fw_name] = {
                                        "name": fw_name,
                                        "type": info["type"],
                                        "version": ver.strip("^~>=<"),
                                        "config_file": "package.json",
                                        "reliability": "high",
                                    }
                except Exception:
                    pass

        return list(frameworks_map.values())

    def _classify_test_type(self, content: str, name: str, path: str) -> list[str]:
        types = set()
        cl = content.lower()
        nl = name.lower()

        if re.search(r"\b(integration|integrate)\b", cl) or "integration" in path.lower():
            types.add("integration")
        if re.search(r"\b(e2e|end.to.end|endtoend)\b", cl) or "e2e" in path.lower():
            types.add("e2e")
        if re.search(r"\b(performance|benchmark|load|stress)\b", cl) or any(
                p in path.lower() for p in ["perf", "benchmark", "load"]):
            types.add("performance")
        if re.search(r"\b(security|vulnerability|penetration|auth)\b", cl) or "security" in path.lower():
            types.add("security")
        if re.search(r"\b(regression)\b", cl) or "regression" in path.lower():
            types.add("regression")
        if re.search(r"\b(smoke|sanity)\b", cl) or "smoke" in path.lower():
            types.add("smoke")
        if re.search(r"\b(api|rest|graphql|endpoint|route)\b", cl) or any(
                p in path.lower() for p in ["api", "routes", "endpoint"]):
            types.add("api")
        if re.search(r"\b(mock|stub|spy|fake)\b", cl):
            types.add("mock")
        if re.search(r"\bfixture\b", cl):
            types.add("fixture")

        if not types:
            if re.search(r"\b(test|spec|should|it\(|describe)\b", cl):
                types.add("unit")

        return list(types) if types else ["unit"]

    def _analyze_test_files(self, test_files) -> list[dict]:
        details = []
        for f in test_files:
            try:
                with open(f["full"], "r", errors="ignore") as fh:
                    content = fh.read()
            except Exception:
                content = ""

            lines = content.splitlines()
            loc = len(lines)
            funcs = FUNC_DEF_RE.findall(content)
            funcs = [fn for fn in funcs if fn and fn not in ("it", "describe", "test", "Test")]
            classes = CLASS_DEF_RE.findall(content)
            assertion_count = sum(len(p.findall(content)) for p in ASSERT_PATTERNS)
            fixture_count = sum(len(p.findall(content)) for p in FIXTURE_PATTERNS)
            mock_count = sum(len(p.findall(content)) for p in MOCK_PATTERNS)
            test_types = self._classify_test_type(content, f["name"], f["path"])

            naming_quality = self._assess_naming_quality(funcs)
            org_quality = self._assess_organization_quality(content, funcs, classes)
            maintainability = self._assess_test_maintainability(content, loc, assertion_count)

            details.append({
                "path": f["path"],
                "file_name": f["name"],
                "framework": self._detect_file_framework(content, f["name"]),
                "test_count": len(funcs),
                "assertion_count": assertion_count,
                "fixture_count": fixture_count,
                "mock_count": mock_count,
                "test_types": test_types,
                "naming_quality": naming_quality,
                "organization_quality": org_quality,
                "maintainability": maintainability,
                "coverage_estimate": min(assertion_count * 5, 85) if funcs else 0,
                "has_failures": bool(re.search(r"(FAIL|FAILED|fail|error|×|✗)", content)),
                "lines_of_code": loc,
            })
        return details

    def _detect_file_framework(self, content: str, name: str) -> str:
        if re.search(r"import pytest|from pytest|@pytest\.", content):
            return "pytest"
        if re.search(r"import unittest|from unittest|import TestCase|class.*TestCase", content):
            return "unittest"
        if re.search(r"jest\.|describe\(|it\(|expect\(", content):
            return "Jest"
        if re.search(r"describe\(|it\(|mocha", content):
            return "Mocha"
        if re.search(r"vitest|vi\.", content):
            return "Vitest"
        if re.search(r"@Test|org\.junit|import org\.junit", content):
            return "JUnit"
        if re.search(r"cy\b|cy\.", content):
            return "Cypress"
        if re.search(r"playwright|page\.|browser\.", content):
            return "Playwright"
        if re.search(r"import.*selenium|WebDriver", content):
            return "Selenium"
        if re.search(r"robotframework|Library.*Robot", content):
            return "Robot Framework"
        if re.search(r"describe\(|it\(|test\(", content):
            return "Mocha"
        return "unknown"

    def _assess_naming_quality(self, funcs: list[str]) -> str:
        if not funcs:
            return "unknown"
        descriptive = sum(1 for fn in funcs if len(fn) > 15 and "_" in fn)
        ratio = descriptive / max(len(funcs), 1)
        if ratio > 0.6:
            return "good"
        elif ratio > 0.3:
            return "average"
        return "poor"

    def _assess_organization_quality(self, content, funcs, classes) -> str:
        has_classes = len(classes) > 0
        has_describe = bool(re.search(r"\bdescribe\(", content))
        has_sections = bool(re.search(r"class\s+\w+.*:", content))
        has_comments = bool(re.search(r"^\s*(#|//|/\*)", content, re.MULTILINE))

        score = 0
        if has_classes or has_describe:
            score += 2
        if has_sections:
            score += 1
        if has_comments:
            score += 1
        if len(funcs) < 20:
            score += 1

        if score >= 4:
            return "good"
        elif score >= 2:
            return "average"
        return "poor"

    def _assess_test_maintainability(self, content, loc, assertions) -> str:
        duplicate_lines = self._estimate_duplication(content)
        if loc > 500:
            return "poor"
        if duplicate_lines > 0.2:
            return "poor"
        if assertions == 0 and loc > 50:
            return "poor"
        if loc > 200:
            return "average"
        return "good"

    def _estimate_duplication(self, content: str) -> float:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        if len(lines) < 5:
            return 0.0
        seen = set()
        dups = 0
        for l in lines:
            if l in seen:
                dups += 1
            seen.add(l)
        return dups / max(len(lines), 1)

    def _find_untested_components(self, workspace_path, source_files, test_files, func_class, semantic=None) -> list[dict]:
        untested = []
        test_paths_lower = {f["path"].lower() for f in test_files}

        test_imports: set[str] = set()
        for tf in test_files:
            try:
                with open(tf["full"], "r", errors="ignore") as fh:
                    content = fh.read()
                for m in re.finditer(r"(?:import|from)\s+(\S+)", content):
                    mod = m.group(1).split(".")[0].split(";")[0].strip()
                    mod = mod.strip("'\"")
                    if mod:
                        test_imports.add(mod.lower())
            except Exception:
                pass

        if semantic and isinstance(semantic, dict):
            components = semantic.get("components", semantic.get("detected_components", []))
            if isinstance(components, list):
                for comp in components:
                    cname = comp.get("name", "")
                    cpath = comp.get("path", comp.get("file", ""))
                    risk = "medium"
                    reason = "No corresponding test module found"
                    sug = "unit"
                    pri = 3
                    if cname.lower().replace(" ", "_") in test_imports:
                        continue
                    for t in test_paths_lower:
                        if cname.lower().replace(" ", "_") in t or cname.lower()[:8] in t:
                            break
                    else:
                        if "auth" in cname.lower():
                            risk = "high"
                            sug = "integration"
                            pri = 1
                        elif "payment" in cname.lower() or "billing" in cname.lower():
                            risk = "critical"
                            sug = "integration"
                            pri = 1
                        elif "api" in cname.lower() or "route" in cname.lower():
                            risk = "high"
                            sug = "api"
                            pri = 2
                        elif "model" in cname.lower() or "schema" in cname.lower():
                            risk = "medium"
                            sug = "unit"
                            pri = 3
                        elif "config" in cname.lower():
                            risk = "low"
                            sug = "unit"
                            pri = 5
                        elif "util" in cname.lower() or "helper" in cname.lower():
                            risk = "low"
                            sug = "unit"
                            pri = 4
                        untested.append({
                            "name": cname,
                            "type": "module",
                            "path": cpath,
                            "risk": risk,
                            "reason": reason,
                            "suggested_test_type": sug,
                            "priority": pri,
                        })

        if func_class:
            functions = func_class.get("functions", [])
            if isinstance(functions, list):
                for fn in functions:
                    fname = fn.get("name", "")
                    ffile = fn.get("file", "")
                    frel = os.path.relpath(ffile, str(workspace_path)) if workspace_path and ffile else ffile
                    if not frel or not fname:
                        continue
                    is_tested = False
                    for tf_path in test_paths_lower:
                        frel_lower = frel.lower()
                        if fname.lower().replace(" ", "_") in tf_path or fname.lower()[:6] in tf_path:
                            is_tested = True
                            break
                        base = os.path.splitext(os.path.basename(frel_lower))[0]
                        if base in tf_path:
                            is_tested = True
                            break
                    if not is_tested:
                        untested.append({
                            "name": fname,
                            "type": "function",
                            "path": frel,
                            "risk": "medium" if fname.startswith("test") else "high",
                            "reason": "No test found covering this function",
                            "suggested_test_type": "unit",
                            "priority": 2,
                        })

        return untested

    def _identify_missing_test_cases(self, untested, semantic) -> list[dict]:
        missing = []
        high_risk = [u for u in untested if u.get("priority", 5) <= 2]
        for u in high_risk[:20]:
            missing.append({
                "name": f"Test for {u['name']}",
                "module": u.get("path", ""),
                "type": u.get("suggested_test_type", "unit"),
                "severity": u.get("risk", "medium"),
                "affected_file": u.get("path", ""),
                "suggestion": f"Write {u.get('suggested_test_type', 'unit')} tests for {u['name']} "
                             f"covering core logic and edge cases.",
                "estimated_impact": f"+5-20% coverage improvement",
            })
        return missing

    def _evaluate_test_quality(self, test_files, frameworks) -> dict:
        if not test_files:
            return {
                "naming_quality": 0.0,
                "assertion_density": 0.0,
                "coverage_depth": 0.0,
                "organization_score": 0.0,
                "maintainability_score": 0.0,
                "reliability_score": 0.0,
            }

        naming_map = {"good": 90, "average": 60, "poor": 30, "unknown": 0}
        org_map = {"good": 90, "average": 60, "poor": 30, "unknown": 0}
        maint_map = {"good": 90, "average": 60, "poor": 30, "unknown": 0}

        total_naming = sum(naming_map.get(f.get("naming_quality", "unknown"), 0) for f in test_files)
        total_org = sum(org_map.get(f.get("organization_quality", "unknown"), 0) for f in test_files)
        total_maint = sum(maint_map.get(f.get("maintainability", "unknown"), 0) for f in test_files)
        n = max(len(test_files), 1)
        naming_score = total_naming / n
        org_score = total_org / n
        maint_score = total_maint / n

        total_loc = sum(f.get("lines_of_code", 1) for f in test_files)
        total_assertions = sum(f.get("assertion_count", 0) for f in test_files)
        assertion_density = (total_assertions / max(total_loc, 1)) * 100

        coverage_depth = min(
            sum(f.get("coverage_estimate", 0) for f in test_files) / n,
            100,
        )
        reliability = org_score * 0.4 + maint_score * 0.3 + naming_score * 0.3

        return {
            "naming_quality": round(naming_score, 1),
            "assertion_density": round(assertion_density, 2),
            "coverage_depth": round(coverage_depth, 1),
            "organization_score": round(org_score, 1),
            "maintainability_score": round(maint_score, 1),
            "reliability_score": round(reliability, 1),
        }

    def _compute_score(self, test_files, untested, quality, source_files, test_file_list) -> dict:
        total_source = max(len(source_files), 1)
        total_test = len(test_files)
        test_ratio = min(total_test / total_source * 100, 100)

        untested_count = len([u for u in untested if u.get("type") != "function"])
        untested_ratio = max(0, 100 - (untested_count / max(total_source, 1)) * 100)

        cover = quality.get("coverage_depth", 0)
        naming = quality.get("naming_quality", 0)
        org = quality.get("organization_score", 0)
        maint = quality.get("maintainability_score", 0)
        reliability = quality.get("reliability_score", 0)
        assertion_density = quality.get("assertion_density", 0)

        overall = round(
            test_ratio * 0.2 +
            untested_ratio * 0.15 +
            cover * 0.15 +
            naming * 0.1 +
            org * 0.1 +
            maint * 0.1 +
            reliability * 0.1 +
            min(assertion_density * 2, 10),
            1,
        )

        health = round(
            naming * 0.2 +
            org * 0.2 +
            maint * 0.2 +
            reliability * 0.2 +
            cover * 0.2,
            1,
        )

        regression = round(
            (min(len(test_files) * 5, 100) * 0.3 +
             reliability * 0.3 +
             cover * 0.2 +
             naming * 0.2),
            1,
        )

        confidence = round(min(
            naming * 0.25 + org * 0.25 + reliability * 0.25 + assertion_density * 5 + 10,
            99,
        ), 1)

        if overall < 30:
            level = "critical"
        elif overall < 50:
            level = "high"
        elif overall < 70:
            level = "medium"
        elif overall < 85:
            level = "low"
        else:
            level = "informational"

        return {
            "overall_test_score": overall,
            "test_coverage": round(test_ratio, 1),
            "testing_health": health,
            "regression_readiness": regression,
            "ai_confidence": confidence,
            "risk_level": level,
        }

    def _generate_recommendations(self, untested, missing, frameworks, score) -> list[dict]:
        recs = []
        seen_categories: set[str] = set()

        high_untested = [u for u in untested if u.get("priority", 5) <= 2]
        if high_untested:
            modules_list = list({u.get("name", "") for u in high_untested[:8]})
            cat = "critical-untested"
            if cat not in seen_categories:
                seen_categories.add(cat)
                recs.append({
                    "priority": 1,
                    "category": "critical-untested",
                    "title": f"Critical Untested Components ({len(high_untested)})",
                    "description": f"High-risk components lack test coverage: {', '.join(modules_list[:5])}.",
                    "suggested_framework": "",
                    "estimated_coverage_improvement": min(len(high_untested) * 5, 40),
                    "affected_modules": modules_list,
                })

        if not frameworks:
            recs.append({
                "priority": 2,
                "category": "missing-framework",
                "title": "No Testing Framework Detected",
                "description": "Add a testing framework (pytest, Jest, etc.) to enable test automation.",
                "suggested_framework": "pytest",
                "estimated_coverage_improvement": 30.0,
                "affected_modules": [],
            })
        else:
            if not any(fw["type"] == "e2e" for fw in frameworks):
                recs.append({
                    "priority": 3,
                    "category": "missing-e2e",
                    "title": "No End-to-End Framework Detected",
                    "description": "Consider adding an e2e framework (Cypress, Playwright) for full-stack testing.",
                    "suggested_framework": "Cypress",
                    "estimated_coverage_improvement": 15.0,
                    "affected_modules": [],
                })

        if score.get("regression_readiness", 0) < 50:
            recs.append({
                "priority": 4,
                "category": "low-regression",
                "title": "Low Regression Readiness",
                "description": "Improve regression test coverage to catch unintended changes early.",
                "suggested_framework": "",
                "estimated_coverage_improvement": 20.0,
                "affected_modules": [],
            })

        if score.get("testing_health", 0) < 50:
            recs.append({
                "priority": 5,
                "category": "testing-health",
                "title": "Testing Health Needs Improvement",
                "description": "Focus on test organization, naming conventions, and assertion quality.",
                "suggested_framework": "",
                "estimated_coverage_improvement": 10.0,
                "affected_modules": [],
            })

        return recs

    def _generate_summary(self, test_files, frameworks, untested, missing, score, recommendations) -> dict:
        lines = []
        fw_names = [fw["name"] for fw in frameworks]
        total_tests = sum(f.get("test_count", 0) for f in test_files)
        total_assertions = sum(f.get("assertion_count", 0) for f in test_files)
        total_fixtures = sum(f.get("fixture_count", 0) for f in test_files)
        total_mocks = sum(f.get("mock_count", 0) for f in test_files)
        untested_files = len([u for u in untested if u.get("type") == "file"])
        untested_funcs = len([u for u in untested if u.get("type") == "function"])
        untested_modules = len([u for u in untested if u.get("type") == "module"])

        if fw_names:
            lines.append(f"Detected frameworks: {', '.join(fw_names)}.")
        if total_tests > 0:
            lines.append(f"Found {total_tests} test functions across {len(test_files)} files.")
        if total_assertions > 0:
            lines.append(f"Total {total_assertions} assertions, {total_fixtures} fixtures, {total_mocks} mocks.")
        if untested_modules > 0:
            lines.append(f"{untested_modules} modules lack test coverage.")
        if score.get("overall_test_score", 0) < 40:
            lines.append("Test coverage is critically low — prioritize adding tests for core modules.")
        elif score.get("overall_test_score", 0) < 70:
            lines.append("Test coverage is moderate — focus on filling gaps in high-risk areas.")
        else:
            lines.append("Test coverage is healthy — maintain and expand for new features.")

        prioritized = []
        for r in sorted(recommendations, key=lambda x: x.get("priority", 99)):
            prioritized.append(f"[P{r['priority']}] {r['title']}: {r.get('description', '')[:120]}")

        return {
            "total_test_files": len(test_files),
            "total_test_functions": total_tests,
            "total_test_classes": len([u for u in untested if u.get("type") == "class"]),
            "total_assertions": total_assertions,
            "total_fixtures": total_fixtures,
            "total_mocks": total_mocks,
            "untested_files": untested_files,
            "untested_functions": untested_funcs,
            "untested_classes": len([u for u in untested if u.get("type") == "class"]),
            "coverage_percentage": score.get("test_coverage", 0),
            "detected_frameworks": fw_names,
            "summary_text": " ".join(lines),
            "prioritized_recommendations": prioritized[:20],
        }
