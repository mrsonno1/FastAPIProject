# schemas/brand.py
from pydantic import BaseModel, Field
from typing import Optional, List


class RankItem(BaseModel):
    id: int
    rank: int


class RankUpdateBulk(BaseModel):
    ranks: List[RankItem]


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


class PaginatedBrandResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[BrandResponse]  # BrandResponse 객체들의 리스트