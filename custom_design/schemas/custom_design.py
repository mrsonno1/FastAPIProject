from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CustomDesignCreate(BaseModel):
    item_name: Optional[str] = None
    request_message: Optional[str] = None
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

# 상태(status) 수정을 위한 스키마
class CustomDesignStatusUpdate(BaseModel):
    status: str

# API 응답을 위한 스키마
class CustomDesignResponse(CustomDesignCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


    class Config:
        from_attributes = True

class CustomDesignApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[CustomDesignResponse] = None


# ▼▼▼ CustomDesignResponse 수정 (user_id, status 추가) ▼▼▼
class CustomDesignResponse2(CustomDesignCreate):
    id: int
    user_id: int  # 필드 추가
    status: str  # 필드 추가
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ▼▼▼ 페이지네이션 응답을 위한 새 스키마 추가 ▼▼▼
class PaginatedCustomDesignResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[CustomDesignResponse2]

    class Config:
        from_attributes = True