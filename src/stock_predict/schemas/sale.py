from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class TrendDirection(str, Enum):
    """ Direção da tendência """
    GROWTH  = "Crescimento"
    DECLINE = "Queda"
    STABLE  = "Estável"


class SaleTrend(BaseModel):
    """ Tendência de vendas """
    item_id: int
    predicted_quantity: Decimal = Field(..., ge=0)
    trend: TrendDirection
    rank: int = Field(..., ge=0)

    model_config = {"from_attributes": True}
