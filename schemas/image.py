# schemas/image.py
from pydantic import BaseModel, Field # Field 임포트
from datetime import datetime

class ImageResponse(BaseModel):
    id: int
    category: str
    display_name: str = Field(..., min_length=1, description="새로운 표시 이름")
    object_name: str
    public_url: str
    uploaded_at: datetime

    class Config:
        from_attributes = True