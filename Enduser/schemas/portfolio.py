from pydantic import BaseModel
from typing import Optional, List
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


# 포트폴리오 목록 아이템
class PortfolioListItem(BaseModel):
    id: int  # 포트폴리오 ID
    item_name: str  # 디자인 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    thumbnail_url: Optional[str] = None  # 썸네일 URL
    realtime_users: int = 0  # 실시간 유저수 (인기순 정렬시 사용)
    created_at: datetime  # 생성일시 (최신순 정렬시 사용)
    account_code: str  # account_code 추가
    in_cart: bool = False  # 장바구니에 포함 여부

    class Config:
        from_attributes = True


# 포트폴리오 목록 응답
class PaginatedPortfolioResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[PortfolioListItem]


# 포트폴리오 상세 조회 응답
class PortfolioDetailResponse(BaseModel):
    item_name: str  # 디자인 이름
    color_name: str  # 디자인 컬러 이름
    account_code: str  # account_code 추가
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    design_line: Optional[DesignComponent] = None  # 라인 디자인 정보
    design_base1: Optional[DesignComponent] = None  # 바탕1 디자인 정보
    design_base2: Optional[DesignComponent] = None  # 바탕2 디자인 정보
    design_pupil: Optional[DesignComponent] = None  # 동공 디자인 정보
    graphic_diameter: Optional[str] = None  # 그래픽 직경
    optic_zone: Optional[str] = None  # 옵틱존
    dia: Optional[str] = None  # DIA


# 실시간 유저수 응답
class RealtimeUsersResponse(BaseModel):
    item_name: str  # 디자인 이름
    realtime_users: int  # 실시간 유저수