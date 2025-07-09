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
    brandname: str
    brandimage: Optional[str] = None
    designName: str
    colorName: str
    image: str
    dkColor: List[str] = Field(default_factory=list)
    dkrgb: List[str] = Field(default_factory=list)
    G_DIA: Optional[str] = None
    Optic: Optional[str] = None
    baseCurve: Optional[str] = None

class ReleasedProductListItem(BaseModel):
    no: int
    brandname: str
    image: str
    designName: str
    colorName: str
    dkColor: List[str] = Field(default_factory=list)
    dkrgb: List[str] = Field(default_factory=list)
    diameter: dict = Field(default_factory=dict)
    viewCount: int = 0
    registerDate: str

class ReleasedProductListResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ReleasedProductListItem]
