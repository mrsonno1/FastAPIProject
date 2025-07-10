# schemas/released_product.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime



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
    dk_color: List[str] = Field(default_factory=list)
    dk_rgb: List[str] = Field(default_factory=list)
    g_dia: Optional[str] = None
    optic: Optional[str] = None
    base_curve: Optional[str] = None

class ReleasedProductListItem(BaseModel):
    id: int
    brand_name: str
    brand_image_url: Optional[str] = None
    design_name: str
    color_name: str
    dkColor: List[str] # dkColor -> dk_color
    dkrgb: List[str]   # dkrgb -> dk_rgb
    G_DIA: Optional[str] = None
    Optic: Optional[str] = None
    base_curve: Optional[str] = None
    view_count: int # viewCount -> view_count
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
