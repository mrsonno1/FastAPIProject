# crud/brand.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Integer
from db import models
from typing import Optional
from Manager.brand.schemas import brand as brand_schema
from typing import List
from sqlalchemy import or_
from fastapi import HTTPException

def update_brand_ranks_bulk(db: Session, ranks: List[brand_schema.RankItem]):
    db.query(models.Brand).update(
        {
            models.Brand.rank: case(
                {brand.id: brand.rank for brand in ranks},
                value=models.Brand.id
            )
        },
        synchronize_session=False
    )
    db.commit()


def delete_brand_by_id(db: Session, brand_id: int) -> models.Brand:
    """브랜드 ID로 브랜드를 삭제합니다. 종속성 검사를 포함합니다."""

    # 종속성 검사: released_product 테이블에서 사용 여부 확인
    released_product_usage = db.query(models.ReleasedProduct).filter(
        models.ReleasedProduct.brand_id == brand_id
    ).first()

    if released_product_usage:
        raise HTTPException(
            status_code=400,
            detail="이 브랜드는 출시 제품에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성이 없으면 삭제 진행
    brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="브랜드를 찾을 수 없습니다.")

    db.delete(brand)
    db.commit()
    return brand


def get_all_brands_ordered(db: Session, brand_name: Optional[str] = None):
    query = db.query(models.Brand)
    if brand_name:
        query = query.filter(models.Brand.brand_name.like(f"%{brand_name}%"))
    return query.order_by(models.Brand.rank).all()


def get_brand_by_name(db: Session, brand_name: str):
    return db.query(models.Brand).filter(models.Brand.brand_name == brand_name).first()


def get_brands_paginated(
        db: Session,
        page: int,
        size: int,
        orderBy: Optional[str] = None,
        searchText: Optional[str] = None
):
    query = db.query(models.Brand)
    if searchText:
        search_pattern = f"%{searchText}%"
        query = query.filter(or_(models.Brand.brand_name.like(search_pattern)))
    if orderBy:
        try:
            order_column_name, order_direction = orderBy.split()
            if hasattr(models.Brand, order_column_name):
                order_column = getattr(models.Brand, order_column_name)
                if order_direction.lower() == 'desc':
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
        except:
            query = query.order_by(models.Brand.rank.asc())
    else:
        query = query.order_by(models.Brand.rank.asc())  # 기본 정렬은 rank 순

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}




def create_brand(db: Session, brand_name: str, brand_image_url: str, object_name: str):
    """새로운 브랜드를 가장 낮은 순위로 생성합니다."""
    max_rank = db.query(func.max(models.Brand.rank)).scalar() or 0

    db_brand = models.Brand(
        brand_name=brand_name,
        brand_image_url=brand_image_url,
        object_name=object_name,
        rank=max_rank + 1
    )
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand


def update_brand_info(
        db: Session,
        db_brand: models.Brand,
        brand_name: str,
        brand_image_url: str,
        object_name: Optional[str]
):
    """브랜드의 이름과 이미지 URL을 수정합니다."""
    db_brand.brand_name = brand_name
    db_brand.brand_image_url = brand_image_url
    if object_name: # 새 파일로 교체된 경우 object_name도 업데이트
        db_brand.object_name = object_name
    db.commit()
    db.refresh(db_brand)
    return db_brand


def update_brand_rank(db: Session, brand_id: int, action: str):
    """브랜드의 순위를 변경합니다."""
    target_brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if not target_brand:
        return None

    all_brands = get_all_brands_ordered(db)
    if len(all_brands) <= 1:  # 브랜드가 하나뿐이면 순위 변경 의미 없음
        return all_brands

    # 순위 변경 로직
    if action == "up":
        # 현재 순위보다 한 단계 위로
        current_index = all_brands.index(target_brand)
        if current_index > 0:
            prev_brand = all_brands[current_index - 1]
            # 두 브랜드의 rank 값 맞바꾸기
            target_brand.rank, prev_brand.rank = prev_brand.rank, target_brand.rank

    elif action == "down":
        # 현재 순위보다 한 단계 아래로
        current_index = all_brands.index(target_brand)
        if current_index < len(all_brands) - 1:
            next_brand = all_brands[current_index + 1]
            target_brand.rank, next_brand.rank = next_brand.rank, target_brand.rank

    elif action == "top":
        # 가장 위로 (rank=1)
        # 1. target_brand를 제외한 모든 브랜드의 rank를 1씩 증가시킴
        db.query(models.Brand).filter(models.Brand.id != brand_id).update(
            {models.Brand.rank: models.Brand.rank + 1}, synchronize_session=False
        )
        # 2. target_brand의 rank를 1로 설정
        target_brand.rank = 1

    elif action == "bottom":
        # 가장 아래로
        max_rank = all_brands[-1].rank
        # 1. target_brand를 제외하고 순위가 더 높았던 브랜드들의 rank를 1씩 감소시킴
        db.query(models.Brand).filter(
            models.Brand.id != brand_id,
            models.Brand.rank > target_brand.rank
        ).update({models.Brand.rank: models.Brand.rank - 1}, synchronize_session=False)
        # 2. target_brand의 rank를 가장 높은 값으로 설정
        target_brand.rank = max_rank

    db.commit()
    return get_all_brands_ordered(db)  # 변경된 전체 순위 목록 반환