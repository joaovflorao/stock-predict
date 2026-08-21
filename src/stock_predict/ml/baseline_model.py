import pandas as pd
from .base import ForecastModel


class BaselineForecastModel(ForecastModel):
    def __init__(self):
        self._last_demand = None
        self._last_period = None
        self._frequency = None

    def fit(self, series: pd.DataFrame, frequency: str) -> None:
        if series.empty:
            raise ValueError("Série vazia. Não é possível ajustar o modelo baseline.")

        self._last_demand = float(series["demand"].iloc[-1])
        self._last_period = series["period"].iloc[-1]
        self._frequency = pd.tseries.frequencies.to_offset(frequency)

    def predict(self, horizon: int) -> pd.DataFrame:
        periods_list = [
            self._last_period + self._frequency * (i + 1)
            for i in range(horizon)
        ]
        return pd.DataFrame({
            "period": periods_list,
            "predicted_quantity": [self._last_demand] * horizon,
        })
