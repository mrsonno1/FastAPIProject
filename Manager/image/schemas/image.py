# schemas/image.py
from pydantic import BaseModel, Field # Field 임포트
from datetime import datetime
from typing import List, Optional

class ImageResponse(BaseModel):
    id: int
    category: str
    display_name: str = Field(..., min_length=1, description="새로운 표시 이름")
    object_name: str
    public_url: str
    uploaded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedImageResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ImageResponse]


class ImageInfoResponse(BaseModel):
    id: int
    image_url: str
    item_name: str
    exposed_users: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True