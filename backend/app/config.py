from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]   # carpeta backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    secret_key: str
    access_token_minutes: int = 480
    model_path: str = "../ml/models/modelo_transmind_severidad.pkl"
    label_encoder_path: str = "../ml/models/label_encoder.pkl"
    features_path: str = "../ml/models/features.json"  # opcional
    model_version: str = "v1.0"
    allow_demo_model: bool = False  # solo para probar la interfaz sin modelo
    device_api_key: str
    cors_origins: str = "http://localhost:5173"


settings = Settings()
