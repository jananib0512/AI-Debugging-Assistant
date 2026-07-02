from pathlib import Path

from app.schemas.config_detection import ConfigFilesDetectionResult

# Every config file detection entry is defined here — the single authoritative list.
_CONFIG_FILES: dict[str, str] = {
    "package_json": "package.json",
    "requirements_txt": "requirements.txt",
    "pyproject_toml": "pyproject.toml",
    "poetry_lock": "poetry.lock",
    "dockerfile": "Dockerfile",
    "tsconfig_json": "tsconfig.json",
    "angular_json": "angular.json",
    "cargo_toml": "Cargo.toml",
    "pom_xml": "pom.xml",
    "build_gradle": "build.gradle",
    "composer_json": "composer.json",
    "env_example": ".env.example",
    "gitignore": ".gitignore",
    "license": "LICENSE",
}

# Files that may have alternative names/extensions.
_README_VARIANTS: set[str] = {"README.md", "README.rst", "README.txt", "README"}
_DOCKER_COMPOSE_VARIANTS: set[str] = {"docker-compose.yml", "docker-compose.yaml"}
_NEXT_CONFIG_VARIANTS: set[str] = {"next.config.js", "next.config.mjs", "next.config.ts"}


class ConfigurationDetectionRepository:
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path.resolve()

    def detect(self) -> ConfigFilesDetectionResult:
        found: list[str] = []
        missing: list[str] = []

        # ---- README: recursive, case-insensitive ----
        readme_exists = self._detect_readme(found)

        # ---- Exact-name files (root level) ----
        file_map: dict[str, bool] = {}
        for key, filename in _CONFIG_FILES.items():
            exists = (self.workspace / filename).exists()
            file_map[key] = exists
            self._track(filename, exists, found, missing)

        # ---- docker-compose (root, two variants) ----
        dc_exists = self._detect_variant(_DOCKER_COMPOSE_VARIANTS, found, missing)

        # ---- vite.config.* (root, glob) ----
        vite_exists = self._detect_vite_config(found)

        # ---- next.config.* (root, three variants) ----
        next_exists = self._detect_variant(_NEXT_CONFIG_VARIANTS, found, missing)

        return ConfigFilesDetectionResult(
            readme=readme_exists,
            package_json=file_map["package_json"],
            requirements_txt=file_map["requirements_txt"],
            pyproject_toml=file_map["pyproject_toml"],
            poetry_lock=file_map["poetry_lock"],
            dockerfile=file_map["dockerfile"],
            docker_compose=dc_exists,
            vite_config=vite_exists,
            tsconfig_json=file_map["tsconfig_json"],
            next_config=next_exists,
            angular_json=file_map["angular_json"],
            cargo_toml=file_map["cargo_toml"],
            pom_xml=file_map["pom_xml"],
            build_gradle=file_map["build_gradle"],
            composer_json=file_map["composer_json"],
            env_example=file_map["env_example"],
            gitignore=file_map["gitignore"],
            license=file_map["license"],
            files_found=sorted(found),
            files_missing=sorted(missing),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _track(
        filename: str, exists: bool,
        found: list[str], missing: list[str],
    ) -> None:
        if exists:
            found.append(filename)
        else:
            missing.append(filename)

    def _detect_readme(self, found: list[str]) -> bool:
        for item in self.workspace.rglob("*"):
            if not item.is_file():
                continue
            name_lower = item.name.lower()
            for variant in _README_VARIANTS:
                if name_lower == variant.lower():
                    found.append(item.name)
                    return True
        return False

    def _detect_variant(
        self, variants: set[str],
        found: list[str], missing: list[str],
    ) -> bool:
        for v in variants:
            if (self.workspace / v).exists():
                found.append(v)
                return True
        missing.append(list(variants)[0])
        return False

    def _detect_vite_config(self, found: list[str]) -> bool:
        for p in self.workspace.glob("vite.config.*"):
            found.append(p.name)
            return True
        return False
