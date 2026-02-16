from pydantic import BaseModel
from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .base import BaseEntity
from .enums import Gender, PredictStatus

if TYPE_CHECKING:
    from .user import User


class Patient(BaseEntity):
    __tablename__ = "patients"

    age = Column(Float, nullable=False)
    gender = Column(SQLAlchemyEnum(Gender), nullable=False)
    physical_activity_days_per_week = Column(Integer, nullable=False)
    stress_level = Column(Integer, nullable=False)
    bmi = Column(Float, nullable=False)
    exercise_hours_per_week = Column(Float, nullable=False)
    sedentary_hours_per_day = Column(Float, nullable=False)
    sleep_hours_per_day = Column(Float, nullable=False)
    heart_rate = Column(Float, nullable=False)
    cholesterol = Column(Float, nullable=False)
    blood_sugar = Column(Float, nullable=False)
    triglycerides = Column(Float, nullable=False)
    smoking = Column(Boolean, default=False)
    alcohol_consumption = Column(Boolean, default=False)
    diabetes = Column(Boolean, default=False)
    obesity = Column(Boolean, default=False)
    family_history = Column(Boolean, default=False)

    predict_tasks: Mapped[list["PredictTask"]] = relationship(
        "PredictTask",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "gender": self.gender,
            "physical_activity_days_per_week": self.physical_activity_days_per_week,
            "stress_level": self.stress_level,
            "bmi": self.bmi,
            "exercise_hours_per_week": self.exercise_hours_per_week,
            "sedentary_hours_per_day": self.sedentary_hours_per_day,
            "sleep_hours_per_day": self.sleep_hours_per_day,
            "heart_rate": self.heart_rate,
            "cholesterol": self.cholesterol,
            "blood_sugar": self.blood_sugar,
            "triglycerides": self.triglycerides,
            "smoking": self.smoking,
            "alcohol_consumption": self.alcohol_consumption,
            "diabetes": self.diabetes,
            "obesity": self.obesity,
            "family_history": self.family_history
        }


class PredictTask(BaseEntity):
    __tablename__ = "predict_tasks"

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)
    status = Column(SQLAlchemyEnum(PredictStatus),
                    default=PredictStatus.PENDING, nullable=False)
    cost = Column(Float, default=0.0)

    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="predict_tasks")
    user: Mapped["User"] = relationship(
        "User", back_populates="predict_tasks")
    predict: Mapped[Optional["Predict"]] = relationship(
        "Predict",
        uselist=False,
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def start_processing(self, cost: float):
        self.status = PredictStatus.PROCESSING
        self.cost = cost
        self.update_timestamp()


class Predict(BaseEntity):
    __tablename__ = "predicts"

    prediction = Column(Boolean, nullable=False)
    probability = Column(Float, nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey(
        "predict_tasks.id"), unique=True, nullable=False)

    task: Mapped["PredictTask"] = relationship(
        "PredictTask", back_populates="predict")


class PatientCreate(BaseModel):
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
    smoking: bool = False
    alcohol_consumption: bool = False
    diabetes: bool = False
    obesity: bool = False
    family_history: bool = False


class PatientUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[Gender] = None
    physical_activity_days_per_week: Optional[int] = None
    stress_level: Optional[int] = None
    bmi: Optional[float] = None
    exercise_hours_per_week: Optional[float] = None
    sedentary_hours_per_day: Optional[float] = None
    sleep_hours_per_day: Optional[float] = None
    heart_rate: Optional[float] = None
    cholesterol: Optional[float] = None
    blood_sugar: Optional[float] = None
    triglycerides: Optional[float] = None
    smoking: Optional[bool] = None
    alcohol_consumption: Optional[bool] = None
    diabetes: Optional[bool] = None
    obesity: Optional[bool] = None
    family_history: Optional[bool] = None


class PredictTaskCreate(BaseModel):
    patient_id: int
    user_id: int


class PredictTaskFilter(BaseModel):
    status: Optional[PredictStatus] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
