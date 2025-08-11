from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 이미지 목록 조회 스키마
class ImageListItem(BaseModel):
    id: int
    category: str
    display_name: str
    object_name: str
    public_url: str
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class PaginatedImageResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ImageListItem]

# 색상 목록 조회 스키마
class ColorListItem(BaseModel):
    id: int
    color_name: str
    color_values: str
    monochrome_type: str
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedColorResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ColorListItem]

# 디자인 컴포넌트 스키마
class DesignComponent(BaseModel):
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    RGB_id: Optional[str] = None
    RGB_color: Optional[str] = None
    RGB_name: Optional[str] = None
    size: Optional[int] = 100
    opacity: Optional[int] = 100

# 커스텀 디자인 상세 조회 응답
class CustomDesignDetailResponse(BaseModel):
    item_name: Optional[str] = None
    account_code: str  # account_code 추가
    design_line: Optional[DesignComponent] = None
    design_base1: Optional[DesignComponent] = None
    design_base2: Optional[DesignComponent] = None
    design_pupil: Optional[DesignComponent] = None
    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None
    dia: Optional[str] = None

# 커스텀 디자인 생성 응답
class CustomDesignCreateResponse(BaseModel):
    id: int
    item_name: Optional[str] = None
    main_image_url: Optional[str] = None

# 커스텀 디자인 목록 아이템
class CustomDesignListItem(BaseModel):
    id: int
    item_name: str
    main_image_url: str
    thumbnail_url: Optional[str] = None
    in_cart: bool  # 카트에 포함되어 있는지 여부
    account_code: str  # account_code 추가
    created_at: datetime  # created_at 추가

    class Config:
        from_attributes = True

# 커스텀 디자인 목록 조회 응답
class PaginatedCustomDesignResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[CustomDesignListItem]