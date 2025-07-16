# crud/color.py
from sqlalchemy.orm import Session
from db import models
from Manager.color.schemas import color as color_schema
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
    """색상 ID로 색상을 삭제합니다. 종속성 검사를 포함합니다."""

    # 종속성 검사: portfolio 테이블에서 사용 여부 확인
    portfolio_usage = db.query(models.Portfolio).filter(
        or_(
            models.Portfolio.design_line_color_id == str(color_id),
            models.Portfolio.design_base1_color_id == str(color_id),
            models.Portfolio.design_base2_color_id == str(color_id),
            models.Portfolio.design_pupil_color_id == str(color_id)
        )
    ).first()

    if portfolio_usage:
        raise HTTPException(
            status_code=400,
            detail="이 컬러는 포트폴리오에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성 검사: custom_design 테이블에서 사용 여부 확인
    custom_design_usage = db.query(models.CustomDesign).filter(
        or_(
            models.CustomDesign.design_line_color_id == str(color_id),
            models.CustomDesign.design_base1_color_id == str(color_id),
            models.CustomDesign.design_base2_color_id == str(color_id),
            models.CustomDesign.design_pupil_color_id == str(color_id)
        )
    ).first()

    if custom_design_usage:
        raise HTTPException(
            status_code=400,
            detail="이 컬러는 커스텀 디자인에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성 검사: released_product 테이블에서 사용 여부 확인
    released_product_usage = db.query(models.Releasedproduct).filter(
        or_(
            models.Releasedproduct.color_line_color_id == str(color_id),
            models.Releasedproduct.color_base1_color_id == str(color_id),
            models.Releasedproduct.color_base2_color_id == str(color_id),
            models.Releasedproduct.color_pupil_color_id == str(color_id)
        )
    ).first()

    if released_product_usage:
        raise HTTPException(
            status_code=400,
            detail="이 컬러는 출시 제품에서 사용 중이므로 삭제할 수 없습니다."
        )

    # 종속성이 없으면 삭제 진행
    color = db.query(models.Color).filter(models.Color.id == color_id).first()
    if not color:
        return False

    db.delete(color)
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
                order_column_name, order_direction = orderBy.strip().split()

                # 허용된 정렬 기준 컬럼 정의 (SQL Injection 방지 및 안정성)
                allowed_columns = {
                    "id": models.Color.id,
                    "color_name": models.Color.color_name,
                    "created_at": models.Color.created_at
                }

                if order_column_name in allowed_columns:
                    order_column = allowed_columns[order_column_name]
                    direction_func = lambda col: col.desc() if order_direction.lower() == 'desc' else col.asc()

                    if order_column_name == 'color_name':
                        # color_name을 숫자로 변환하여 정렬 (기존 로직 유지)
                        numeric_expression = cast(func.regexp_replace(order_column, r'[^0-9]', '', 'g'), Integer)
                        query = query.order_by(direction_func(numeric_expression))
                    else:
                        query = query.order_by(direction_func(order_column))
                else:
                    # 허용되지 않은 컬럼명이면 기본 정렬(최신순) 적용
                    query = query.order_by(models.Color.created_at.desc())
            except (ValueError, AttributeError):
                # orderBy 형식이 잘못되었거나 존재하지 않는 컬럼일 경우 기본 정렬로 대체
                query = query.order_by(models.Color.created_at.desc())
        else:
            # orderBy 파라미터가 없으면 기본 정렬 (최신순)
            query = query.order_by(models.Color.created_at.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}