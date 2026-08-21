import os

os.environ.setdefault("KERAS_BACKEND", "torch")

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import keras
from keras import layers

from .base import ForecastModel


class LSTMForecastModel(ForecastModel):
    def __init__(self, n_lags: int = 8, units: int = 32, epochs: int = 100):
        self.n_lags = n_lags
        self.units = units
        self.epochs = epochs
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self._last_known: list[float] = []
        self._last_period = None
        self._frequency = None

    def fit(self, series: pd.DataFrame, frequency: str) -> None:
        if len(series) <= self.n_lags:
            raise ValueError(
                f"Série tem {len(series)} períodos, mas n_lags ({self.n_lags}) exige mais "
                f"que isso para gerar ao menos uma sequência de treino."
            )

        demand = series["demand"].to_numpy(dtype="float64").reshape(-1, 1)
        scaled = self.scaler.fit_transform(demand).flatten()

        x, y = [], []
        for i in range(self.n_lags, len(scaled)):
            x.append(scaled[i - self.n_lags:i])
            y.append(scaled[i])
        x = np.array(x).reshape(-1, self.n_lags, 1)
        y = np.array(y)

        self.model = keras.Sequential([
            layers.Input(shape=(self.n_lags, 1)),
            layers.LSTM(self.units),
            layers.Dense(1),
        ])
        self.model.compile(optimizer="adam", loss="mse")
        self.model.fit(x, y, epochs=self.epochs, batch_size=8, verbose=0)

        self._last_known = scaled[-self.n_lags:].tolist()
        self._last_period = series["period"].iloc[-1]
        self._frequency = pd.tseries.frequencies.to_offset(frequency)

    def predict(self, horizon: int) -> pd.DataFrame:
        history = list(self._last_known)
        scaled_predictions = []
        for _ in range(horizon):
            x = np.array(history[-self.n_lags:]).reshape(1, self.n_lags, 1)
            scaled_prediction = float(self.model.predict(x, verbose=0)[0, 0])
            scaled_predictions.append(scaled_prediction)
            history.append(scaled_prediction)

        predictions = self.scaler.inverse_transform(
            np.array(scaled_predictions).reshape(-1, 1)
        ).flatten()
        predictions = np.clip(predictions, 0.0, None)

        periods_list = [
            self._last_period + self._frequency * (i + 1)
            for i in range(horizon)
        ]
        return pd.DataFrame({
            "period": periods_list,
            "predicted_quantity": predictions,
        })
