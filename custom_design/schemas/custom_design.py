from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DesignElement(BaseModel):
    image_id: str
    image_url: str
    image_name: str
    RGB_id: str
    RGB_color: str
    RGB_name: str
    size: int = Field(None, ge=0, le=200)
    opacity: int = Field(None, ge=0, le=100)

class CustomDesignCreate(BaseModel):
    item_name: str
    request_message: Optional[str] = None
    main_image_url: Optional[str] = None

    design_line: Optional[DesignElement] = None
    design_base1: Optional[DesignElement] = None
    design_base2: Optional[DesignElement] = None
    design_pupil: Optional[DesignElement] = None

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

#    user_id: int
#    status: str

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