from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import brand as brand_schema
from Enduser.crud import brand as brand_crud
import math
from services.translate_service import translate_service
from core.dependencies import get_current_language_dependency
router = APIRouter(tags=["Brand"])


# get_brands_list 함수 수정 - Depends에 언어 추가
@router.get("/brands/list", response_model=brand_schema.PaginatedBrandResponse)
def get_brands_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        brand_name: Optional[str] = Query(None, description="브랜드 이름으로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (name: 이름순, name_desc: 이름역순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user),
        language: str = Depends(get_current_language_dependency)  # 추가
):
    """브랜드 목록 조회"""

    paginated_data = brand_crud.get_brands_paginated(
        db=db,
        page=page,
        size=size,
        brand_name=brand_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    # 결과 포맷팅 (번역 적용)
    items = []
    for brand in paginated_data["items"]:
        brand_name_translated = brand.brand_name

        # 영어로 번역이 필요한 경우
        if language == 'en':
            brand_name_translated = translate_service.translate_text(
                brand.brand_name,
                target_lang='en',
                source_lang='ko'
            )

        items.append(brand_schema.BrandListItem(
            brand_name=brand_name_translated,
            brand_image_url=brand.brand_image_url
        ))

    return brand_schema.PaginatedBrandResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=items
    )