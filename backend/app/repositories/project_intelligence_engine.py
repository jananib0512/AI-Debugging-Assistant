import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.detection.project_scanner import (
    EXTENSION_LANGUAGE_MAP,
    IGNORED_DIRS,
    IGNORED_FILES,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    ASSET_EXTENSIONS,
    SCRIPT_EXTENSIONS,
)

COMMENT_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "Python": [(r"#.*$", "single"), (r"'''(?:.|\n)*?'''", "multi"), (r'"""(?:.|\n)*?"""', "multi")],
    "JavaScript": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "TypeScript": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Java": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Go": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Rust": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi"), (r"///.*$", "single")],
    "C": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "C++": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "C#": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi"), (r"///.*$", "single")],
    "PHP": [(r"//.*$", "single"), (r"#.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Ruby": [(r"#.*$", "single"), (r"=begin[\s\S]*?=end", "multi")],
    "Swift": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Kotlin": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Shell": [(r"#.*$", "single")],
    "SQL": [(r"--.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "HTML": [(r"<!--[\s\S]*?-->", "multi")],
    "CSS": [(r"/\*[\s\S]*?\*/", "multi")],
    "SCSS": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "YAML": [(r"#.*$", "single")],
    "TOML": [(r"#.*$", "single")],
    "Dart": [(r"//.*$", "single"), (r"/\*[\s\S]*?\*/", "multi")],
    "Lua": [(r"--.*$", "single"), (r"--\[\[[\s\S]*?\]\]", "multi")],
    "Perl": [(r"#.*$", "single")],
    "R": [(r"#.*$", "single")],
}

FUNCTION_PATTERNS: dict[str, re.Pattern] = {
    "Python": re.compile(r"^\s*def\s+(\w+)\s*\("),
    "JavaScript": re.compile(r"(?:function\s+(\w+)\s*\(|(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*\([^)]*\)\s*\{)"),
    "TypeScript": re.compile(r"(?:function\s+(\w+)\s*\(|(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*\([^)]*\)\s*\{)"),
    "Java": re.compile(r"(?:public|private|protected|static|\s)\s+\w+\s+(\w+)\s*\("),
    "Go": re.compile(r"^\s*func\s+(\w+)\s*\("),
    "Rust": re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)\s*\("),
    "C": re.compile(r"^\s*(?:\w+\s+)+\*?(\w+)\s*\([^)]*\)\s*\{"),
    "C++": re.compile(r"^\s*(?:\w+\s+)+\*?(\w+)\s*\([^)]*\)\s*\{"),
    "C#": re.compile(r"(?:public|private|protected|internal|static|\s)\s+\w+\s+(\w+)\s*\("),
    "PHP": re.compile(r"^\s*(?:public|private|protected|static)?\s*function\s+(\w+)\s*\("),
    "Ruby": re.compile(r"^\s*def\s+(\w+)\s*(?:\(|$)"),
    "Swift": re.compile(r"^\s*(?:func\s+(\w+)\s*\()"),
    "Kotlin": re.compile(r"^\s*(?:fun\s+(\w+)\s*\()"),
    "Shell": re.compile(r"^\s*(\w+)\s*\(\)\s*\{"),
}

CLASS_PATTERNS: dict[str, re.Pattern] = {
    "Python": re.compile(r"^\s*class\s+(\w+)"),
    "JavaScript": re.compile(r"^\s*class\s+(\w+)"),
    "TypeScript": re.compile(r"^\s*class\s+(\w+)"),
    "Java": re.compile(r"^\s*(?:public|private|protected)?\s*(?:abstract|final)?\s*(?:class|interface|enum)\s+(\w+)"),
    "Go": re.compile(r"^\s*type\s+(\w+)\s+struct"),
    "Rust": re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)"),
    "C++": re.compile(r"^\s*(?:class|struct)\s+(\w+)"),
    "C#": re.compile(r"^\s*(?:public|private|protected|internal)?\s*(?:abstract|sealed|static)?\s*(?:class|struct|interface|enum)\s+(\w+)"),
    "PHP": re.compile(r"^\s*(?:abstract|final)?\s*class\s+(\w+)"),
    "Ruby": re.compile(r"^\s*class\s+(\w+)"),
    "Swift": re.compile(r"^\s*(?:class|struct|enum|protocol)\s+(\w+)"),
    "Kotlin": re.compile(r"^\s*(?:data\s+)?(?:class|interface|enum)\s+(\w+)"),
}

CYCLOMATIC_KEYWORDS: dict[str, list[str]] = {
    "Python": ["if ", "elif ", "for ", "while ", "and ", "or ", "except", "case ", "assert "],
    "JavaScript": ["if ", "else if", "for ", "while ", "case ", "catch ", "&&", r"\|\|", "? "],
    "TypeScript": ["if ", "else if", "for ", "while ", "case ", "catch ", "&&", r"\|\|", "? "],
    "Java": ["if ", "else if", "for ", "while ", "case ", "catch ", "&&", r"\|\|", "? "],
    "Go": ["if ", "for ", "case ", "&&", r"\|\|"],
    "Rust": ["if ", "else if", "for ", "while ", "match ", "&&", r"\|\|"],
    "C": ["if ", "else if", "for ", "while ", "case ", "&&", r"\|\|", "? "],
    "C++": ["if ", "else if", "for ", "while ", "case ", "catch ", "&&", r"\|\|", "? "],
    "C#": ["if ", "else if", "for ", "foreach ", "while ", "case ", "catch ", "&&", r"\|\|", "? "],
    "PHP": ["if ", "elseif", "for ", "foreach ", "while ", "case ", "catch ", "&&", r"\|\|"],
    "Ruby": ["if ", "elsif", "for ", "while ", "case ", "&&", r"\|\|"],
    "Shell": ["if ", "elif ", "for ", "while ", "case "],
    "SQL": ["IF ", "CASE ", "WHEN "],
}


def _count_comment_lines(content: str, language: str) -> int:
    patterns = COMMENT_PATTERNS.get(language, [])
    comment_lines: set[int] = set()
    lines = content.splitlines()
    for pattern_str, ctype in patterns:
        try:
            compiled = re.compile(pattern_str, re.MULTILINE)
            for match in compiled.finditer(content):
                start_line = content[:match.start()].count("\n")
                if ctype == "single":
                    comment_lines.add(start_line)
                else:
                    block = match.group(0)
                    block_lines = block.count("\n") + 1
                    for i in range(block_lines):
                        comment_lines.add(start_line + i)
        except re.error:
            pass
    return len(comment_lines)


def _count_blank_lines(content: str) -> int:
    return sum(1 for line in content.splitlines() if not line.strip())


def _detect_functions(content: str, language: str) -> list[str]:
    pattern = FUNCTION_PATTERNS.get(language)
    if not pattern:
        return []
    names = []
    for match in pattern.finditer(content):
        name = next((g for g in match.groups() if g), "")
        if name:
            names.append(name)
    return names


def _detect_classes(content: str, language: str) -> list[str]:
    pattern = CLASS_PATTERNS.get(language)
    if not pattern:
        return []
    names = []
    for match in pattern.finditer(content):
        name = next((g for g in match.groups() if g), "")
        if name:
            names.append(name)
    return names


def _calc_cyclomatic(content: str, language: str) -> int:
    keywords = CYCLOMATIC_KEYWORDS.get(language, [])
    count = 1
    for kw in keywords:
        try:
            count += len(re.findall(kw, content))
        except re.error:
            pass
    return count


def _compute_function_lengths(content: str, language: str) -> list[int]:
    func_pattern = FUNCTION_PATTERNS.get(language)
    if not func_pattern:
        return []
    lines = content.splitlines()
    func_starts = []
    for i, line in enumerate(lines):
        if func_pattern.search(line):
            func_starts.append(i)
    if not func_starts:
        return []
    lengths = []
    for idx, start in enumerate(func_starts):
        end = func_starts[idx + 1] if idx + 1 < len(func_starts) else len(lines)
        lengths.append(end - start)
    return lengths


def _compute_class_sizes(content: str, language: str) -> list[int]:
    class_pattern = CLASS_PATTERNS.get(language)
    if not class_pattern:
        return []
    lines = content.splitlines()
    class_starts = []
    for i, line in enumerate(lines):
        if class_pattern.search(line):
            class_starts.append(i)
    if not class_starts:
        return []
    sizes = []
    for idx, start in enumerate(class_starts):
        end = class_starts[idx + 1] if idx + 1 < len(class_starts) else len(lines)
        sizes.append(end - start)
    return sizes


def _naming_convention(name: str) -> str:
    if re.match(r'^[a-z]+(_[a-z]+)*$', name):
        return "snake_case"
    if re.match(r'^[a-z]+([A-Z][a-z]*)*$', name):
        return "camelCase"
    if re.match(r'^[A-Z][a-z]+([A-Z][a-z]*)*$', name):
        return "PascalCase"
    if re.match(r'^[A-Z]+(_[A-Z]+)*$', name):
        return "SCREAMING_SNAKE"
    if re.match(r'^[a-z]+(-[a-z]+)*$', name):
        return "kebab-case"
    return "other"


def _detect_mixed_naming(file_paths: list[str]) -> list[str]:
    conventions_seen: set[str] = set()
    for fp in file_paths:
        parts = fp.replace("\\", "/").split("/")
        for part in parts:
            base = os.path.splitext(part)[0]
            if base and not base.startswith("."):
                conventions_seen.add(_naming_convention(base))
    conventions_seen.discard("other")
    if len(conventions_seen) >= 3:
        return sorted(conventions_seen)
    return []


def _find_duplicate_filenames(file_paths: list[str]) -> list[str]:
    basename_map: dict[str, list[str]] = defaultdict(list)
    for fp in file_paths:
        base = os.path.basename(fp).lower()
        basename_map[base].append(fp)
    return [f"{base} ({len(paths)}x)" for base, paths in basename_map.items() if len(paths) > 1]


def _find_duplicate_modules(dir_names: list[str]) -> list[str]:
    name_counts = Counter(d.lower() for d in dir_names)
    return [f"{name} ({count}x)" for name, count in name_counts.items() if count > 1 and name not in {"src", "lib", "tests", "docs", "scripts"}]


def _find_empty_dirs(all_dirs: set[str], all_files: list[str]) -> list[str]:
    parent_dirs: set[str] = set()
    for fp in all_files:
        parts = fp.replace("\\", "/").split("/")
        for i in range(1, len(parts)):
            parent_dirs.add("/".join(parts[:i]))
    empty = [d for d in all_dirs if d not in parent_dirs]
    return sorted(empty)


def _detect_large_imports(content: str, language: str) -> int:
    if language == "Python":
        imports = re.findall(r"^\s*import\s+(\S+)", content, re.MULTILINE)
        from_imports = re.findall(r"^\s*from\s+\S+\s+import\s+(.+)", content, re.MULTILINE)
        total = len(imports)
        for fi in from_imports:
            total += len(fi.split(","))
        return total
    if language in ("JavaScript", "TypeScript"):
        imports = re.findall(r"(?:import\s+\{[^}]*\}\s*from|import\s+\w+\s*from)", content)
        return len(imports)
    return 0


class ProjectIntelligenceEngine:
    def analyze(self, workspace_path: Path) -> dict:
        if not workspace_path.exists():
            return self._empty_result()

        all_source_files: list[str] = []
        file_languages: dict[str, str] = {}
        file_contents: dict[str, str] = {}
        file_sizes: dict[str, int] = {}
        file_lines: dict[str, int] = {}
        file_blank: dict[str, int] = {}
        file_comments: dict[str, int] = {}
        file_functions: dict[str, list[str]] = {}
        file_classes: dict[str, list[str]] = {}
        file_complexity: dict[str, int] = {}
        file_func_lengths: dict[str, list[int]] = {}
        file_class_sizes: dict[str, list[int]] = {}
        language_loc: dict[str, int] = {}
        lang_file_counts: dict[str, int] = defaultdict(int)
        lang_sizes: dict[str, int] = defaultdict(int)
        dir_sizes: dict[str, int] = defaultdict(int)
        dir_file_counts: dict[str, int] = defaultdict(int)

        all_dirs: set[str] = set()
        all_files_list: list[str] = []

        for root_str, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            root = Path(root_str)
            rel = root.relative_to(workspace_path)
            is_root = rel == Path(".")

            for d in dirs:
                rel_dir = str(rel / d) if not is_root else d
                all_dirs.add(rel_dir)

            for f in files:
                if f.startswith(".") and f.lower() not in {
                    "dockerfile", ".env", ".env.example", ".gitignore",
                    ".dockerignore", ".editorconfig", ".prettierrc",
                    ".eslintrc", ".python-version", ".node-version",
                }:
                    continue
                if f.lower() in IGNORED_FILES:
                    continue

                rel_file = str(rel / f) if not is_root else f
                full_path = str(root / f)
                all_files_list.append(rel_file)

                ext = os.path.splitext(f)[1].lower()
                lang = EXTENSION_LANGUAGE_MAP.get(ext)
                if f.lower() == "dockerfile":
                    lang = "Docker"

                try:
                    fsize = os.path.getsize(full_path)
                    file_sizes[rel_file] = fsize
                    lang_sizes[lang or "Other"] += fsize

                    parts = rel_file.replace("\\", "/").split("/")
                    for i in range(1, len(parts) + 1):
                        parent = "/".join(parts[:i])
                        dir_sizes[parent] += fsize
                        dir_file_counts[parent] += 1
                except OSError:
                    fsize = 0

                if lang:
                    all_source_files.append(rel_file)
                    file_languages[rel_file] = lang
                    lang_file_counts[lang] += 1

                    try:
                        content = Path(full_path).read_text(encoding="utf-8", errors="ignore")
                        file_contents[rel_file] = content
                        lines = content.splitlines()
                        total = len(lines)
                        blank = _count_blank_lines(content)
                        comments = _count_comment_lines(content, lang)
                        funcs = _detect_functions(content, lang)
                        classes = _detect_classes(content, lang)
                        complexity = _calc_cyclomatic(content, lang)
                        func_lengths = _compute_function_lengths(content, lang)
                        class_szs = _compute_class_sizes(content, lang)

                        file_lines[rel_file] = total
                        file_blank[rel_file] = blank
                        file_comments[rel_file] = comments
                        file_functions[rel_file] = funcs
                        file_classes[rel_file] = classes
                        file_complexity[rel_file] = complexity
                        file_func_lengths[rel_file] = func_lengths
                        file_class_sizes[rel_file] = class_szs

                        language_loc[lang] = language_loc.get(lang, 0) + total
                    except Exception:
                        pass

        if not all_source_files:
            return self._empty_result()

        total_lines = sum(file_lines.values()) if file_lines else 0
        total_blank = sum(file_blank.values()) if file_blank else 0
        total_comments = sum(file_comments.values()) if file_comments else 0
        total_code = total_lines - total_blank - total_comments
        comment_ratio = round(total_comments / total_lines * 100, 1) if total_lines > 0 else 0.0
        code_files = len(all_source_files)
        total_size = sum(file_sizes.values())
        avg_file_size = round(total_size / code_files, 1) if code_files > 0 else 0.0

        largest_file = ""
        largest_file_size = 0
        smallest_file = ""
        smallest_file_size = float("inf")
        for fname, fsize in file_sizes.items():
            if fsize > largest_file_size:
                largest_file = fname
                largest_file_size = fsize
            if fsize < smallest_file_size:
                smallest_file = fname
                smallest_file_size = fsize

        if smallest_file_size == float("inf"):
            smallest_file_size = 0

        all_functions: list[str] = []
        all_classes: list[str] = []
        all_complexities: list[int] = []
        all_func_lengths: list[int] = []
        all_class_sizes_list: list[int] = []

        for fname in all_source_files:
            all_functions.extend(file_functions.get(fname, []))
            all_classes.extend(file_classes.get(fname, []))
            cmplx = file_complexity.get(fname, 1)
            all_complexities.append(cmplx)
            all_func_lengths.extend(file_func_lengths.get(fname, []))
            all_class_sizes_list.extend(file_class_sizes.get(fname, []))

        total_functions = len(all_functions)
        total_classes = len(all_classes)
        avg_complexity = round(sum(all_complexities) / len(all_complexities), 1) if all_complexities else 0.0
        max_complexity = max(all_complexities) if all_complexities else 0

        low_c = sum(1 for c in all_complexities if c <= 5)
        medium_c = sum(1 for c in all_complexities if 6 <= c <= 10)
        high_c = sum(1 for c in all_complexities if 11 <= c <= 20)
        critical_c = sum(1 for c in all_complexities if c > 20)

        total_dist = len(all_complexities) if all_complexities else 1
        complexity_dist = [
            {"label": "Low (1-5)", "count": low_c, "percentage": round(low_c / total_dist * 100, 1)},
            {"label": "Medium (6-10)", "count": medium_c, "percentage": round(medium_c / total_dist * 100, 1)},
            {"label": "High (11-20)", "count": high_c, "percentage": round(high_c / total_dist * 100, 1)},
            {"label": "Critical (>20)", "count": critical_c, "percentage": round(critical_c / total_dist * 100, 1)},
        ]

        avg_func_length = round(sum(all_func_lengths) / len(all_func_lengths), 1) if all_func_lengths else 0.0
        avg_class_size = round(sum(all_class_sizes_list) / len(all_class_sizes_list), 1) if all_class_sizes_list else 0.0

        maintainability_score = self._calc_maintainability(
            comment_ratio, avg_complexity, total_code, code_files, total_functions, total_classes
        )
        maintainability_grade = self._score_to_grade(maintainability_score)

        code_organization = self._detect_organization_issues(
            all_files_list, all_dirs, file_sizes, file_lines
        )
        code_style = self._detect_style_issues(
            file_contents, file_languages,
            file_functions, file_classes,
            all_source_files, file_lines, file_sizes,
        )

        python_files = lang_file_counts.get("Python", 0)
        javascript_files = lang_file_counts.get("JavaScript", 0) + lang_file_counts.get("TypeScript", 0)
        html_files = lang_file_counts.get("HTML", 0)
        css_files = lang_file_counts.get("CSS", 0) + lang_file_counts.get("SCSS", 0)
        json_files = lang_file_counts.get("JSON", 0)
        markdown_files = lang_file_counts.get("Markdown", 0)

        all_langs = set(file_languages.values())
        image_count = 0
        video_count = 0
        other_count = 0
        for fname in all_files_list:
            ext = os.path.splitext(fname)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                image_count += 1
            elif ext in VIDEO_EXTENSIONS:
                video_count += 1
            elif ext not in {os.path.splitext(f)[1].lower() for f in all_source_files}:
                if ext in ASSET_EXTENSIONS or ext in SCRIPT_EXTENSIONS:
                    other_count += 1

        language_distribution = []
        total_lang_files = sum(lang_file_counts.values())
        for lang in sorted(lang_file_counts.keys()):
            language_distribution.append({
                "language": lang,
                "file_count": lang_file_counts[lang],
                "percentage": round(lang_file_counts[lang] / total_lang_files * 100, 1) if total_lang_files > 0 else 0.0,
            })

        total_loc = sum(language_loc.values()) or 1
        language_loc_list = [
            {"language": lang, "lines": lines, "percentage": round(lines / total_loc * 100, 1)}
            for lang, lines in sorted(language_loc.items(), key=lambda x: -x[1])
        ]

        sorted_dirs = sorted(
            [(d, dir_file_counts[d], dir_sizes[d]) for d in all_dirs if dir_file_counts[d] > 0],
            key=lambda x: -x[2],
        )[:10]
        largest_dirs = [{"path": d, "file_count": c, "size": s} for d, c, s in sorted_dirs]

        sorted_files = sorted(
            [(f, file_sizes[f], file_lines.get(f, 0)) for f in all_source_files if f in file_sizes],
            key=lambda x: -x[1],
        )[:10]
        largest_files_list = [{"path": f, "size": s, "lines": l} for f, s, l in sorted_files]

        recommendations = self._generate_recommendations(
            code_organization, code_style, maintainability_grade,
            comment_ratio, avg_complexity, total_functions, total_classes,
            all_complexities, all_func_lengths,
        )

        return {
            "code_metrics": {
                "total_lines": total_lines,
                "code_lines": total_code,
                "blank_lines": total_blank,
                "comment_lines": total_comments,
                "comment_ratio": comment_ratio,
                "code_files": code_files,
                "avg_file_size": avg_file_size,
                "largest_file": largest_file,
                "largest_file_size": largest_file_size,
                "smallest_file": smallest_file,
                "smallest_file_size": smallest_file_size,
                "avg_function_length": avg_func_length,
                "avg_class_size": avg_class_size,
            },
            "complexity": {
                "total_functions": total_functions,
                "total_classes": total_classes,
                "avg_cyclomatic_complexity": avg_complexity,
                "max_complexity": max_complexity,
                "low_count": low_c,
                "medium_count": medium_c,
                "high_count": high_c,
                "critical_count": critical_c,
            },
            "complexity_distribution": complexity_dist,
            "maintainability": {
                "score": maintainability_score,
                "grade": maintainability_grade,
            },
            "code_organization": code_organization,
            "code_style": code_style,
            "project_stats": {
                "python_files": python_files,
                "javascript_files": javascript_files,
                "html_files": html_files,
                "css_files": css_files,
                "json_files": json_files,
                "markdown_files": markdown_files,
                "images": image_count,
                "videos": video_count,
                "other_assets": other_count,
            },
            "language_distribution": language_distribution,
            "language_loc": language_loc_list,
            "largest_directories": largest_dirs,
            "largest_files": largest_files_list,
            "recommendations": recommendations,
        }

    def _calc_maintainability(
        self, comment_ratio: float, avg_complexity: float,
        total_code: int, code_files: int, total_functions: int, total_classes: int,
    ) -> int:
        score = 100
        if comment_ratio < 5:
            score -= 15
        elif comment_ratio < 15:
            score -= 5
        if avg_complexity > 10:
            score -= 20
        elif avg_complexity > 5:
            score -= 10
        if code_files > 0:
            avg_loc_per_file = total_code / code_files
            if avg_loc_per_file > 500:
                score -= 15
            elif avg_loc_per_file > 200:
                score -= 5
        if total_functions > 0 and total_classes > 0:
            ratio = total_functions / total_classes
            if ratio > 20:
                score -= 10
        if comment_ratio > 40:
            score += 5
        if avg_complexity <= 3:
            score += 10
        func_per_file = total_functions / code_files if code_files > 0 else 0
        if func_per_file > 0 and func_per_file < 5:
            score += 5
        return max(0, min(100, score))

    @staticmethod
    def _score_to_grade(score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 65:
            return "C"
        if score >= 50:
            return "D"
        return "F"

    def _detect_organization_issues(
        self, all_files: list[str], all_dirs: set[str],
        file_sizes: dict[str, int], file_lines: dict[str, int],
    ) -> list[dict]:
        issues: list[dict] = []

        dup_files = _find_duplicate_filenames(all_files)
        for d in dup_files[:5]:
            issues.append({"type": "duplicate_filename", "detail": d, "severity": "warning"})

        dir_names = [os.path.basename(d) for d in all_dirs if d]
        dup_modules = _find_duplicate_modules(dir_names)
        for d in dup_modules[:5]:
            issues.append({"type": "duplicate_module", "detail": d, "severity": "warning"})

        for fname, fsize in file_sizes.items():
            if fsize > 500 * 1024:
                issues.append({"type": "large_file", "detail": f"{fname} ({fsize / 1024:.0f} KB)", "severity": "warning"})

        for d in all_dirs:
            depth = d.count("/") + 1
            if depth > 8:
                issues.append({"type": "deep_nesting", "detail": f"Directory `{d}` has depth {depth}", "severity": "info"})

        empty_dirs = _find_empty_dirs(all_dirs, all_files)
        for d in empty_dirs[:5]:
            issues.append({"type": "empty_folder", "detail": f"`{d}`", "severity": "info"})

        return issues[:20]

    def _detect_style_issues(
        self, file_contents: dict[str, str], file_languages: dict[str, str],
        file_functions: dict[str, list[str]], file_classes: dict[str, list[str]],
        all_source_files: list[str], file_lines: dict[str, int],
        file_sizes: dict[str, int],
    ) -> list[dict]:
        issues: list[dict] = []

        for fname, funcs in file_functions.items():
            for func in funcs:
                content = file_contents.get(fname, "")
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if f"def {func}" in line or f"function {func}" in line:
                        func_end = i + 1
                        while func_end < len(lines) and (
                            lines[func_end].startswith((" ", "\t")) or not lines[func_end].strip()
                        ):
                            func_end += 1
                        length = func_end - i
                        if length > 100:
                            issues.append({
                                "type": "long_function",
                                "detail": f"`{func}` in {fname} ({length} lines)",
                                "severity": "warning",
                            })
                        break

        for fname, classes in file_classes.items():
            content = file_contents.get(fname, "")
            lines = content.splitlines()
            for cls in classes:
                for i, line in enumerate(lines):
                    if f"class {cls}" in line or line.strip().startswith(f"class {cls}"):
                        cls_end = i + 1
                        while cls_end < len(lines) and (
                            lines[cls_end].startswith((" ", "\t")) or not lines[cls_end].strip()
                        ):
                            cls_end += 1
                        length = cls_end - i
                        if length > 500:
                            issues.append({
                                "type": "long_class",
                                "detail": f"`{cls}` in {fname} ({length} lines)",
                                "severity": "warning",
                            })
                        break

        for fname, fsize in file_sizes.items():
            fsize_b = fsize
            lines_cnt = file_lines.get(fname, 0)
            if lines_cnt > 2000 or fsize_b > 1024 * 1024:
                issues.append({
                    "type": "very_large_file",
                    "detail": f"`{fname}` ({lines_cnt} lines, {fsize_b / 1024:.0f} KB)",
                    "severity": "warning",
                })

        conventions = _detect_mixed_naming(all_source_files)
        if conventions:
            issues.append({
                "type": "mixed_naming",
                "detail": f"Mixed conventions detected: {', '.join(conventions)}",
                "severity": "info",
            })

        for fname in all_source_files[:30]:
            lang = file_languages.get(fname)
            content = file_contents.get(fname, "")
            if content and lang:
                import_count = _detect_large_imports(content, lang)
                if import_count > 15:
                    issues.append({
                        "type": "large_imports",
                        "detail": f"`{fname}` has {import_count} imports",
                        "severity": "info",
                    })

        return issues[:20]

    @staticmethod
    def _generate_recommendations(
        code_org: list[dict], code_style: list[dict],
        maintainability_grade: str, comment_ratio: float,
        avg_complexity: float, total_functions: int, total_classes: int,
        all_complexities: list[int], all_func_lengths: list[int],
    ) -> list[dict]:
        recs: list[dict] = []
        seen = set()

        def add_rec(rtype: str, detail: str):
            key = f"{rtype}:{detail}"
            if key not in seen:
                seen.add(key)
                recs.append({"type": rtype, "detail": detail})

        if maintainability_grade in ("D", "F"):
            add_rec("maintainability", "Improve code maintainability by reducing complexity and adding comments")
        elif maintainability_grade == "C":
            add_rec("maintainability", "Consider refactoring complex modules to improve maintainability")

        if avg_complexity > 10:
            add_rec("complexity", f"Average cyclomatic complexity is {avg_complexity}. Aim for under 10 by splitting complex functions")
        high_critical = sum(1 for c in all_complexities if c > 10)
        if high_critical > 5:
            add_rec("complexity", f"Found {high_critical} functions with high or critical complexity. Refactor into smaller units")

        if comment_ratio < 5:
            add_rec("documentation", "Code has very few comments ({comment_ratio}%). Add inline documentation for complex logic")
        elif comment_ratio > 50:
            add_rec("documentation", "High comment-to-code ratio ({comment_ratio}%). Consider if some comments are redundant")

        for issue in code_org:
            if issue["type"] == "duplicate_filename":
                add_rec("duplication", f"Duplicate filenames: {issue['detail']}. Rename to avoid confusion")
            elif issue["type"] == "duplicate_module":
                add_rec("duplication", f"Duplicate modules: {issue['detail']}. Consolidate or rename")
            elif issue["type"] == "empty_folder":
                add_rec("organization", f"Empty folder: {issue['detail']}. Remove or populate")
            elif issue["type"] == "large_file":
                add_rec("modularization", f"Large file: {issue['detail']}. Consider splitting into smaller modules")

        for issue in code_style:
            if issue["type"] == "long_function":
                add_rec("refactoring", f"Long function: {issue['detail']}. Break into smaller helper functions")
            elif issue["type"] == "long_class":
                add_rec("refactoring", f"Large class: {issue['detail']}. Consider splitting by responsibility")
            elif issue["type"] == "very_large_file":
                add_rec("modularization", f"Large file: {issue['detail']}. Split into smaller focused modules")
            elif issue["type"] == "large_imports":
                add_rec("organization", f"Large imports: {issue['detail']}. Consider using lazy imports or re-export modules")

        long_funcs = sum(1 for l in all_func_lengths if l > 50)
        if long_funcs > 5:
            add_rec("refactoring", f"{long_funcs} functions exceed 50 lines. Extract utilities to reduce function sizes")

        if not recs:
            add_rec("good_job", "Codebase metrics look healthy. Continue maintaining current standards")

        return recs[:15]

    @staticmethod
    def _empty_result() -> dict:
        return {
            "code_metrics": {
                "total_lines": 0, "code_lines": 0, "blank_lines": 0,
                "comment_lines": 0, "comment_ratio": 0.0, "code_files": 0,
                "avg_file_size": 0.0, "largest_file": "", "largest_file_size": 0,
                "smallest_file": "", "smallest_file_size": 0,
                "avg_function_length": 0.0, "avg_class_size": 0.0,
            },
            "complexity": {
                "total_functions": 0, "total_classes": 0,
                "avg_cyclomatic_complexity": 0.0, "max_complexity": 0,
                "low_count": 0, "medium_count": 0, "high_count": 0, "critical_count": 0,
            },
            "complexity_distribution": [],
            "maintainability": {"score": 0, "grade": "F"},
            "code_organization": [],
            "code_style": [],
            "project_stats": {
                "python_files": 0, "javascript_files": 0, "html_files": 0,
                "css_files": 0, "json_files": 0, "markdown_files": 0,
                "images": 0, "videos": 0, "other_assets": 0,
            },
            "language_distribution": [],
            "language_loc": [],
            "largest_directories": [],
            "largest_files": [],
            "recommendations": [],
        }
