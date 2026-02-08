from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, Optional

from .base import BaseEntity
from .enums import Gender, PredictStatus

if TYPE_CHECKING:
    from .user import User


class Patient(BaseEntity):
    __tablename__ = "patients"

    age = Column(Integer, nullable=False)
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
