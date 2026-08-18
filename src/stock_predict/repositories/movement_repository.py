from datetime import date
from sqlalchemy.orm import Session

from stock_predict.models.movement import Movement
from stock_predict.schemas.movement import MovementCreate


class MovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, movement: MovementCreate) -> Movement:
        db_movement = Movement(
            item_id=movement.item_id,
            movement_date=movement.movement_date,
            quantity=movement.quantity,
            movement_type=movement.movement_type,
        )
        self.db.add(db_movement)
        self.db.commit()
        self.db.refresh(db_movement)
        return db_movement

    def bulk_create(self, movements: list[MovementCreate]) -> None:
        db_movements_list = [
            Movement(
                item_id=move.item_id,
                movement_date=move.movement_date,
                quantity=move.quantity,
                movement_type=move.movement_type,
            )
            for move in movements
        ]
        self.db.bulk_save_objects(db_movements_list)
        self.db.commit()

    def get_by_item(
            self,
            item_id: int,
            start_date: date | None = None,
            end_date: date | None = None
    ) -> list[Movement]:
        db_movements_by_item = (
            self.db.query(Movement)
            .filter(Movement.item_id == item_id)
        )
        if start_date:
            db_movements_by_item = db_movements_by_item.filter(
                Movement.movement_date >= start_date
            )
        if end_date:
            db_movements_by_item = db_movements_by_item.filter(
                Movement.movement_date <= end_date
            )

        return db_movements_by_item.order_by(
            Movement.movement_date
        ).all()
