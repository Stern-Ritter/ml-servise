
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseMLModel(ABC):
    @abstractmethod
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass


class MLModel(BaseMLModel):
    def __init__(self, name: str, version: str):
        self._name = name
        self._version = version

    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "version": self._version,
        }
