# schemas/released_product.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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

class ReleasedProductCreate(BaseModel):
    design_name: str
    color_name: str
    main_image_url: Optional[str] = None
    brand: Dict[str, Any] = {}
    color_line: Optional[DesignElement] = None
    color_base1: Optional[DesignElement] = None
    color_base2: Optional[DesignElement] = None
    color_pupil: Optional[DesignElement] = None

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
