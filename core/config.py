# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # ▼▼▼▼▼ 환경 분기를 위한 변수 추가 ▼▼▼▼▼
    APP_ENV: str = "local"  # 기본값은 local

    # ▼▼▼▼▼ S3 설정을 위한 변수 추가 ▼▼▼▼▼
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_S3_REGION: Optional[str] = None

    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str
    MINIO_USE_SECURE: bool

    class Config:
        env_file = ".env"

settings = Settings()