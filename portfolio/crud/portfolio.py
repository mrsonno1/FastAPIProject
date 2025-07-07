from sqlalchemy.orm import Session
from db import models
from portfolio.schemas import portfolio as portfolio_schema
from typing import Optional, List
from sqlalchemy import or_


def create_portfolio(db: Session, portfolio: portfolio_schema.PortfolioCreate, user_id: int):
    db_portfolio = models.Portfolio(
        item_name=portfolio.item_name,
        color_name=portfolio.color_name,
        exposed_countries=portfolio.exposed_countries,
        is_fixed_axis=portfolio.is_fixed_axis,
        main_image_url=portfolio.main_image_url,
        design_line=portfolio.design_line.model_dump() if portfolio.design_line else None,
        design_base1=portfolio.design_base1.model_dump() if portfolio.design_base1 else None,
        design_base2=portfolio.design_base2.model_dump() if portfolio.design_base2 else None,
        design_pupil=portfolio.design_pupil.model_dump() if portfolio.design_pupil else None,
        graphic_diameter=portfolio.graphic_diameter,
        optic_zone=portfolio.optic_zone,
        user_id=user_id
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


# 아이디 중복 체크
def get_portfolio_by_design_name(db: Session, item_name: str):
    return db.query(models.Portfolio).filter(models.Portfolio.item_name == item_name).first()


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
        item_name: Optional[str] = None,
        color_name: Optional[str] = None,
        exposed_countries: Optional[List[str]] = None,
        is_fixed_axis: Optional[bool] = None,
        orderBy: Optional[str] = None,
):
    query = db.query(models.Portfolio)

    if item_name:
        query = query.filter(models.Portfolio.item_name.ilike(f"%{item_name}%"))

    if color_name:
        query = query.filter(models.Portfolio.color_name.ilike(f"%{color_name}%"))

    if exposed_countries:
        query = query.filter(or_(*[models.Portfolio.exposed_countries.contains(country) for country in exposed_countries]))

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    if orderBy:
        try:
            order_column, order_direction = orderBy.split()
            if order_column == "user_name":
                query = query.outerjoin(models.AdminUser, models.Portfolio.user_id == models.AdminUser.id)
                if order_direction.lower() == "asc":
                    query = query.order_by(models.AdminUser.username.asc())
                else:
                    query = query.order_by(models.AdminUser.username.desc())
            elif order_column == "design_name": # design_name 대신 item_name 사용
                if order_direction.lower() == "asc":
                    query = query.order_by(models.Portfolio.item_name.asc())
                else:
                    query = query.order_by(models.Portfolio.item_name.desc())
            else:
                # Default sort if orderBy is not recognized
                query = query.order_by(models.Portfolio.id.desc())
        except ValueError:
            # Handle cases where orderBy is not in 'column direction' format
            query = query.order_by(models.Portfolio.id.desc())
    else:
        query = query.order_by(models.Portfolio.id.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}


