from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field
from stock_predict.schemas.config import Granularity


class PredictionResult(BaseModel):
    """ Resultado da predição """
    item_id: int
    period: date
    predicted_quantity: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    confidence_level: float = Field(..., ge=0, le=100, description="Nível de confiança do resultado (%)")
    model_name: str
    reliable: bool = Field(
        True,
        description="False quando o histórico do item é curto demais para o modelo escolhido, "
                    "e a previsão foi calculada com base na demanda média histórica",
    )

    model_config = {"from_attributes": True}


class EvaluationResult(BaseModel):
    """ Valores dos resultados """
    model_name: str
    wape: float= Field(..., ge=0)
    mae: float= Field(..., ge=0)
    rmse: float= Field(..., ge=0)


class SeriesRequest(BaseModel):
    """  """
    item_id: int
    granularity: Granularity
    horizon: int = Field(..., gt=0)
    min_train_size: int = Field(8, gt=0)


class PredictRequest(SeriesRequest):
    model_name: Literal["baseline", "xgboost", "lstm"] = "xgboost"
