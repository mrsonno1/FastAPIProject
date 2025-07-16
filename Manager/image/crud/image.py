from sqlalchemy.orm import Session
from db import models
from typing import Optional
from sqlalchemy import or_, cast, Integer, func
from fastapi import HTTPException

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


def delete_image_by_id(db: Session, image_id: int) -> models.Image:
    """이미지 ID로 이미지를 삭제합니다. 종속성 검사를 포함합니다."""

    # 종속성 검사: portfolio 테이블에서 사용 여부 확인
    portfolio_usage = db.query(models.Portfolio).filter(
        or_(
            models.Portfolio.design_line_image_id == str(image_id),
            models.Portfolio.design_base1_image_id == str(image_id),
            models.Portfolio.design_base2_image_id == str(image_id),
            models.Portfolio.design_pupil_image_id == str(image_id)
        )
    ).first()

    if portfolio_usage:
        raise HTTPException(
            status_code=400,
            detail="이 이미지는 포트폴리오에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성 검사: custom_design 테이블에서 사용 여부 확인
    custom_design_usage = db.query(models.CustomDesign).filter(
        or_(
            models.CustomDesign.design_line_image_id == str(image_id),
            models.CustomDesign.design_base1_image_id == str(image_id),
            models.CustomDesign.design_base2_image_id == str(image_id),
            models.CustomDesign.design_pupil_image_id == str(image_id)
        )
    ).first()

    if custom_design_usage:
        raise HTTPException(
            status_code=400,
            detail="이 이미지는 커스텀 디자인에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성이 없으면 삭제 진행
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    db.delete(image)
    db.commit()
    return image

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
        try:
            order_column_name, order_direction = orderBy.strip().split()

            # 허용된 정렬 기준 컬럼 정의
            allowed_columns = {
                "id": models.Image.id,
                "display_name": models.Image.display_name,
                "created_at": models.Image.created_at
            }

            if order_column_name in allowed_columns:
                order_column = allowed_columns[order_column_name]
                direction_func = lambda col: col.desc() if order_direction.lower() == 'desc' else col.asc()

                # display_name을 숫자로 변환하여 정렬 (기존 로직 유지)
                if order_column_name == 'display_name':
                    numeric_expression = cast(func.regexp_replace(order_column, r'[^0-9]', '', 'g'), Integer)
                    query = query.order_by(direction_func(numeric_expression))
                else:
                    query = query.order_by(direction_func(order_column))
            else:
                # 허용되지 않은 컬럼이면 기본 정렬 (최신순)
                query = query.order_by(models.Image.created_at.desc())
        except (ValueError, AttributeError):
            # orderBy 형식이 잘못되었거나 존재하지 않는 컬럼일 경우 기본 정렬로 대체
            query = query.order_by(models.Image.created_at.desc())
    else:
        # orderBy 파라미터가 없으면 기본 정렬 (최신순)
        query = query.order_by(models.Image.created_at.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}