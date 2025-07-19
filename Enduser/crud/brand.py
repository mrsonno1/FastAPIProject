from sqlalchemy.orm import Session
from db import models
from typing import Optional, Dict, Any


def get_brands_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        brand_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """브랜드 목록을 페이지네이션하여 조회"""

    query = db.query(models.Brand)

    # 브랜드명 검색 (부분 일치)
    if brand_name:
        query = query.filter(models.Brand.brand_name.ilike(f"%{brand_name}%"))

    # 전체 카운트
    total_count = query.count()

    # 정렬
    if orderBy == "name":
        query = query.order_by(models.Brand.brand_name.asc())
    elif orderBy == "name_desc":
        query = query.order_by(models.Brand.brand_name.desc())
    else:
        # 기본값: rank 순서
        query = query.order_by(models.Brand.rank.asc())

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }