# crud/color.py
from sqlalchemy.orm import Session
from db import models
from schemas import color as color_schema
from typing import Optional

def get_color_by_name(db: Session, color_name: str):
    """color_name으로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.color_name == color_name).first()


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


def update_color(db: Session, db_color: models.Color, color_update: color_schema.ColorUpdate):
    """컬러 값 업데이트"""
    db_color.color_values = color_update.color_values
    db_color.monochrome_type = color_update.monochrome_type
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
        order_column_name, order_direction = orderBy.split()
        if hasattr(models.Color, order_column_name):
            order_column = getattr(models.Color, order_column_name)
            if order_direction.lower() == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
    else:
        query = query.order_by(models.Color.id.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}