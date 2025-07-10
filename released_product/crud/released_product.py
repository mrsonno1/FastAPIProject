# crud/released_product.py
from sqlalchemy.orm import Session
from db import models
from released_product.schemas import released_product as released_product_schema
from typing import Optional
from fastapi import HTTPException
from datetime import date
from sqlalchemy.dialects.postgresql import insert # PostgreSQL의 UPSERT 기능 사용

def create_released_product(db: Session, released_product: dict, user_id: int):
    db_released_product = models.Releasedproduct(
        design_name=released_product.design_name,
        color_name=released_product.color_name,
        brand_id=released_product.brand_id,
        main_image_url=released_product.main_image_url,
        color_line_color_id=released_product.color_line_color_id,
        color_base1_color_id=released_product.color_base1_color_id,
        color_base2_color_id=released_product.color_base2_color_id,
        color_pupil_color_id=released_product.color_pupil_color_id,
        graphic_diameter=released_product.graphic_diameter,
        optic_zone=released_product.optic_zone,
        base_curve=released_product.base_curve,
        user_id=user_id
    )
    db.add(db_released_product)
    db.commit()
    db.refresh(db_released_product)
    return db_released_product

def get_released_product_by_design_name(db: Session, design_name: str):
    return db.query(models.Releasedproduct).filter(models.Releasedproduct.design_name == design_name).first()

def delete_released_product_by_id(db: Session, product_id: int) -> bool:
    db_product = db.query(models.Releasedproduct).filter(models.Releasedproduct.id == product_id).first()
    if not db_product:
        return False

    # Check if the main_image_url is referenced in the Image model
    if db_product.main_image_url and db.query(models.Image).filter(models.Image.public_url == db_product.main_image_url).first():
        raise HTTPException(status_code=400, detail=f"Released Product '{db_product.design_name}' cannot be deleted as its main image is referenced elsewhere.")

    db.delete(db_product)
    db.commit()
    return True

def update_released_product(
        db: Session,
        db_released_product: models.Releasedproduct,
        released_product_update: released_product_schema.ReleasedProductCreate
):
    update_data = released_product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # JSON 필드는 model_dump()를 통해 딕셔너리로 변환하여 저장
        if key in ["color_line", "color_base1", "color_base2", "color_pupil"] and value is not None:
            setattr(db_released_product, key, value.model_dump())
        else:
            setattr(db_released_product, key, value)
    db.commit()
    db.refresh(db_released_product)
    return db_released_product


def get_released_products_paginated(
        db: Session,
        page: int,
        size: int,
        design_name: Optional[str] = None,
        color_name: Optional[str] = None,
        brandname: Optional[str] = None,
        orderBy: Optional[str] = None,
):
    query = db.query(models.Releasedproduct)

    if design_name:
        query = query.filter(models.Releasedproduct.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Releasedproduct.color_name.ilike(f"%{color_name}%"))

    if brandname:
        # Releasedproduct.brand_id와 Brand.id를 기준으로 JOIN
        query = query.join(models.Brand, models.Releasedproduct.brand_id == models.Brand.id)
        # JOIN된 Brand 테이블의 brand_name 컬럼으로 필터링
        query = query.filter(models.Brand.brand_name.ilike(f"%{brandname}%"))

    if orderBy:
        try:
            order_column_name, order_direction = orderBy.strip().split()

            # 허용할 정렬 컬럼 목록 정의
            allowed_columns = {
                "created_at": models.Releasedproduct.created_at,
                "views": models.Releasedproduct.views,
                "id": models.Releasedproduct.id
            }

            if order_column_name in allowed_columns:
                order_column = allowed_columns[order_column_name]
                if order_direction.lower() == 'desc':
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                # 허용되지 않은 컬럼이면 기본 정렬 (최신순)
                query = query.order_by(models.Releasedproduct.created_at.desc())

        except (ValueError, AttributeError):
            # 형식이 잘못된 경우 기본 정렬 (최신순)
            query = query.order_by(models.Releasedproduct.created_at.desc())
    else:
        # orderBy 파라미터가 없으면 기본 정렬 (최신순)
        query = query.order_by(models.Releasedproduct.created_at.desc())

    total_count = query.count()
    offset = (page - 1) * size
    items = query.order_by(models.Releasedproduct.id.desc()).offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}


def get_released_product_by_id(db: Session, product_id: int):
    """ID로 출시 제품 정보 조회"""
    return db.query(models.Releasedproduct).filter(models.Releasedproduct.id == product_id).first()


