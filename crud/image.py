# crud/image.py
from sqlalchemy.orm import Session
from db import models
from typing import Optional


def update_image(
        db: Session,
        db_image: models.Image,
        display_name: str,
        new_object_name: Optional[str] = None,
        new_public_url: Optional[str] = None
):
    """
    이미지의 정보를 업데이트합니다. (이름, 파일 정보 등)
    """
    db_image.display_name = display_name

    # 새로운 파일 정보가 제공된 경우에만 업데이트
    if new_object_name and new_public_url:
        db_image.object_name = new_object_name
        db_image.public_url = new_public_url

    db.commit()
    db.refresh(db_image)
    return db_image


def get_image_by_display_name(db: Session, category: str, display_name: str):
    """category와 display_name의 조합으로 이미지 정보 조회"""
    return db.query(models.Image).filter(
        models.Image.category == category,
        models.Image.display_name == display_name
    ).first()


def update_image_file(db: Session, db_image: models.Image, new_object_name: str, new_public_url: str):
    """이미지 파일 교체 후 DB 정보(object_name, public_url) 업데이트"""
    db_image.object_name = new_object_name
    db_image.public_url = new_public_url
    db.commit()
    db.refresh(db_image)
    return db_image


def get_images_paginated(
        db: Session,
        page: int,
        size: int,
        category: Optional[str] = None,
        orderBy: Optional[str] = None,
        searchText: Optional[str] = None
):
    query = db.query(models.Image)

    # 1. 카테고리 필터링
    if category:
        query = query.filter(models.Image.category == category)

    # 2. 다중 컬럼 텍스트 검색 (searchText)
    if searchText:
        search_pattern = f"%{searchText}%"
        query = query.filter(
            or_(
                models.Image.display_name.like(search_pattern),
                models.Image.category.like(search_pattern)
                # 추가하고 싶은 다른 검색 대상 컬럼을 여기에 or_()로 추가
            )
        )

    # 3. 동적 정렬 (orderBy)
    if orderBy:
        # 예: "rank asc", "id desc"
        order_column_name, order_direction = orderBy.split()
        if hasattr(models.Image, order_column_name):
            order_column = getattr(models.Image, order_column_name)
            if order_direction.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        # 기본 정렬
        query = query.order_by(models.Image.id.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}