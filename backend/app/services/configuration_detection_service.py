import logging
from pathlib import Path

from app.repositories.configuration_detection_repository import (
    ConfigurationDetectionRepository,
)
from app.schemas.config_detection import ConfigFilesDetectionResult

logger = logging.getLogger(__name__)

# Module-level cache — single source of truth, persists across requests.
_cache: dict[int, ConfigFilesDetectionResult] = {}


class ConfigurationDetectionService:

    def get_config_files(
        self, project_id: int, workspace_path: Path
    ) -> ConfigFilesDetectionResult:
        if project_id in _cache:
            return _cache[project_id]

        repo = ConfigurationDetectionRepository(workspace_path)
        result = repo.detect()
        _cache[project_id] = result
        return result

    def invalidate_cache(self, project_id: int) -> None:
        _cache.pop(project_id, None)
