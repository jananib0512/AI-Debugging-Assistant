from models.forecast_model import ForecastModel
class ForecastRepository:
    def __init__(self):
        self.model = ForecastModel()
    def get_all_forecasts(self):
        return self.model.query_all()
    def save_forecast(self, forecast):
        return self.model.save(forecast)
