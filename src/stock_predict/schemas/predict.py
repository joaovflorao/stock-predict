from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    """ Resultado da predição """
    item_id: int
    period: date
    predicted_quantity: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    confidence_level: float = Field(..., ge=0, le=100, description="Nível de confiança do resultado (%)")
    model_name: str

    model_config = {"from_attributes": True}


class EvaluationResult(BaseModel):
    """ Valores dos resultados """
    model_name: str
    wape: float= Field(..., ge=0)
    mae: float= Field(..., ge=0)
    rmse: float= Field(..., ge=0)
