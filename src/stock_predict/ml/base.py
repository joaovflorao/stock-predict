from abc import ABC, abstractmethod
import pandas as pd


class ForecastModel(ABC):
    @abstractmethod
    def fit(self, series: pd.DataFrame, frequency: str) -> None:
        """ series: colunas [period, demand] ordenadas cronologicamente """
        ...

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """ retorna as colunas [period, predicted_quantity] """
        ...
