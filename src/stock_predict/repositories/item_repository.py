from sqlalchemy.orm import Session

from stock_predict.models.item import Item
from stock_predict.schemas.item import ItemCreate


class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: str) -> Item | None:
        return (
            self.db.query(Item)
            .filter(Item.external_id == external_id)
            .first()
        )

    def create(self, item: ItemCreate) -> Item:
        db_item = Item(
            external_id=item.external_id,
            description=item.description,
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def get_or_create(self, external_id: str, description: str) -> Item:
        existing_item = self.get_by_external_id(external_id)
        if existing_item:
            return existing_item

        return self.create(
            ItemCreate(
                external_id=external_id,
                description=description,
            )
        )

    def list_all(self) -> list[Item]:
        return self.db.query(Item).all()