def get_released_product_detail(db: Session, product_id: int):
    """ID로 출시 제품의 상세 정보를 조회하고 포맷팅합니다."""
    # 제품 기본 정보 조회
    product = get_released_product_by_id(db, product_id)
    if not product:
        return None

    db.query(models.Releasedproduct).filter(models.Releasedproduct.id == product_id).update(
        {models.Releasedproduct.views: models.Releasedproduct.views + 1},
        synchronize_session=False
    )

    # --- [DailyView 기록 로직 추가] ---
    today = date.today()

    # PostgreSQL의 ON CONFLICT DO UPDATE (UPSERT) 문 실행
    stmt = insert(models.DailyView).values(
        view_date=today,
        content_type='released_product',
        content_id=product_id,
        view_count=1
    ).on_conflict_do_update(
        index_elements=['view_date', 'content_type', 'content_id'],
        set_={'view_count': models.DailyView.view_count + 1}
    )
    db.execute(stmt)
    # ---------------------------

    db.commit()  # 모든 변경사항(views, daily_views)을 한 번에 커밋


    # 컬러 정보 조회
    color_names = []
    color_rgb_values = []

    brand_image_url = None

    # 라인 컬러 정보
    if product.color_line_color_id:
        line_color = db.query(models.Color).filter(models.Color.id == product.color_line_color_id).first()
        if line_color:
            color_names.append(line_color.color_name)
            # 컬러 값에서 처음 3개 값만 가져옴
            rgb_parts = line_color.color_values.split(',')[:3]
            color_rgb_values.append(','.join(rgb_parts))

    # 바탕1 컬러 정보
    if product.color_base1_color_id:
        base1_color = db.query(models.Color).filter(models.Color.id == product.color_base1_color_id).first()
        if base1_color:
            color_names.append(base1_color.color_name)
            rgb_parts = base1_color.color_values.split(',')[:3]
            color_rgb_values.append(','.join(rgb_parts))

    # 바탕2 컬러 정보
    if product.color_base2_color_id:
        base2_color = db.query(models.Color).filter(models.Color.id == product.color_base2_color_id).first()
        if base2_color:
            color_names.append(base2_color.color_name)
            rgb_parts = base2_color.color_values.split(',')[:3]
            color_rgb_values.append(','.join(rgb_parts))

    # 동공 컬러 정보
    if product.color_pupil_color_id:
        pupil_color = db.query(models.Color).filter(models.Color.id == product.color_pupil_color_id).first()
        if pupil_color:
            color_names.append(pupil_color.color_name)
            rgb_parts = pupil_color.color_values.split(',')[:3]
            color_rgb_values.append(','.join(rgb_parts))

    # 브랜드 정보 조회
    brand_name = ""
    if product.brand_id:
        brand = db.query(models.Brand).filter(models.Brand.id == product.brand_id).first()
        if brand:
            brand_name = brand.brand_name
            brand_image_url = brand.brand_image_url

    # 응답 데이터 구성
    return {
        "id": product.id,
        "brandname": brand_name,
        "brandimage": brand_image_url,
        "designName": product.design_name,
        "colorName": product.color_name,
        "image": product.main_image_url,

        "dkColor": color_names,
        "dkrgb": color_rgb_values,
        "G_DIA": product.graphic_diameter,
        "Optic": product.optic_zone,
        "baseCurve": product.base_curve
    }


def get_formatted_released_products(db: Session, page: int, size: int, design_name: Optional[str] = None, color_name: Optional[str] = None):
    """출시 제품 목록을 포맷팅된 형태로 조회합니다."""
    query = db.query(models.Releasedproduct)

    if design_name:
        query = query.filter(models.Releasedproduct.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Releasedproduct.color_name.ilike(f"%{color_name}%"))

    total_count = query.count()
    offset = (page - 1) * size
    products = query.order_by(models.Releasedproduct.id.desc()).offset(offset).limit(size).all()

    formatted_items = []
    for idx, product in enumerate(products):
        # 브랜드 정보 조회
        brand_data = {}
        if product.brand_id:
            brand = db.query(models.Brand).filter(models.Brand.id == product.brand_id).first()
            if brand:
                brand_data = {
                    "brand_name": brand.brand_name,
                    "brand_image_url": brand.brand_image_url
                }

        # 컬러 정보 조회
        color_names = []
        color_rgb_values = []

        # 라인 컬러 정보
        if product.color_line_color_id:
            line_color = db.query(models.Color).filter(models.Color.id == product.color_line_color_id).first()
            if line_color:
                color_names.append(line_color.color_name)
                rgb_parts = line_color.color_values.split(',')[:3]
                color_rgb_values.append(','.join(rgb_parts))

        # 바탕1 컬러 정보
        if product.color_base1_color_id:
            base1_color = db.query(models.Color).filter(models.Color.id == product.color_base1_color_id).first()
            if base1_color:
                color_names.append(base1_color.color_name)
                rgb_parts = base1_color.color_values.split(',')[:3]
                color_rgb_values.append(','.join(rgb_parts))

        # 바탕2 컬러 정보
        if product.color_base2_color_id:
            base2_color = db.query(models.Color).filter(models.Color.id == product.color_base2_color_id).first()
            if base2_color:
                color_names.append(base2_color.color_name)
                rgb_parts = base2_color.color_values.split(',')[:3]
                color_rgb_values.append(','.join(rgb_parts))

        # 동공 컬러 정보
        if product.color_pupil_color_id:
            pupil_color = db.query(models.Color).filter(models.Color.id == product.color_pupil_color_id).first()
            if pupil_color:
                color_names.append(pupil_color.color_name)
                rgb_parts = pupil_color.color_values.split(',')[:3]
                color_rgb_values.append(','.join(rgb_parts))

        # 등록일 포맷팅 (YY/MM/DD)
        register_date = product.created_at.strftime("%y/%m/%d") if product.created_at else ""

        # 응답 데이터 구성
        formatted_items.append({
            "no": product.id,
            "brandname": brand_data.get("brand_name", ""),
            "image": product.main_image_url,
            "designName": product.design_name,
            "colorName": product.color_name,
            "dkColor": color_names,
            "dkrgb": color_rgb_values,
            "diameter": {
                "G_DIA": product.graphic_diameter,
                "Optic": product.optic_zone
            },
            "viewCount": product.views,
            "registerDate": register_date
        })

    return {"items": formatted_items, "total_count": total_count}
