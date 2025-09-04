# crud/color.py
from sqlalchemy.orm import Session
from db import models
from Manager.color.schemas import color as color_schema
from typing import Optional
from sqlalchemy import or_, cast, Integer, func, case
from fastapi import HTTPException
import re


def natural_sort_key(text):
    """
    자연 정렬을 위한 키 함수
    7자리 알파뉴메릭 문자열 정렬
    - 숫자만: 0000001 ~ 9999999
    - 알파벳+숫자: AA00001 ~ ZZ99999
    예: 0000001, 0000002, AA00001, AA00002, AB00001, ZZ99999 순서로 정렬
    """
    if not text or text == "":
        return (0, "", 0)  # 빈 문자열은 맨 앞으로
    
    text = text.upper()
    
    # 숫자만 있는 경우
    if text.isdigit():
        return (1, "", int(text))
    
    # 알파벳+숫자 혼합인 경우
    # 앞 2자리 알파벳, 뒤 5자리 숫자 형식 가정
    match = re.match(r'^([A-Z]{1,2})(\d{1,5})$', text)
    if match:
        alpha_part = match.group(1).ljust(2, '0')  # 알파벳 부분을 2자리로 맞춤
        num_part = int(match.group(2))
        return (2, alpha_part, num_part)
    
    # 그 외의 경우 (기타 형식)
    return (3, text, 0)

def get_color_by_name(db: Session, color_name: str):
    """color_name으로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.color_name == color_name).first()

def get_color_by_id(db: Session, color_id: int):
    """ID로 컬러 정보 조회"""
    return db.query(models.Color).filter(models.Color.id == color_id).first()

def create_color(db: Session, color: color_schema.ColorCreate):
    """새로운 컬러 생성"""
    
    # color_name을 입력값 그대로 저장
    color_name = color.color_name if color.color_name is not None else ""

    db_color = models.Color(
        color_name=color_name,
        color_values=color.color_values,
        monochrome_type=color.monochrome_type
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
    # color_name을 입력값 그대로 저장
    color_name = color_update.color_name if color_update.color_name is not None else ""
    
    db_color.color_values = color_update.color_values
    db_color.monochrome_type = color_update.monochrome_type
    db_color.color_name = color_name
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
            )
        )

    total_count = query.count()

    # 2. 동적 정렬 처리
    color_name_sort = False
    sort_desc = False
    
    if orderBy:
        try:
            order_column_name, order_direction = orderBy.strip().split()
            
            # 허용된 정렬 기준 컬럼 정의
            allowed_columns = {
                "id": models.Color.id,
                "color_name": models.Color.color_name,
                "created_at": models.Color.created_at,
                "updated_at": models.Color.updated_at
            }

            if order_column_name in allowed_columns:
                if order_column_name == 'color_name':
                    # color_name 정렬은 Python에서 자연 정렬로 처리
                    color_name_sort = True
                    sort_desc = order_direction.lower() == 'desc'
                    # DB에서는 정렬하지 않고 모든 데이터를 가져옴
                    pass
                else:
                    # 다른 컬럼들은 DB에서 정렬
                    order_column = allowed_columns[order_column_name]
                    direction_func = lambda col: col.desc() if order_direction.lower() == 'desc' else col.asc()
                    query = query.order_by(direction_func(order_column))
            else:
                # 허용되지 않은 컬럼명이면 기본 정렬(최신순) 적용
                query = query.order_by(models.Color.created_at.desc())
        except (ValueError, AttributeError):
            # orderBy 형식이 잘못된 경우 기본 정렬로 대체
            query = query.order_by(models.Color.created_at.desc())
    else:
        # orderBy 파라미터가 없으면 기본 정렬 (최신순)
        query = query.order_by(models.Color.created_at.desc())

    if color_name_sort:
        # color_name으로 정렬하는 경우: 모든 데이터를 가져와서 Python에서 자연 정렬
        all_items = query.all()
        sorted_items = sorted(all_items, key=lambda x: natural_sort_key(x.color_name), reverse=sort_desc)
        
        # 페이지네이션 적용
        offset = (page - 1) * size
        items = sorted_items[offset:offset + size]
    else:
        # 다른 컬럼으로 정렬하는 경우: DB에서 페이지네이션 적용
        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}