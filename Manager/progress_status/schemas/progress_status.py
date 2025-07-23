# progress_status/schemas/progress_status.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# 진행 상태 기본 스키마
class ProgressStatusBase(BaseModel):
    user_id: int
    custom_design_id: Optional[int] = None
    portfolio_id: Optional[int] = None
    status: str = Field(..., description="진행 상태 (0: 대기, 1: 진행중, 2: 지연, 3: 배송완료)")
    notes: Optional[str] = None
    client_name: Optional[str] = None
    number: Optional[str] = None
    address: Optional[str] = None
    status_note: Optional[str] = None
    expected_shipping_date: Optional[date] = None


# 진행 상태 생성용 스키마
class ProgressStatusCreate(ProgressStatusBase):
    pass


# 진행 상태 수정용 스키마
class ProgressStatusUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    status_note: Optional[str] = None
    expected_shipping_date: Optional[date] = None


# API 응답을 위한 기본 스키마
class ProgressStatusResponse(ProgressStatusBase):
    id: int
    request_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 이미지 및 컬러 컴포넌트 상세 정보
class ImageComponentDetail(BaseModel):
    id: Optional[int] = None
    display_name: Optional[str] = None
    public_url: Optional[str] = None
    opacity: Optional[int] = None

    class Config:
        from_attributes = True


class ColorComponentDetail(BaseModel):
    id: Optional[int] = None
    color_name: Optional[str] = None
    color_values: Optional[str] = None

    class Config:
        from_attributes = True


# 목록 조회용 아이템 스키마 (조인된 데이터 포함)
class ProgressStatusListItem(BaseModel):
    id: int
    user_name: str  # AdminUser의 contact_name 또는 username
    account_code: str  # AdminUser의 account_code 추가
    image_url: Optional[str] = None  # main_image_url
    type: int  # 0=custom_design, 1=portfolio
    type_id: int  # custom_design id 또는 portfolio id
    type_name: str  # custom_design의 item_name 또는 portfolio의 design_name

    # 디자인 컴포넌트 정보
    design_line: Optional[ImageComponentDetail] = None
    design_line_color: Optional[ColorComponentDetail] = None
    design_base1: Optional[ImageComponentDetail] = None
    design_base1_color: Optional[ColorComponentDetail] = None
    design_base2: Optional[ImageComponentDetail] = None
    design_base2_color: Optional[ColorComponentDetail] = None
    design_pupil: Optional[ImageComponentDetail] = None
    design_pupil_color: Optional[ColorComponentDetail] = None

    status: str
    notes: Optional[str] = None
    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None
    dia: Optional[str] = None
    expected_shipping_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 상세 조회용 스키마
class ProgressStatusDetailResponse(BaseModel):
    id: int
    user_name: str
    account_code: str  # account_code 추가
    type: int  # 0=custom_design, 1=portfolio
    type_id: int
    status: str
    notes: Optional[str] = None
    type_name: str
    client_name: Optional[str] = None
    number: Optional[str] = None
    address: Optional[str] = None
    status_note: Optional[str] = None
    image_url: Optional[str] = None

    # 디자인 컴포넌트 정보
    design_line: Optional[ImageComponentDetail] = None
    design_line_color: Optional[ColorComponentDetail] = None
    design_base1: Optional[ImageComponentDetail] = None
    design_base1_color: Optional[ColorComponentDetail] = None
    design_base2: Optional[ImageComponentDetail] = None
    design_base2_color: Optional[ColorComponentDetail] = None
    design_pupil: Optional[ImageComponentDetail] = None
    design_pupil_color: Optional[ColorComponentDetail] = None

    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None
    dia: Optional[str] = None

    request_date: datetime
    expected_shipping_date: Optional[date] = None
    changelog: Optional[str] = None  # 변경 이력

    class Config:
        from_attributes = True


# 페이지네이션 응답 스키마
class PaginatedProgressStatusResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ProgressStatusListItem]


# API 응답 래퍼 스키마
class ProgressStatusApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ProgressStatusResponse] = None


# 상태 응답 스키마 (삭제 등에 사용)
class StatusResponse(BaseModel):
    status: str
    message: str