import pandas as pd
from xgboost import XGBRegressor
from .base import ForecastModel


class XGBoostForecastModel(ForecastModel):
    def __init__(self, n_lags: int = 4):
        self.n_lags = n_lags
        self.model = XGBRegressor()
        self._last_known: list[float] = []
        self._last_period = None
        self._frequency = None

    def fit(self, series: pd.DataFrame, frequency: str) -> None:
        if len(series) <= self.n_lags:
            raise ValueError(
                f"Série tem {len(series)} períodos, mas n_lags ({self.n_lags}) exige mais "
                f"que isso para gerar ao menos uma linha de treino."
            )

        df = series.copy()
        for lag in range(1, self.n_lags + 1):
            df[f"lag_{lag}"] = df["demand"].shift(lag)
        df = df.dropna()

        x = df[[f"lag_{i}" for i in range(1, self.n_lags + 1)]]
        y = df["demand"]

        self.model.fit(x, y)

        self._last_known = series["demand"].tolist()[-self.n_lags:]
        self._last_period = series["period"].iloc[-1]
        self._frequency = pd.tseries.frequencies.to_offset(frequency)

    def predict(self, horizon: int) -> pd.DataFrame:
        history = list(self._last_known)
        predictions_list = []
        for _ in range(horizon):
            x = pd.DataFrame(
                [history[-self.n_lags:]],
                columns=[f"lag_{i}" for i in range(1, self.n_lags + 1)]
            )
            prediction = float(self.model.predict(x)[0])
            predictions_list.append(prediction)
            history.append(prediction)

        periods_list = [
            self._last_period + self._frequency * (i + 1)
            for i in range(horizon)
        ]
        return pd.DataFrame({
            "period": periods_list,
            "predicted_quantity": predictions_list
        })
