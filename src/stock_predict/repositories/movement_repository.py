from datetime import date
from sqlalchemy.orm import Session

from stock_predict.models.item import Movement
from stock_predict.schemas.movement import MovementCreate


class MovementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, movement: MovementCreate) -> Movement:
        raise NotImplementedError

    def bulk_create(self, movements: list[Movement]) -> None:
        raise NotImplementedError

    def get_by_item(self, item_id: int, start_date: date = None, end_date: date = None) -> list[Movement]:
        raise NotImplementedError
