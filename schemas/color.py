# schemas/color.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# 기본 필드를 포함하는 Base 스키마
class ColorBase(BaseModel):
    color_values: str = Field(..., description="쉼표로 구분된 컬러 값 (R,G,B,C,M,Y,K)")
    monochrome_type: str = Field(..., description="흑백 타입 (예: 흑, 백)")
# 생성을 위한 스키마
class ColorCreate(ColorBase):
    color_name: str = Field(..., min_length=1)

# 수정을 위한 스키마
class ColorUpdate(ColorBase):
    pass

# API 응답을 위한 스키마
class ColorResponse(ColorBase):
    id: int
    color_name: str
    monochrome_type: str
    updated_at: datetime

    class Config:
        from_attributes = True

# 중복 확인 응답을 위한 스키마
class NameCheckResponse(BaseModel):
    exists: bool