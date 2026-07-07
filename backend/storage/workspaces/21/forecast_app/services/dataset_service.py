from repositories.dataset_repository import DatasetRepository
from pipelines.validation_pipeline import ValidationPipeline
class DatasetService:
    def __init__(self):
        self.dataset_repo = DatasetRepository()
        self.validator = ValidationPipeline()
    def upload_dataset(self):
        data = self.dataset_repo.save_upload()
        return self.validator.validate(data)
