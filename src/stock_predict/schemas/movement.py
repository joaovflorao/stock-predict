from datetime import date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class MovementType(str, Enum):
    """ Tipos de movimentação """
    PURCHASE = "Compra"
    SALE     = "Venda"
    CONSUME  = "Consumo"


class Movement(BaseModel):
    """ Movimentação normalizada """
    id: int
    item_id: int
    movement_date: date
    quantity: Decimal
    movement_type: MovementType

    model_config = {"from_attributes": True}


class StockMovementRow(BaseModel):
    """ Dado bruto da movimentação sem normalização """
    movement_date: date = Field(..., alias="Data")
    item_id: str = Field(..., alias="ID Item")
    description: str = Field(..., alias="Descrição Item")
    quantity: Decimal = Field(..., gt=0, max_digits=12, decimal_places=3, alias="Quantidade")
    movement_type: MovementType = Field(..., alias="Tipo Movimento")

    model_config = {"populate_by_name": True}
