from sqlalchemy.orm import Session

from stock_predict.repositories.item_repository import ItemRepository
from stock_predict.repositories.movement_repository import MovementRepository
from stock_predict.schemas.movement import StockMovementRow, MovementCreate


def ingest_movement(raw_rows: list[StockMovementRow], db: Session) -> None:
    item_repo = ItemRepository(db)
    movement_repo = MovementRepository(db)

    movements_list = []
    for row in raw_rows:
        obj_item = item_repo.get_or_create(
            external_id=row.item_id,
            description=row.description,
        )
        obj_move = MovementCreate(
            item_id=obj_item.id,
            movement_date=row.movement_date,
            quantity=row.quantity,
            movement_type=row.movement_type,
        )
        movements_list.append(obj_move)

    movement_repo.bulk_create(movements_list)
