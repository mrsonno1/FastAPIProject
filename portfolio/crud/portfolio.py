from sqlalchemy.orm import Session
from db import models
from portfolio.schemas import portfolio as portfolio_schema
from typing import Optional, List
from sqlalchemy import or_
from fastapi import HTTPException

def create_portfolio(db: Session, portfolio: portfolio_schema.PortfolioCreate, user_id: int):
    # is_fixed_axis 값 검증
    if portfolio.is_fixed_axis not in ['Y', 'N']:
        raise HTTPException(status_code=400, detail="is_fixed_axis는 'Y' 또는 'N'이어야 합니다")

    db_portfolio = models.Portfolio(
        design_name=portfolio.design_name,
        color_name=portfolio.color_name,
        exposed_countries=portfolio.exposed_countries,
        is_fixed_axis=portfolio.is_fixed_axis,
        main_image_url=portfolio.main_image_url,
        design_line_image_id=portfolio.design_line_image_id,
        design_line_color_id=portfolio.design_line_color_id,
        design_base1_image_id=portfolio.design_base1_image_id,
        design_base1_color_id=portfolio.design_base1_color_id,
        design_base2_image_id=portfolio.design_base2_image_id,
        design_base2_color_id=portfolio.design_base2_color_id,
        design_pupil_image_id=portfolio.design_pupil_image_id,
        design_pupil_color_id=portfolio.design_pupil_color_id,
        graphic_diameter=portfolio.graphic_diameter,
        optic_zone=portfolio.optic_zone,
        user_id=user_id
    )

    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


# 디자인명 중복 체크
def get_portfolio_by_design_name(db: Session, design_name: str):
    return db.query(models.Portfolio).filter(models.Portfolio.design_name == design_name).first()


def delete_portfolio_by_id(db: Session, portfolio_id: int) -> bool:
    db_portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        return False

    # Check if the main_image_url is referenced in the Image model
    if db_portfolio.main_image_url and db.query(models.Image).filter(models.Image.public_url == db_portfolio.main_image_url).first():
        raise HTTPException(status_code=400, detail=f"Portfolio '{db_portfolio.design_name}' cannot be deleted as its main image is referenced elsewhere.")

    db.delete(db_portfolio)
    db.commit()
    return True


def get_all_portfolio(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Portfolio).order_by(models.Portfolio.id.desc()).offset(skip).limit(limit).all()



def update_portfolio(
        db: Session,
        db_portfolio: models.Portfolio,
        portfolio_update: portfolio_schema.PortfolioCreate
):
    update_data = portfolio_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_portfolio, key, value)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def get_portfolios_paginated(
        db: Session,
        page: int,
        size: int,
        design_name: Optional[str] = None,
        color_name: Optional[str] = None,
        exposed_countries: Optional[List[str]] = None,
        is_fixed_axis: Optional[str] = None,
        orderBy: Optional[str] = None,
):
    query = db.query(models.Portfolio)

    if design_name:
        query = query.filter(models.Portfolio.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Portfolio.color_name.ilike(f"%{color_name}%"))

    if exposed_countries:
        # 각 국가 ID가 콤마로 구분된 리스트에 포함되어 있는지 확인
        for country_id in exposed_countries:
            query = query.filter(models.Portfolio.exposed_countries.like(f"%{country_id}%"))

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    if orderBy:
        try:
            # 1. '컬럼명 방향'으로 문자열을 분리
            order_column_name, order_direction = orderBy.strip().split()

            # 2. 허용할 컬럼 목록 정의 (보안 및 안정성)
            allowed_columns = {
                "design_name": models.Portfolio.design_name,
                "created_at": models.Portfolio.created_at,
                "views": models.Portfolio.views,
                "id": models.Portfolio.id  # 기본 정렬을 위해 id도 포함
            }

            # 3. 허용된 컬럼인지 확인
            if order_column_name in allowed_columns:
                order_column = allowed_columns[order_column_name]

                # 4. 정렬 방향 적용
                if order_direction.lower() == 'desc':
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                # 허용되지 않은 컬럼명이면 기본 정렬 적용
                query = query.order_by(models.Portfolio.created_at.desc())

        except (ValueError, AttributeError):
            # orderBy 형식이 잘못되었거나 존재하지 않는 컬럼일 경우 기본 정렬로 대체
            query = query.order_by(models.Portfolio.created_at.desc())
    else:
        # orderBy 파라미터가 없으면 기본 정렬 (최신순)
        query = query.order_by(models.Portfolio.created_at.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}


