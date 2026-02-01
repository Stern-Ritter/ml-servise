from .base import BaseMLModel


class MLModel(BaseMLModel):
    def __init__(self, name: str, version: str):
        self._name = name
        self._version = version

    def predict(self, data: dict) -> dict:
        pass

    def get_model_info(self) -> dict:
        return {
            "name": self._name,
            "version": self._version,
        }
