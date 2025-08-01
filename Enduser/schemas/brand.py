from pydantic import BaseModel
from typing import List, Optional


# 브랜드 아이템
class BrandListItem(BaseModel):
    brand_name: str  # 브랜드 이름
    brand_image_url: Optional[str] = None  # 브랜드 이미지 URL

    class Config:
        from_attributes = True


# 브랜드 목록 응답
class PaginatedBrandResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[BrandListItem]