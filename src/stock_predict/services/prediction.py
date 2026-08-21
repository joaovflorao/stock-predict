from typing import Literal

import pandas as pd
from sqlalchemy.orm import Session

from stock_predict.ml.baseline_model import BaselineForecastModel
from stock_predict.ml.lstm_model import LSTMForecastModel
from stock_predict.ml.xgboost_model import XGBoostForecastModel
from stock_predict.schemas.config import Granularity
from stock_predict.schemas.predict import PredictRequest, PredictionResult
from stock_predict.services.demand import get_demand_series
from stock_predict.services.evaluation import compare_models, walk_forward_validation


CONFIDENCE_LEVEL = 95.0
Z_SCORE_95 = 1.96


MODEL_FACTORIES = {
    "baseline": BaselineForecastModel,
    "xgboost": XGBoostForecastModel,
    "lstm": LSTMForecastModel,
}


def _build_predictions(
        item_id: int,
        model_name: str,
        forecast,
        rmse: float,
        reliable: bool = True,
) -> list[PredictionResult]:
    margin = Z_SCORE_95 * rmse
    return [
        PredictionResult(
            item_id=item_id,
            period=row.period,
            predicted_quantity=row.predicted_quantity,
            lower_bound=max(row.predicted_quantity - margin, 0),
            upper_bound=row.predicted_quantity + margin,
            confidence_level=CONFIDENCE_LEVEL,
            model_name=model_name,
            reliable=reliable,
        )
        for row in forecast.itertuples()
    ]


def _fallback_forecast(series: pd.DataFrame, horizon: int, frequency: str) -> pd.DataFrame:
    """ Previsão simples (demanda média histórica) usada quando o histórico é curto demais para o modelo escolhido """
    average_demand = float(series["demand"].mean())
    offset = pd.tseries.frequencies.to_offset(frequency)
    last_period = series["period"].iloc[-1]
    periods_list = [last_period + offset * (i + 1) for i in range(horizon)]

    return pd.DataFrame({
        "period": periods_list,
        "predicted_quantity": [average_demand] * horizon,
    })


def generate_prediction(db: Session, request: PredictRequest) -> list[PredictionResult]:
    series, frequency = get_demand_series(db, request.item_id, request.granularity)
    model_factory = MODEL_FACTORIES[request.model_name]

    reliable = True
    try:
        validation = walk_forward_validation(
            series, model_factory, request.horizon,
            request.min_train_size, frequency
        )
        rmse = validation["metrics"]["rmse"]

        model = model_factory()
        model.fit(series, frequency)
        forecast = model.predict(request.horizon)
    except ValueError:
        if series.empty:
            raise

        reliable = False
        rmse = 0.0
        forecast = _fallback_forecast(series, request.horizon, frequency)

    return _build_predictions(request.item_id, request.model_name, forecast, rmse, reliable)


def run_full_analysis(
        db: Session,
        item_id: int,
        granularity: Granularity,
        horizon: int,
        min_train_size: int = 8,
        model_name: Literal["baseline", "xgboost", "lstm"] = "xgboost"
) -> dict:
    """ Executa a análise completa de um item numa única sessão no DB """
    series, frequency = get_demand_series(db, item_id, granularity)

    comparison = compare_models(series, frequency, horizon, min_train_size, MODEL_FACTORIES)

    request = PredictRequest(
        item_id=item_id,
        granularity=granularity,
        horizon=horizon,
        min_train_size=min_train_size,
        model_name=model_name,
    )
    predictions = generate_prediction(db, request)

    history = [
        {
            "period": str(row.period.date()),
            "demand": float(row.demand)
        }
        for row in series.itertuples()
    ]
    return {
        "history": history,
        "comparison": comparison,
        "predictions": predictions,
    }
