from models.dataset_model import DatasetModel
class DatasetRepository:
    def __init__(self):
        self.model = DatasetModel()
    def get_dataset(self):
        return self.model.get_latest()
    def save_upload(self):
        return self.model.create()
