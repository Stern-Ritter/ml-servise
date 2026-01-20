from typing import Optional

from enums import RoleName, Currency
from .base import Entity
from .finance import Balance
from .predict import PredictTask, Predict
from .finance import Transaction


class User(Entity):
    def __init__(self, id: int, login: str, email: str,
                 display_name: str, password_hash: str, role: Role,
                 transactions_history: Optional[list[Transaction]] = None,
                 predictions_history: Optional[list[tuple[PredictTask, Predict]]] = None):
        super().__init__(id)
        self._login = login
        self._email = email
        self._display_name = display_name
        self._password_hash = password_hash
        self._is_active = True
        self._balance = Balance(1, 0.0, Currency.RUB, id)
        self._role = role
        self._transactions_history = transactions_history if transactions_history is not None else []
        self._predictions_history = predictions_history if predictions_history is not None else []

    @property
    def login(self) -> str:
        return self._login

    @property
    def email(self) -> str:
        return self._email

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def balance(self) -> Balance:
        return self._balance

    @property
    def role(self) -> Role:
        return self._role

    def verify_password(self, password_hash: str) -> bool:
        return self._password_hash == password_hash

    def change_password(self, old_password_hash: str, new_password_hash: str) -> bool:
        if self.verify_password(old_password_hash):
            self._password_hash = new_password_hash
            self.update_timestamp()
            return True
        return False

    def add_transaction(self, transaction: Transaction):
        self._transactions_history.append(transaction)
        self.update_timestamp()

    def add_prediction(self, task: PredictTask, predict: Predict):
        self._predictions_history.append((task, predict))
        self.update_timestamp()


class Role(Entity):
    def __init__(self, id: int, name: RoleName):
        super().__init__(id)
        self._name = name

    @property
    def name(self) -> RoleName:
        return self._name

    @name.setter
    def name(self, value: RoleName):
        self._name = value
        self.update_timestamp()
