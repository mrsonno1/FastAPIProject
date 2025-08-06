# schemas/country.py
from pydantic import BaseModel, Field
from typing import List, Optional

# 국가 생성을 위한 스키마
class CountryCreate(BaseModel):
    country_name: str = Field(..., min_length=1)
    country_name_en: str = Field(None, min_length=1, description="영문 국가명")

# 국가 정보 수정을 위한 스키마
class CountryUpdate(BaseModel):
    country_name: str = Field(..., min_length=1)
    country_name_en: str = Field(None, min_length=1, description="영문 국가명")

# API 응답을 위한 스키마
class CountryResponse(BaseModel):
    id: int
    country_name: str
    country_name_en: Optional[str] = None
    rank: Optional[int] = None  # rank가 NULL일 수 있도록 수정

    class Config:
        from_attributes = True

# 순위 변경을 위한 스키마 (브랜드와 동일)
class RankUpdate(BaseModel):
    action: str = Field(..., description="순위 변경 동작 (up, down, top, bottom)")

class RankItem(BaseModel):
    id: int
    rank: int

class RankUpdateBulk(BaseModel):
    ranks: List[RankItem]