from sqlalchemy.orm import Session
from sqlalchemy import and_
from db import models
from typing import Optional, Dict, Any
from datetime import date
from Enduser.crud import realtime_users as realtime_users_crud


def get_released_products_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        brand_name: Optional[str] = None,
        item_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """출시 제품 목록을 페이지네이션하여 조회"""

    query = db.query(models.Releasedproduct, models.Brand).join(
        models.Brand,
        models.Releasedproduct.brand_id == models.Brand.id
    )

    # 필터링
    if brand_name:
        query = query.filter(models.Brand.brand_name == brand_name)

    if item_name:
        query = query.filter(models.Releasedproduct.design_name.contains(item_name))

    # 전체 카운트
    total_count = query.count()

    # 정렬
    if orderBy == "latest":
        # 최신순 정렬
        query = query.order_by(models.Releasedproduct.created_at.desc())
    elif orderBy == "popularity" or orderBy is None:
        # 인기순 정렬 (조회수 기준, 동일한 경우 디자인명 ABC순)
        query = query.order_by(
            models.Releasedproduct.views.desc(),
            models.Releasedproduct.design_name.asc()
        )
    else:
        # 기본값: 인기순
        query = query.order_by(
            models.Releasedproduct.views.desc(),
            models.Releasedproduct.design_name.asc()
        )

    # 페이지네이션
    offset = (page - 1) * size
    results = query.offset(offset).limit(size).all()

    # 결과 포맷팅
    formatted_items = []
    for product, brand in results:
        # 실시간 유저수 조회
        realtime_users = realtime_users_crud.get_realtime_users_count(
            db, 'released_product', product.design_name
        )

        formatted_items.append({
            "item_name": product.design_name,
            "main_image_url": product.main_image_url,
            "brand_name": brand.brand_name,
            "realtime_users": realtime_users
        })

    return {
        "total_count": total_count,
        "items": formatted_items
    }


def get_released_product_detail(db: Session, item_name: str) -> Optional[Dict[str, Any]]:
    """디자인 이름으로 출시 제품 상세 정보 조회"""

    result = db.query(models.Releasedproduct, models.Brand).join(
        models.Brand,
        models.Releasedproduct.brand_id == models.Brand.id
    ).filter(
        models.Releasedproduct.design_name == item_name
    ).first()

    if not result:
        return None

    product, brand = result

    # 조회수 증가
    product.views += 1

    # DailyView 기록
    today = date.today()
    daily_view = db.query(models.DailyView).filter(
        models.DailyView.view_date == today,
        models.DailyView.content_type == 'released_product',
        models.DailyView.content_id == product.id
    ).first()

    if daily_view:
        daily_view.view_count += 1
    else:
        new_daily_view = models.DailyView(
            view_date=today,
            content_type='released_product',
            content_id=product.id,
            view_count=1
        )
        db.add(new_daily_view)

    db.commit()
    db.refresh(product)

    # 각 컴포넌트 정보 조회 (색상 정보만)
    def get_component_info(color_id: str):
        if not color_id:
            return None

        color = db.query(models.Color).filter(models.Color.id == color_id).first()

        if not color:
            return None

        return {
            "image_id": None,  # 출시제품은 이미지 정보 없음
            "image_url": None,
            "image_name": None,
            "RGB_id": color_id,
            "RGB_color": color.color_values,
            "RGB_name": color.color_name,
            "size": 100,
            "opacity": 100
        }

    # 실시간 유저수 조회
    realtime_users = realtime_users_crud.get_realtime_users_count(
        db, 'released_product', product.design_name
    )

    return {
        "item_name": product.design_name,
        "color_name": product.color_name,
        "design_line": get_component_info(product.color_line_color_id),
        "design_base1": get_component_info(product.color_base1_color_id),
        "design_base2": get_component_info(product.color_base2_color_id),
        "design_pupil": get_component_info(product.color_pupil_color_id),
        "graphic_diameter": product.graphic_diameter,
        "optic_zone": product.optic_zone,
        "brand_name": brand.brand_name,
        "realtime_users": realtime_users
    }