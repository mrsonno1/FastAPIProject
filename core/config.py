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

    # ▼▼▼▼▼ 모든 MinIO 필드를 선택사항으로 변경합니다 ▼▼▼▼▼
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET_NAME: Optional[str] = None
    MINIO_USE_SECURE: Optional[bool] = None

    class Config:
        env_file = ".env"

settings = Settings()