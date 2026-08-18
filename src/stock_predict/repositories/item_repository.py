from sqlalchemy.orm import Session

from stock_predict.models.item import Item
from stock_predict.schemas.item import ItemCreate


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self) -> Item | None:
        raise NotImplementedError

    def create(self, item: ItemCreate) -> Item:
        raise NotImplementedError

    def get_or_create(self, external_id: str, description: str) -> Item:
        raise NotImplementedError

    def list_all(self) -> list[Item]:
        raise NotImplementedError
