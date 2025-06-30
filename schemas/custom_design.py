from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DesignElement(BaseModel):
    image_url: Optional[str] = None
    color_code: Optional[str] = None
    percentage: Optional[int] = Field(None, ge=0, le=100)

class CustomDesignCreate(BaseModel):
    user_id: str
    code_name: str
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
class CustomDesignResponse(BaseModel):
    id: int
    user_id: str
    code_name: str
    status: str
    request_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    main_image_url: Optional[str] = None
    design_line: Optional[DesignElement] = None
    design_base1: Optional[DesignElement] = None
    design_base2: Optional[DesignElement] = None
    design_pupil: Optional[DesignElement] = None
    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None

    class Config:
        from_attributes = True