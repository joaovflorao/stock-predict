from sqlalchemy.orm import Session

from stock_predict.repositories.item_repository import ItemRepository
from stock_predict.repositories.movement_repository import MovementRepository
from stock_predict.schemas.item import ItemCreate
from stock_predict.schemas.movement import StockMovementRow, MovementCreate


def ingest_movement(raw_rows: list[StockMovementRow], db: Session) -> None:
    item_repo = ItemRepository(db)
    movement_repo = MovementRepository(db)

    unique_items = {}
    for row in raw_rows:
        unique_items.setdefault(row.item_id, row.description)

    external_ids = list(unique_items.keys())
    existing_items = item_repo.get_by_external_ids(external_ids)

    items_by_external_ids = {item.external_id: item.id for item in existing_items}
    missing_external_ids = [
        ext_id for ext_id in external_ids
        if ext_id not in items_by_external_ids
    ]
    if missing_external_ids:
        new_items = [
            ItemCreate(external_id=ext_id, description=unique_items[ext_id])
            for ext_id in missing_external_ids
        ]
        created_items = item_repo.bulk_create(new_items)
        items_by_external_ids.update(
            {item.external_id: item.id for item in created_items}
        )

    movements_list = [
        MovementCreate(
            item_id=items_by_external_ids[row.item_id],
            movement_date=row.movement_date,
            quantity=row.quantity,
            movement_type=row.movement_type,
        )
        for row in raw_rows
    ]
    movement_repo.bulk_create(movements_list)
