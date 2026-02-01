from abc import ABC, abstractmethod
from datetime import datetime


class Entity(ABC):
    def __init__(self, id: int):
        self._id = id
        self._created_at = datetime.now()
        self._updated_at = datetime.now()

    @property
    def id(self) -> int:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update_timestamp(self):
        self._updated_at = datetime.now()

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        attributes = []

        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                continue
            if attr_name.startswith('_') and not attr_name.startswith('__'):
                clean_name = attr_name[1:]
                try:
                    value = getattr(self, attr_name)
                    attributes.append(f"{clean_name}={value!r}")
                except AttributeError:
                    continue

        return f"{class_name}({', '.join(attributes)})"


class BaseMLModel(ABC):
    @abstractmethod
    def predict(self, data: dict) -> dict:
        pass
