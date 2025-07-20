from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from db import models
from typing import Optional, List, Dict, Any
import math
from datetime import date, datetime
from Enduser.crud import realtime_users as realtime_users_crud


def get_portfolios_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        exposed_countries: Optional[List[str]] = None,
        is_fixed_axis: Optional[str] = None,
        item_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """엔드유저용 포트폴리오 목록을 페이지네이션하여 조회"""

    # 기본 쿼리 - 삭제되지 않은 포트폴리오만 조회
    query = db.query(models.Portfolio).filter(
        models.Portfolio.is_deleted == False
    )

    # 필터링
    if exposed_countries:
        # 각 국가 ID가 콤마로 구분된 리스트에 포함되어 있는지 확인
        for country_id in exposed_countries:
            query = query.filter(models.Portfolio.exposed_countries.like(f"%{country_id}%"))

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    if item_name:
        query = query.filter(models.Portfolio.design_name.contains(item_name))

    # 전체 카운트
    total_count = query.count()









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






    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    # 결과 포맷팅
    formatted_items = []
    for portfolio in items:
        # 실시간 유저수 조회
        realtime_users = realtime_users_crud.get_realtime_users_count(
            db, 'portfolio', portfolio.design_name
        )

        formatted_items.append({
            "item_name": portfolio.design_name,
            "main_image_url": portfolio.main_image_url,
            "realtime_users": realtime_users,
            "created_at": portfolio.created_at
        })

    return {
        "total_count": total_count,
        "items": formatted_items
    }


def get_portfolio_detail(db: Session, item_name: str) -> Optional[Dict[str, Any]]:
    """디자인 이름으로 포트폴리오 상세 정보 조회"""

    portfolio = db.query(models.Portfolio).filter(
        models.Portfolio.design_name == item_name,
        models.Portfolio.is_deleted == False
    ).first()

    if not portfolio:
        return None

    # 조회수 증가
    portfolio.views += 1

    # DailyView 기록
    today = date.today()
    daily_view = db.query(models.DailyView).filter(
        models.DailyView.view_date == today,
        models.DailyView.content_type == 'portfolio',
        models.DailyView.content_id == portfolio.id
    ).first()

    if daily_view:
        daily_view.view_count += 1
    else:
        new_daily_view = models.DailyView(
            view_date=today,
            content_type='portfolio',
            content_id=portfolio.id,
            view_count=1
        )
        db.add(new_daily_view)

    db.commit()
    db.refresh(portfolio)

    # 각 컴포넌트 정보 조회
    def get_component_info(image_id: str, color_id: str):
        if not image_id or not color_id:
            return None

        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        color = db.query(models.Color).filter(models.Color.id == color_id).first()

        if not image or not color:
            return None

        return {
            "image_id": image_id,
            "image_url": image.public_url,
            "image_name": image.display_name,
            "RGB_id": color_id,
            "RGB_color": color.color_values,
            "RGB_name": color.color_name,
            "size": 100,
            "opacity": 100  # 포트폴리오는 투명도가 없으므로 100 고정
        }

    return {
        "item_name": portfolio.design_name,
        "color_name": portfolio.color_name,
        "design_line": get_component_info(
            portfolio.design_line_image_id,
            portfolio.design_line_color_id
        ),
        "design_base1": get_component_info(
            portfolio.design_base1_image_id,
            portfolio.design_base1_color_id
        ),
        "design_base2": get_component_info(
            portfolio.design_base2_image_id,
            portfolio.design_base2_color_id
        ),
        "design_pupil": get_component_info(
            portfolio.design_pupil_image_id,
            portfolio.design_pupil_color_id
        ),
        "graphic_diameter": portfolio.graphic_diameter,
        "optic_zone": portfolio.optic_zone
    }