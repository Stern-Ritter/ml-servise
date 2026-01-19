from enums import Currency, TransactionType
from .base import Entity


class Balance(Entity):
    def __init__(self, id: int, value: float, currency: Currency, user_id: int):
        super().__init__(id)
        self._value = value
        self._currency = currency
        self._user_id = user_id

    @property
    def value(self) -> float:
        return self._value

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def user_id(self) -> int:
        return self._user_id

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._value += amount
        self.update_timestamp()
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or amount > self._value:
            return False
        self._value -= amount
        self.update_timestamp()
        return True


class Transaction(Entity):
    def __init__(self, id: int, type: TransactionType, amount: float, currency: Currency,
                 description: str, user_id: int):
        super().__init__(id)
        self._type = type
        self._amount = amount
        self._currency = currency
        self._description = description
        self._user_id = user_id

    @property
    def type(self) -> TransactionType:
        return self._type

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    @property
    def description(self) -> str:
        return self._description

    @property
    def user_id(self) -> int:
        return self._user_id
