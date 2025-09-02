from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 디자인 컴포넌트 정보
class DesignComponent(BaseModel):
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    RGB_id: Optional[str] = None
    RGB_color: Optional[str] = None
    RGB_name: Optional[str] = None
    size: Optional[int] = 100
    opacity: Optional[int] = 100


# 출시 제품 목록 아이템
class ReleasedProductListItem(BaseModel):
    id: int  # 출시제품 ID
    item_name: str  # 디자인 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    thumbnail_url: Optional[str] = None  # 썸네일 URL
    brand_name: str  # 브랜드 이름
    realtime_users: int = 0  # 실시간 유저수

    class Config:
        from_attributes = True


# 출시 제품 목록 응답
class PaginatedReleasedProductResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ReleasedProductListItem]


# 출시 제품 상세 정보 응답
class ReleasedProductDetailResponse(BaseModel):
    id: int  # 출시제품 ID
    item_name: str  # 디자인 이름
    color_name: Optional[str] = None  # 디자인 컬러 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    design_line: Optional[DesignComponent] = None  # 라인 디자인 정보
    design_base1: Optional[DesignComponent] = None  # 바탕1 디자인 정보
    design_base2: Optional[DesignComponent] = None  # 바탕2 디자인 정보
    design_pupil: Optional[DesignComponent] = None  # 동공 디자인 정보
    graphic_diameter: Optional[str] = None  # 그래픽 직경
    optic_zone: Optional[str] = None  # 옵틱존
    base_curve: Optional[str] = None  # 베이스커브
    dia: Optional[str] = None  # DIA
    brand_name: str  # 브랜드 이름
    realtime_users: int = 0  # 실시간 유저수


# 실시간 유저수 응답
class RealtimeUsersResponse(BaseModel):
    item_name: str  # 디자인 이름
    realtime_users: int  # 실시간 유저수