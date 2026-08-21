from typing import Literal

from sqlalchemy.orm import Session

from stock_predict.ml.baseline_model import BaselineForecastModel
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
}


def _build_predictions(
        item_id: int,
        model_name: str,
        forecast,
        rmse: float,
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
            model_name=model_name
        )
        for row in forecast.itertuples()
    ]


def generate_prediction(db: Session, request: PredictRequest) -> list[PredictionResult]:
    series, frequency = get_demand_series(db, request.item_id, request.granularity)
    model_factory = MODEL_FACTORIES[request.model_name]

    validation = walk_forward_validation(
        series, model_factory, request.horizon,
        request.min_train_size, frequency
    )
    rmse = validation["metrics"]["rmse"]

    model = model_factory()
    model.fit(series, frequency)
    forecast = model.predict(request.horizon)

    return _build_predictions(request.item_id, request.model_name, forecast, rmse)


def run_full_analysis(
        db: Session,
        item_id: int,
        granularity: Granularity,
        horizon: int,
        mint_train_size: int = 8,
        model_name: Literal["baseline", "xgboost"] = "xgboost"
) -> dict:
    """ Executa a análise completa de um item numa única sessão no DB """
    series, frequency = get_demand_series(db, item_id, granularity)

    comparison = compare_models(series, frequency, horizon, mint_train_size, MODEL_FACTORIES)
    rmse_by_model = {result.model_name: result.rmse for result in comparison}

    model_factory = MODEL_FACTORIES[model_name]
    model = model_factory()
    model.fit(series, frequency)
    forecast = model.predict(horizon)

    predictions = _build_predictions(item_id, model_name, forecast, rmse_by_model[model_name])

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
