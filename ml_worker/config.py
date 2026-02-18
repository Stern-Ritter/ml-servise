from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None

    RABBITMQ_HOST: Optional[str] = None
    RABBITMQ_PORT: Optional[int] = None
    RABBITMQ_USER: Optional[str] = None
    RABBITMQ_PASSWORD: Optional[str] = None
    QUEUE_NAME: Optional[str] = None

    APP_NAME: Optional[str] = None
    API_VERSION: Optional[str] = None
    DEBUG: Optional[bool] = None

    MODEL_PATH: str = './model/heart_attack_model.pkl'
    MODEL_PREPROCESSING_PIPELINE_PATH: str = './model/preprocessing_pipeline.pkl'
    MODEL_REQUIRED_FEATURES_PATH: str = './model/feature_names.pkl'
    MODEL_OPTIMAL_THRESHOLD_PATH: str = './model/optimal_threshold.pkl'

    DEFAULT_THRESHOLD: float = 0.50

    @property
    def DATABASE_URL_psycopg(self):
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def validate(self) -> None:
        if not all([
            self.DB_HOST,
            self.DB_USER,
            self.DB_PASSWORD,
            self.DB_NAME,
            self.RABBITMQ_HOST,
            self.RABBITMQ_PORT,
            self.RABBITMQ_USER,
            self.RABBITMQ_PASSWORD,
            self.QUEUE_NAME
        ]):
            raise ValueError("Missing required configuration")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
