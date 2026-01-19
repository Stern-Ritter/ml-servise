from dataclasses import dataclass

from enums import Gender, PredictStatus
from .base import Entity


@dataclass
class Patient:
    id: int
    age: int
    gender: Gender
    physical_activity_days_per_week: int
    stress_level: int
    bmi: float
    exercise_hours_per_week: float
    sedentary_hours_per_day: float
    sleep_hours_per_day: float
    heart_rate: float
    cholesterol: float
    blood_sugar: float
    triglycerides: float
    smoking: bool
    alcohol_consumption: bool
    diabetes: bool
    obesity: bool
    family_history: bool


class PredictTask(Entity):
    def __init__(self, id: int, patient: Patient, user_id: int):
        super().__init__(id)
        self._patient = patient
        self._user_id = user_id
        self._status = PredictStatus.PENDING
        self._cost: float = 0.0

    @property
    def patient(self) -> Patient:
        return self._patient

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def status(self) -> PredictStatus:
        return self._status

    @status.setter
    def status(self, value: PredictStatus):
        self._status = value
        self.update_timestamp()

    def start_processing(self, cost: float):
        self._status = PredictStatus.PROCESSING
        self._cost = cost
        self.update_timestamp()


class Predict(Entity):
    def __init__(self, id: int, prediction: bool, probability: float):
        super().__init__(id)
        self._prediction = prediction
        self._probability = probability

    @property
    def prediction(self) -> bool:
        return self._prediction

    @property
    def probability(self) -> float:
        return self._probability
