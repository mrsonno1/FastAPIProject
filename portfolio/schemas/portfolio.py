from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from custom_design.schemas.custom_design import DesignElement

# 포트폴리오 생성을 위한 스키마
class PortfolioCreate(BaseModel):
    design_name: str
    color_name: str
    exposed_countries:  Dict[str, Any] = {}  # 국가 이름 리스트로 받음
    is_fixed_axis: bool = False
    main_image_url: Optional[str] = None

    design_line: Optional[DesignElement] = None
    design_base1: Optional[DesignElement] = None
    design_base2: Optional[DesignElement] = None
    design_pupil: Optional[DesignElement] = None

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

