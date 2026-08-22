from sqlalchemy import or_
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

    def get_by_external_ids(self, external_ids: list[str]) -> list[Item]:
        return (
            self.db.query(Item)
            .filter(Item.external_id.in_(external_ids))
            .all()
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

    def bulk_create(self, items: list[ItemCreate]) -> list[Item]:
        db_items = [
            Item(external_id=item.external_id, description=item.description)
            for item in items
        ]
        self.db.bulk_save_objects(db_items, return_defaults=True)
        self.db.commit()
        return db_items

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

    def search(self, query: str, limit: int = 30) -> list[Item]:
        q = self.db.query(Item).order_by(Item.id)
        if query:
            pattern = f"%{query}%"
            q = q.filter(
                or_(
                    Item.external_id.ilike(pattern),
                    Item.description.ilike(pattern),
                )
            )
        return q.limit(limit).all()
