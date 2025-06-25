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
    category: Optional[str] = None
):
    """
    이미지 목록을 검색 조건(category)과 함께 페이지네이션하여 가져옵니다.
    """
    # 1. 기본 쿼리 시작
    query = db.query(models.Image)

    # 2. category 파라미터가 제공되면, 필터링 조건 추가
    if category:
        query = query.filter(models.Image.category == category)

    # 3. 필터링된 쿼리에서 전체 항목 수 계산
    total_count = query.count()

    # 4. 순서 정렬 및 페이지네이션 적용하여 데이터 가져오기
    offset = (page - 1) * size
    items = query.order_by(models.Image.id.desc()).offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}