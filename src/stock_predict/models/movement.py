from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, Date, Enum, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_predict.database.base import Base
from stock_predict.schemas.movement import MovementType

if TYPE_CHECKING:
    from stock_predict.models.item import Item



class Movement(Base):
    __tablename__ = "stock_movement"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stock_item.id"),
        nullable=False,
        index=True,
    )
    movement_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )
    movement_type: Mapped[MovementType] = mapped_column(
        Enum(MovementType),
        nullable=False,
    )

    item: Mapped["Item"] = relationship(
        back_populates="movements",
    )
