from repositories.forecast_repository import ForecastRepository
from repositories.dataset_repository import DatasetRepository
from pipelines.validation_pipeline import ValidationPipeline
from pipelines.eda_pipeline import EDAPipeline
from pipelines.preprocessing_pipeline import PreprocessingPipeline
from pipelines.forecast_pipeline import ForecastPipeline
from pipelines.comparison_pipeline import ComparisonPipeline
from pipelines.report_pipeline import ReportPipeline
class ForecastService:
    def __init__(self):
        self.forecast_repo = ForecastRepository()
        self.dataset_repo = DatasetRepository()
        self.validator = ValidationPipeline()
        self.eda = EDAPipeline()
        self.preprocessor = PreprocessingPipeline()
        self.forecast_pipeline = ForecastPipeline()
        self.comparison = ComparisonPipeline()
        self.report = ReportPipeline()
    def generate_forecast(self):
        data = self.dataset_repo.get_dataset()
        validated = self.validator.validate(data)
        eda_result = self.eda.analyze(validated)
        preprocessed = self.preprocessor.process(eda_result)
        forecast = self.forecast_pipeline.run(preprocessed)
        compared = self.comparison.compare(forecast)
        return self.report.generate(compared)
    def generate_report(self):
        data = self.forecast_repo.get_all_forecasts()
        return self.report.generate(data)
