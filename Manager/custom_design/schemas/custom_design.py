# Manager/custom_design/schemas/custom_design.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CustomDesignCreate(BaseModel):
    item_name: Optional[str] = None
    status: Optional[str] = None
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

    line_transparency: Optional[str] = None
    base1_transparency: Optional[str] = None
    base2_transparency: Optional[str] = None
    pupil_transparency: Optional[str] = None

    # 새로 추가되는 size 필드들
    line_size: Optional[str] = None
    base1_size: Optional[str] = None
    base2_size: Optional[str] = None
    pupil_size: Optional[str] = None

    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None

# 상태(status) 수정을 위한 스키마
class CustomDesignStatusUpdate(BaseModel):
    status: str


class DesignComponentDetail(BaseModel):
    id: Optional[int] = None
    display_name: Optional[str] = None
    public_url: Optional[str] = None
    opacity: Optional[int] = None  # opacity 필드 추가
    size: Optional[int] = None  # size 필드 추가


class ColorComponentDetail(BaseModel):
    id: Optional[int] = None
    color_name: Optional[str] = None
    color_values: Optional[str] = None


class CustomDesignDetailResponse(BaseModel):
    id: int

    user_name: str
    account_code: str  # account_code 추가

    item_name: str
    status: str
    request_message: Optional[str] = None
    main_image_url: Optional[str] = None

    design_line: Optional[DesignComponentDetail] = None
    design_line_color: Optional[ColorComponentDetail] = None

    design_base1: Optional[DesignComponentDetail] = None
    design_base1_color: Optional[ColorComponentDetail] = None

    design_base2: Optional[DesignComponentDetail] = None
    design_base2_color: Optional[ColorComponentDetail] = None

    design_pupil: Optional[DesignComponentDetail] = None
    design_pupil_color: Optional[ColorComponentDetail] = None

    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True



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
    user_id: str  # 필드 추가
    status: str  # 필드 추가
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 새로운 목록 아이템 스키마 정의
class CustomDesignListItem(BaseModel):
    id: int
    user_name: str  # account 테이블의 contact_name 또는 username
    account_code: str  # AdminUser의 account_code 추가
    main_image_url: Optional[str] = None
    item_name: str
    user_id: str  # custom_designs 테이블의 user_id (생성자 아이디)
    created_at: datetime
    status: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 페이지네이션 응답 스키마가 새로운 아이템 스키마를 사용하도록 변경 ---
class PaginatedCustomDesignResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[CustomDesignListItem]  # CustomDesignResponse2 -> CustomDesignListItem

    class Config:
        from_attributes = True