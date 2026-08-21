from typing import Literal

from pydantic import BaseModel, Field

from stock_predict.schemas.config import Granularity


class OpportunityRequest(BaseModel):
    """ Parâmetros para ranquear os itens por tendência e volume de demanda prevista """
    granularity: Granularity
    horizon: int = Field(..., gt=0)
    min_train_size: int = Field(8, gt=0)
    model_name: Literal["baseline", "xgboost", "lstm"] = "xgboost"
    trend_threshold_pct: float = Field(
        5.0, ge=0, description="Variação percentual mínima para classificar como crescimento/queda"
    )


class ItemOpportunity(BaseModel):
    """ Classificação de tendência e volume previsto de um item """
    item_id: int
    item_description: str
    granularity: Granularity
    model_name: str

    historical_average_demand: float = Field(..., ge=0)
    forecasted_average_demand: float = Field(..., ge=0)
    total_forecasted_demand: float = Field(..., ge=0)
    trend: Literal["crescimento", "queda", "estavel"]
    trend_pct: float

    reliable: bool = Field(
        ...,
        description="False quando o histórico do item é curto demais para o modelo de previsão, "
                    "e a tendência foi estimada com base na demanda média histórica",
    )
