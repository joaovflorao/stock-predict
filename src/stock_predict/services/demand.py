from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from stock_predict.repositories.movement_repository import MovementRepository
from stock_predict.schemas.config import Granularity
from stock_predict.services.aggregation import build_time_series, granularity_to_frequency


def get_demand_series(
        db: Session,
        item_id: int,
        granularity: Granularity,
        start_date: date| None = None,
        end_date: date| None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Monta a série temporal de demanda de um item a partir do DB

    Retorna a série e a frequência correspondente a granularidade, para ser repassada a ForecastModel.fit()
    """
    movements = MovementRepository(db).get_by_item(item_id, start_date, end_date)
    series = build_time_series(movements, granularity)
    frequency = granularity_to_frequency(granularity)

    return series, frequency
