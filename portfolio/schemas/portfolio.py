from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 포트폴리오 생성을 위한 스키마
class PortfolioCreate(BaseModel):
    design_name: str
    color_name: str
    exposed_countries: str = ""  # 콤마로 구분된 국가 ID들 (예: "1,2,3,4")
    is_fixed_axis: str = "N"  # Y 또는 N
    main_image_url: Optional[str] = None

    design_line_image_id: Optional[str] = None
    design_line_color_id: Optional[str] = None

    design_base1_image_id: Optional[str] = None
    design_base1_color_id: Optional[str] = None

    design_base2_image_id: Optional[str] = None
    design_base2_color_id: Optional[str] = None

    design_pupil_image_id: Optional[str] = None
    design_pupil_color_id: Optional[str] = None

    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None


# API 응답을 위한 스키마
class PortfolioResponse(PortfolioCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PortfolioResponse] = None


class StatusResponse(BaseModel):
    status: str
    message: str


class DkComponentDict(BaseModel):
    line: Optional[str] = None
    base1: Optional[str] = None
    base2: Optional[str] = None
    pupil: Optional[str] = None

class DiameterInfo(BaseModel):
    G_DIA: Optional[str] = None
    Optic: Optional[str] = None

class PortfolioListItem(BaseModel):
    id: int
    user_name: str
    main_image_url: Optional[str] = None
    design_name: Optional[str] = None
    color_name: Optional[str] = None

    design: DkComponentDict
    dkColor: DkComponentDict
    dkrgb: DkComponentDict

    diameter: DiameterInfo
    country_name: str
    is_fixed_axis: str # 스키마 필드명은 is_fixed_axis가 더 적절합니다.
    viewCount: int
    created_at: datetime

    class Config:
        from_attributes = True # ORM 모델과 매핑을 위해 필요


# 페이지네이션 응답 스키마
class PaginatedPortfolioListResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[PortfolioListItem]

class PaginatedPortfolioResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[PortfolioResponse]

