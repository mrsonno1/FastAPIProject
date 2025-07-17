from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import brand as brand_schema
from Enduser.crud import brand as brand_crud
import math

router = APIRouter(tags=["Brand"])


@router.get("/brands/list", response_model=brand_schema.PaginatedBrandResponse)
def get_brands_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        brand_name: Optional[str] = Query(None, description="브랜드 이름으로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (name: 이름순, name_desc: 이름역순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
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

    # 결과 포맷팅
    items = [
        brand_schema.BrandListItem(
            brand_name=brand.brand_name,
            brand_image_url=brand.brand_image_url
        )
        for brand in paginated_data["items"]
    ]

    return brand_schema.PaginatedBrandResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=items
    )