from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class PurchaseSuggestion(BaseModel):
    """ Sugestão de reposição de estoque """
    item_id: int
    suggested_quantity: Decimal = Field(..., ge=0)
    reorder_point: Decimal = Field(..., ge=0)
    reference_date: date

    model_config = {"from_attributes": True}
