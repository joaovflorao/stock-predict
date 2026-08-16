from pydantic import BaseModel


class Item(BaseModel):
    """ Item de estoque normalizado """
    id: int
    external_id: str
    description: str

    model_config = {"from_attributes": True}


class ItemCreate(BaseModel):
    external_id: str
    description: str
