from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from db import models
from typing import Optional, List, Dict, Any
import math
from datetime import date, datetime
from Enduser.crud import realtime_users as realtime_users_crud


def get_portfolios_paginated(
        db: Session,
        user_id: str,
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
        # 각 국가 ID가 정확히 일치하는지 확인 (콤마로 구분된 값에서 정확한 매칭)
        for country_id in exposed_countries:
            # 정확한 매칭을 위한 조건들:
            # 1. 시작 부분에 있는 경우: "1,2,3" -> "1"로 시작
            # 2. 중간에 있는 경우: "4,1,2" -> ",1,"
            # 3. 끝에 있는 경우: "2,3,1" -> ",1"로 끝
            # 4. 전체가 하나인 경우: "1" -> 정확히 "1"
            query = query.filter(
                or_(
                    models.Portfolio.exposed_countries == country_id,  # 전체가 하나인 경우
                    models.Portfolio.exposed_countries.like(f"{country_id},%"),  # 시작 부분
                    models.Portfolio.exposed_countries.like(f"%,{country_id},%"),  # 중간
                    models.Portfolio.exposed_countries.like(f"%,{country_id}")  # 끝
                )
            )

    if is_fixed_axis is not None:
        query = query.filter(models.Portfolio.is_fixed_axis == is_fixed_axis)

    if item_name:
        query = query.filter(models.Portfolio.design_name.contains(item_name))

    # 전체 카운트
    total_count = query.count()









    # 정렬 처리
    if orderBy == "popularity":
        # 인기순: 조회수 내림차순, 동일한 경우 디자인명 오름차순
        query = query.order_by(
            models.Portfolio.views.desc(),
            models.Portfolio.design_name.asc()
        )
    elif orderBy == "latest":
        # 최신순: 생성일 내림차순
        query = query.order_by(models.Portfolio.created_at.desc())
    else:
        # 기본값: 인기순
        query = query.order_by(
            models.Portfolio.views.desc(),
            models.Portfolio.design_name.asc()
        )






    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    
    # 사용자의 장바구니 아이템 조회
    cart_items = db.query(models.Cart.item_name).filter(
        models.Cart.user_id == user_id,
        models.Cart.category == "포트폴리오"
    ).all()
    cart_item_names = {item.item_name for item in cart_items}

    # 결과 포맷팅
    formatted_items = []
    for portfolio in items:
        # 실시간 유저수 조회
        realtime_users = realtime_users_crud.get_realtime_users_count(
            db, 'portfolio', portfolio.design_name
        )
        
        # user_id로 account_code 조회
        user = db.query(models.AdminUser).filter(
            models.AdminUser.id == portfolio.user_id
        ).first()
        
        account_code = user.account_code if user else None
        
        # 장바구니 포함 여부 확인
        in_cart = portfolio.design_name in cart_item_names

        formatted_items.append({
            "item_name": portfolio.design_name,
            "main_image_url": portfolio.main_image_url,
            "thumbnail_url": portfolio.thumbnail_url,
            "realtime_users": realtime_users,
            "created_at": portfolio.created_at,
            "account_code": account_code,
            "in_cart": in_cart
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
    
    # user_id로 account_code 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.id == portfolio.user_id
    ).first()
    
    account_code = user.account_code if user else None

    return {
        "item_name": portfolio.design_name,
        "color_name": portfolio.color_name,
        "account_code": account_code,
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
        "optic_zone": portfolio.optic_zone,
        "dia": portfolio.dia
    }