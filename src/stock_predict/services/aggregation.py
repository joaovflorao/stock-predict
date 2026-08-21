import pandas as pd

from stock_predict.models.movement import Movement
from stock_predict.schemas.config import Granularity
from stock_predict.schemas.movement import MovementType


DEMAND_MOVEMENT_TYPES = {
    MovementType.SALE,
    MovementType.CONSUME,
}
GRANULARITY_TO_PANDAS_FREQ = {
    Granularity.DAILY: "D",
    Granularity.WEEKLY: "W",
    Granularity.MONTHLY: "MS",
    Granularity.ANNUAL: "YS",
}


def granularity_to_frequency(granularity: Granularity) -> str:
    return GRANULARITY_TO_PANDAS_FREQ[granularity]


def movements_to_dataframe(movements: list[Movement]) -> pd.DataFrame:
    """ Converte a lista de Movement em um pandas DataFrame """
    return pd.DataFrame(
        [
            {
                "movement_date": move.movement_date,
                "quantity": move.quantity,
                "movement_type": move.movement_type,
            }
            for move in movements
        ]
    )


def filter_demand_movements(df: pd.DataFrame) -> pd.DataFrame:
    """ Filtra os tipos de movimento considerados """
    return df[df["movement_type"].isin(DEMAND_MOVEMENT_TYPES)]


def build_time_series(
        movements: list[Movement],
        granularity: Granularity
) -> pd.DataFrame:
    """
        Agrega as movimentações de um item em uma série temporal de demanda.

        Retorna um DataFrame com colunas [period, demand], ordenando cronologicamente,
        com períodos sem movimentação preenchidos como 0 (ausência de venda/consumo)
    """

    if not movements:
        return pd.DataFrame(columns=["period", "demand"])

    df = movements_to_dataframe(movements)
    df = filter_demand_movements(df)

    if df.empty:
        return pd.DataFrame(columns=["period", "demand"])

    df["movement_date"] = pd.to_datetime(df["movement_date"])
    df["quantity"] = df["quantity"].astype(float)

    frequency = granularity_to_frequency(granularity)
    series = (
        df.set_index("movement_date")["quantity"]
        .resample(frequency)
        .sum()
    )
    full_range = pd.date_range(
        start=series.index.min(),
        end=series.index.max(),
        freq=frequency
    )
    series = series.reindex(full_range, fill_value=0.0)

    return (
        series
        .rename("demand")
        .rename_axis("period")
        .reset_index()
    )
