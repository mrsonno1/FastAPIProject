# schemas/brand.py
from pydantic import BaseModel, Field
from typing import Optional, List



# API 응답을 위한 스키마
class BrandResponse(BaseModel):
    id: int
    brand_name: str
    brand_image_url: Optional[str] = None
    rank: int

    class Config:
        from_attributes = True

# 순위 변경을 위한 입력 스키마
class RankUpdate(BaseModel):
    action: str = Field(..., description="순위 변경 동작 (up, down, top, bottom)")