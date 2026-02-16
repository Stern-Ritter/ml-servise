from typing import Dict, Any


class MLService():
    def __init__(self, model_path: str = None):
        self.model = None
        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str):
        pass

    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "prediction": True,
            "probability": 1.0
        }
