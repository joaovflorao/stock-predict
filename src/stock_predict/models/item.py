from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_predict.database.base import Base

if TYPE_CHECKING:
    from stock_predict.schemas.movement import Movement


class Item(Base):
    __tablename__ = "stock_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    movements: Mapped[list["Movement"]] = relationship(
        back_populates="item",
    )
