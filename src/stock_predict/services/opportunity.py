import pandas as pd
from sqlalchemy.orm import Session

from stock_predict.models.item import Item
from stock_predict.repositories.item_repository import ItemRepository
from stock_predict.schemas.opportunity import ItemOpportunity, OpportunityRequest
from stock_predict.services.demand import get_demand_series
from stock_predict.services.prediction import MODEL_FACTORIES


def _classify_trend(historical_average: float, forecasted_average: float, threshold_pct: float) -> tuple[str, float]:
    if historical_average == 0:
        trend_pct = 100.0 if forecasted_average > 0 else 0.0
    else:
        trend_pct = (forecasted_average - historical_average) / historical_average * 100

    if trend_pct > threshold_pct:
        return "crescimento", trend_pct
    if trend_pct < -threshold_pct:
        return "queda", trend_pct
    return "estavel", trend_pct


def compute_opportunity(
        item: Item,
        series: pd.DataFrame,
        frequency: str,
        request: OpportunityRequest,
) -> ItemOpportunity | None:
    """ Classifica a tendência de demanda de um item e estima o volume total previsto, sem depender do banco """
    if series.empty:
        return None

    historical_average_demand = float(series["demand"].mean())
    model_factory = MODEL_FACTORIES[request.model_name]

    reliable = True
    try:
        model = model_factory()
        model.fit(series, frequency)
        forecast = model.predict(request.horizon)

        forecasted_average_demand = float(forecast["predicted_quantity"].mean())
        total_forecasted_demand = float(forecast["predicted_quantity"].sum())
    except ValueError:
        reliable = False
        forecasted_average_demand = historical_average_demand
        total_forecasted_demand = historical_average_demand * request.horizon

    trend, trend_pct = _classify_trend(
        historical_average_demand, forecasted_average_demand, request.trend_threshold_pct
    )

    return ItemOpportunity(
        item_id=item.id,
        item_description=item.description,
        granularity=request.granularity,
        model_name=request.model_name,
        historical_average_demand=historical_average_demand,
        forecasted_average_demand=forecasted_average_demand,
        total_forecasted_demand=total_forecasted_demand,
        trend=trend,
        trend_pct=trend_pct,
        reliable=reliable,
    )


def generate_opportunities(db: Session, request: OpportunityRequest) -> list[ItemOpportunity]:
    items = ItemRepository(db).list_all()

    opportunities = []
    for item in items:
        series, frequency = get_demand_series(db, item.id, request.granularity)
        opportunity = compute_opportunity(item, series, frequency, request)
        if opportunity is not None:
            opportunities.append(opportunity)

    return sorted(opportunities, key=lambda o: o.total_forecasted_demand, reverse=True)
