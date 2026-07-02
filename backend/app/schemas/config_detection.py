from pydantic import BaseModel


class ConfigFilesDetectionResult(BaseModel):
    readme: bool
    package_json: bool
    requirements_txt: bool
    pyproject_toml: bool
    poetry_lock: bool
    dockerfile: bool
    docker_compose: bool
    vite_config: bool
    tsconfig_json: bool
    next_config: bool
    angular_json: bool
    cargo_toml: bool
    pom_xml: bool
    build_gradle: bool
    composer_json: bool
    env_example: bool
    gitignore: bool
    license: bool
    files_found: list[str]
    files_missing: list[str]
