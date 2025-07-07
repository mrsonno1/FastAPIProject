# crud/color.py
from sqlalchemy.orm import Session
from db import models
from color.schemas import color as color_schema
from typing import Optional
from sqlalchemy import or_, cast, Integer, func
from fastapi import HTTPException

def get_color_by_name(db: Session, color_name: str):
    """color_name으로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.color_name == color_name).first()

def get_color_by_id(db: Session, color_id: int):
    """ID로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.id == color_id).first()

def create_color(db: Session, color: color_schema.ColorCreate):
    """새로운 컬러 생성"""
    db_color = models.Color(
        color_name=color.color_name,
        color_values=color.color_values,
        monochrome_type = color.monochrome_type
    )
    db.add(db_color)
    db.commit()
    db.refresh(db_color)
    return db_color

def delete_color_by_id(db: Session, color_id: int) -> bool:
    """ID로 컬러 정보를 찾아 삭제합니다."""
    db_color = db.query(models.Color).filter(models.Color.id == color_id).first()
    if not db_color:
        return False

    color_name = db_color.color_name

    # Check in Portfolio
    if db.query(models.Portfolio).filter(
        (models.Portfolio.color_name == color_name) |
        (models.Portfolio.design_line.op('->>')('RGB_name') == color_name) |
        (models.Portfolio.design_base1.op('->>')('RGB_name') == color_name) |
        (models.Portfolio.design_base2.op('->>')('RGB_name') == color_name) |
        (models.Portfolio.design_pupil.op('->>')('RGB_name') == color_name)
    ).first():
        raise HTTPException(status_code=400, detail=f"Color '{color_name}' cannot be deleted as it is referenced in a portfolio.")

    # Check in Releasedproduct
    if db.query(models.Releasedproduct).filter(
        (models.Releasedproduct.color_name == color_name) |
        (models.Releasedproduct.color_line.op('->>')('RGB_name') == color_name) |
        (models.Releasedproduct.color_base1.op('->>')('RGB_name') == color_name) |
        (models.Releasedproduct.color_base2.op('->>')('RGB_name') == color_name) |
        (models.Releasedproduct.color_pupil.op('->>')('RGB_name') == color_name)
    ).first():
        raise HTTPException(status_code=400, detail=f"Color '{color_name}' cannot be deleted as it is referenced in a released product.")

    # Check in CustomDesign
    if db.query(models.CustomDesign).filter(
        (models.CustomDesign.design_line.op('->>')('RGB_name') == color_name) |
        (models.CustomDesign.design_base1.op('->>')('RGB_name') == color_name) |
        (models.CustomDesign.design_base2.op('->>')('RGB_name') == color_name) |
        (models.CustomDesign.design_pupil.op('->>')('RGB_name') == color_name)
    ).first():
        raise HTTPException(status_code=400, detail=f"Color '{color_name}' cannot be deleted as it is referenced in a custom design.")

    db.delete(db_color)
    db.commit()
    return True

def update_color(db: Session, db_color: models.Color, color_update: color_schema.ColorUpdate):
    """컬러 값 업데이트"""
    db_color.color_values = color_update.color_values
    db_color.monochrome_type = color_update.monochrome_type
    db_color.color_name = color_update.color_name
    db.commit()
    db.refresh(db_color)
    return db_color


def get_colors_paginated(
        db: Session,
        page: int,
        size: int,
        orderBy: Optional[str] = None,
        searchText: Optional[str] = None
):
    query = db.query(models.Color)

    # 1. 다중 컬럼 텍스트 검색
    if searchText:
        search_pattern = f"%{searchText}%"
        query = query.filter(
            or_(
                models.Color.color_name.like(search_pattern),
                models.Color.monochrome_type.like(search_pattern),
                models.Color.color_values.like(search_pattern)
            )
        )

    # 2. 동적 정렬
    if orderBy:
        try:
            order_column_name, order_direction = orderBy.split()
            direction_func = lambda col: col.desc() if order_direction.lower() == 'desc' else col.asc()

            order_column = getattr(models.Color, order_column_name)

            # 만약 정렬 대상이 color_name이라면, 숫자로 형 변환하여 정렬
            if order_column_name == 'color_name':
                numeric_expression = cast(func.regexp_replace(order_column, r'[^0-9]', '', 'g'), Integer)
                query = query.order_by(direction_func(numeric_expression))
            else:
                query = query.order_by(direction_func(order_column))

        except (ValueError, AttributeError):
            query = query.order_by(models.Color.id.desc())
    else:
        query = query.order_by(models.Color.id.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}