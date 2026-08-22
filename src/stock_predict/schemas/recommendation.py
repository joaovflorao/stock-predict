from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from stock_predict.schemas.config import Granularity
from stock_predict.schemas.predict import PredictRequest


class PurchaseRecommendationRequest(PredictRequest):
    """ Parâmetros para calcular quando e quanto comprar de um item """
    lead_time_periods: int = Field(..., gt=0, description="Tempo de reposição, em períodos da granularidade escolhida")


class PurchaseRecommendationBulkRequest(BaseModel):
    """ Parâmetros para calcular quando e quanto comprar de todos os itens """
    granularity: Granularity
    horizon: int = Field(..., gt=0)
    min_train_size: int = Field(8, gt=0)
    model_name: Literal["baseline", "xgboost", "lstm"] = "xgboost"
    lead_time_periods: int = Field(..., gt=0, description="Tempo de reposição, em períodos da granularidade escolhida")


class PurchaseRecommendation(BaseModel):
    """ Resultado da recomendação de compra """
    item_id: int
    granularity: Granularity
    lead_time_periods: int
    model_name: str

    current_stock: Decimal
    average_demand_per_period: float = Field(..., ge=0)
    safety_stock: float = Field(..., ge=0)
    reorder_point: float = Field(..., ge=0)
    should_reorder_now: bool
    recommended_order_quantity: float = Field(..., ge=0)
    periods_until_stockout: int | None = None
    next_reorder_date: date | None = None

    reliable: bool = Field(
        ...,
        description="False quando o histórico do item é curto demais para o modelo de previsão, "
                    "e a recomendação foi calculada com base na demanda média histórica",
    )

    model_config = {"from_attributes": True}
