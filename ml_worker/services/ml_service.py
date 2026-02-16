from typing import Dict, Any


class MLService():
    def __init__(self, model, preprocessing_pipeline,
                 required_features, threshold=0.5):
        self.model = model
        self.preprocessing_pipeline = preprocessing_pipeline
        self.required_features = required_features
        self.threshold = threshold

    def predict(self, data) -> Dict[str, Any]:
        probas = self.model.predict_proba(data)[:, 1]
        proba = probas[0]
        prediction = (proba >= self.threshold).astype(int)

        return {
            "prediction": bool(prediction),
            "probability": float(proba)
        }
