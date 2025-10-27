# schemas/color.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 생성을 위한 스키마 - 완전히 새로 정의
class ColorCreate(BaseModel):
    color_name: Optional[str] = Field(default="", min_length=0, description="컬러 이름 (빈 문자열 허용)")
    color_values: Optional[str] = Field(default=None, description="쉼표로 구분된 컬러 값 (R,G,B,C,M,Y,K) - 선택사항")
    monochrome_type: str = Field(..., description="흑백 타입 (예: 흑, 백)")

# 기본 필드를 포함하는 Base 스키마
class ColorBase(BaseModel):
    color_values: str = Field(..., description="쉼표로 구분된 컬러 값 (R,G,B,C,M,Y,K)")
    monochrome_type: str = Field(..., description="흑백 타입 (예: 흑, 백)")

# 수정을 위한 스키마
class ColorUpdate(BaseModel):
    color_values: Optional[str] = Field(default=None, description="쉼표로 구분된 컬러 값 (R,G,B,C,M,Y,K) - 선택사항")
    monochrome_type: Optional[str] = Field(default=None, description="흑백 타입 (예: 흑, 백) - 선택사항")
    color_name: Optional[str] = Field(default="", min_length=0, description="컬러 이름 (빈 문자열 허용)")


# API 응답을 위한 스키마
class ColorResponse(ColorBase):
    id: int
    color_name: Optional[str] = Field(default="", description="컬러 이름")
    monochrome_type: str
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# 중복 확인 응답을 위한 스키마
class NameCheckResponse(BaseModel):
    exists: bool

class PaginatedColorResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[ColorResponse]