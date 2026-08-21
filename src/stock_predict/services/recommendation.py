from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from stock_predict.repositories.movement_repository import MovementRepository
from stock_predict.schemas.recommendation import PurchaseRecommendation, PurchaseRecommendationRequest
from stock_predict.services.aggregation import calculate_current_stock
from stock_predict.services.demand import get_demand_series
from stock_predict.services.evaluation import walk_forward_validation
from stock_predict.services.prediction import MODEL_FACTORIES, Z_SCORE_95


def _average_demand(series: pd.DataFrame) -> float:
    if series.empty:
        return 0.0
    return float(series["demand"].mean())


def _project_next_reorder_date(series: pd.DataFrame, frequency: str, current_stock: Decimal, average_demand_per_period: float):
    if average_demand_per_period <= 0 or series.empty:
        return None, None

    periods_until_stockout = max(int(float(current_stock) // average_demand_per_period), 0)
    offset = pd.tseries.frequencies.to_offset(frequency)
    last_period = series["period"].iloc[-1]
    next_reorder_date = (last_period + offset * periods_until_stockout).date()

    return periods_until_stockout, next_reorder_date


def compute_recommendation(
        series: pd.DataFrame,
        frequency: str,
        current_stock: Decimal,
        request: PurchaseRecommendationRequest,
) -> PurchaseRecommendation:
    """
        Calcula quando e quanto comprar de um item a partir da série de demanda já agregada
        e do saldo de estoque atual, sem depender do banco de dados
    """
    model_factory = MODEL_FACTORIES[request.model_name]
    forecast_horizon = max(request.horizon, request.lead_time_periods)

    reliable = True
    try:
        validation = walk_forward_validation(
            series, model_factory, request.horizon, request.min_train_size, frequency
        )
        rmse = validation["metrics"]["rmse"]

        model = model_factory()
        model.fit(series, frequency)
        forecast = model.predict(forecast_horizon)

        lead_time_forecast = forecast["predicted_quantity"].head(request.lead_time_periods)
        horizon_forecast = forecast["predicted_quantity"].head(request.horizon)

        average_demand_per_period = float(lead_time_forecast.mean()) if not lead_time_forecast.empty else 0.0
        demand_during_lead_time = float(lead_time_forecast.sum())
        demand_during_horizon = float(horizon_forecast.sum())
        safety_stock = Z_SCORE_95 * rmse * (request.lead_time_periods ** 0.5)
    except ValueError:
        reliable = False
        average_demand_per_period = _average_demand(series)
        demand_during_lead_time = average_demand_per_period * request.lead_time_periods
        demand_during_horizon = average_demand_per_period * request.horizon
        safety_stock = 0.0

    reorder_point = demand_during_lead_time + safety_stock
    should_reorder_now = float(current_stock) <= reorder_point
    recommended_order_quantity = max(demand_during_horizon + safety_stock - float(current_stock), 0.0)

    periods_until_stockout, next_reorder_date = _project_next_reorder_date(
        series, frequency, current_stock, average_demand_per_period
    )

    return PurchaseRecommendation(
        item_id=request.item_id,
        granularity=request.granularity,
        lead_time_periods=request.lead_time_periods,
        model_name=request.model_name,
        current_stock=current_stock,
        average_demand_per_period=average_demand_per_period,
        safety_stock=safety_stock,
        reorder_point=reorder_point,
        should_reorder_now=should_reorder_now,
        recommended_order_quantity=recommended_order_quantity,
        periods_until_stockout=periods_until_stockout,
        next_reorder_date=next_reorder_date,
        reliable=reliable,
    )


def generate_purchase_recommendation(db: Session, request: PurchaseRecommendationRequest) -> PurchaseRecommendation:
    movements = MovementRepository(db).get_by_item(request.item_id)
    current_stock = calculate_current_stock(movements)

    series, frequency = get_demand_series(db, request.item_id, request.granularity)

    return compute_recommendation(series, frequency, current_stock, request)
