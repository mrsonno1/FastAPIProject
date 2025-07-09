from pydantic import BaseModel
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


class PaginatedPortfolioResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[PortfolioResponse]

