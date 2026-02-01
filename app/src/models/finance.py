from sqlalchemy import Column, Float, String, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING

from .base import BaseEntity
from .enums import Currency, TransactionType

if TYPE_CHECKING:
    from .user import User


class Balance(BaseEntity):
    __tablename__ = "balances"

    value = Column(Float, default=0.0, nullable=False)
    currency = Column(SQLAlchemyEnum(Currency),
                      nullable=False, default=Currency.RUB)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="balance")

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self.value += amount
        self.update_timestamp()
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or amount > self.value:
            return False
        self.value -= amount
        self.update_timestamp()
        return True


class Transaction(BaseEntity):
    __tablename__ = "transactions"

    type = Column(SQLAlchemyEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(SQLAlchemyEnum(Currency), nullable=False)
    description = Column(String(256))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
