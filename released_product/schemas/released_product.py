# schemas/released_product.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ColorComponentDetail(BaseModel):
    id: int
    color_name: str
    color_values: str

    class Config:
        from_attributes = True

class ReleasedProductCreate(BaseModel):
    design_name: str
    color_name: str
    main_image_url: Optional[str] = None
    brand_id: int
    color_line_color_id: Optional[str] = None
    color_base1_color_id: Optional[str] = None
    color_base2_color_id: Optional[str] = None
    color_pupil_color_id: Optional[str] = None
    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None
    base_curve: Optional[str] = None

class ReleasedProductResponse(ReleasedProductCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReleasedProductApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ReleasedProductResponse] = None

class PaginatedReleasedProductResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ReleasedProductResponse]

class StatusResponse(BaseModel):
    status: str
    message: str

class ReleasedProductDetailResponse(BaseModel):
    id: int
    brand_name: str
    brand_image_url: Optional[str] = None
    design_name: str
    color_name: str
    image: str

    # dk_color, dk_rgb 필드를 아래의 상세 객체 필드로 교체
    color_line_color: Optional[ColorComponentDetail] = None
    color_base1_color: Optional[ColorComponentDetail] = None
    color_base2_color: Optional[ColorComponentDetail] = None
    color_pupil_color: Optional[ColorComponentDetail] = None

    g_dia: Optional[str] = None
    optic: Optional[str] = None
    base_curve: Optional[str] = None

    class Config:
        from_attributes = True




class ColorComponentDetail(BaseModel):
    id: int
    color_name: str
    color_values: str

    class Config:
        from_attributes = True



class ReleasedProductListItem(BaseModel):
    id: int
    brand_name: str
    brand_image_url: Optional[str] = None
    design_name: str
    color_name: str
    image: str
    color_line_color: Optional[ColorComponentDetail] = None
    color_base1_color: Optional[ColorComponentDetail] = None
    color_base2_color: Optional[ColorComponentDetail] = None
    color_pupil_color: Optional[ColorComponentDetail] = None
    graphic_diameter: Optional[str] = None
    optic: Optional[str] = None
    base_curve: Optional[str] = None

    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True




class ReleasedProductListResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ReleasedProductListItem]
