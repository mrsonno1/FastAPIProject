from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# 새로운 디자인 요소 포맷
class DesignComponents(BaseModel):
    라인: Optional[str] = None
    바탕1: Optional[str] = None
    바탕2: Optional[str] = None
    동공: Optional[str] = None

# 직경 정보 포맷
class DiameterInfo(BaseModel):
    G_DIA: Optional[str] = None
    Optic: Optional[str] = None

# 단일 포트폴리오 상세 정보를 위한 스키마
class PortfolioDetailItem(BaseModel):
    designName: Optional[str] = None
    colorName: Optional[str] = None
    country: Optional[str] = None
    fixed: Optional[str] = None
    image: Optional[str] = None
    design: Optional[DesignComponents] = None
    designimage: Optional[List[str]] = None
    dkColor: Optional[List[str]] = None
    dkrgb: Optional[List[str]] = None
    G_DIA: Optional[str] = None
    Optic: Optional[str] = None

# 단일 포트폴리오 응답을 위한 스키마
class PortfolioDetailResponse(BaseModel):
    success: bool = True
    message: str = "포트폴리오 정보를 성공적으로 조회했습니다."
    data: Optional[PortfolioDetailItem] = None

# 포트폴리오 응답을 위한 새로운 포맷 스키마
class PortfolioListItem(BaseModel):
    no: int
    image: Optional[str] = None
    designName: Optional[str] = None
    colorName: Optional[str] = None
    design: Optional[DesignComponents] = None
    dkColor: Optional[List[str]] = None
    dkrgb: Optional[List[str]] = None
    diameter: Optional[DiameterInfo] = None
    country: Optional[str] = None
    fixed: Optional[str] = None
    viewCount: Optional[int] = 0
    registerDate: Optional[str] = None

# 페이지네이션된 응답 포맷
class PaginatedPortfolioFormatResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[PortfolioListItem]
