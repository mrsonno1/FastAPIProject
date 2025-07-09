# crud/released_product.py
from sqlalchemy.orm import Session
from db import models
from released_product.schemas import released_product as released_product_schema
from typing import Optional
from fastapi import HTTPException


def create_released_product(db: Session, released_product: dict, user_id: int):

    # models.Releasedproduct 객체를 생성합니다.
    # 모든 값은 딕셔너리 키 접근 방식( ['key'] 또는 .get('key') )을 사용합니다.
    db_released_product = models.Releasedproduct(
        design_name=released_product['design_name'],
        color_name=released_product['color_name'],
        brand_id=released_product.get('brand_id'),  # DB 모델의 'brand' 컬럼에 'brand_id' 값을 할당
        main_image_url=released_product['main_image_url'],
        color_line_color_id=released_product.get('color_line_color_id'),
        color_base1_color_id=released_product.get('color_base1_color_id'),
        color_base2_color_id=released_product.get('color_base2_color_id'),
        color_pupil_color_id=released_product.get('color_pupil_color_id'),
        graphic_diameter=released_product.get('graphic_diameter'),
        optic_zone=released_product.get('optic_zone'),
        base_curve=released_product.get('base_curve'),
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
):
    query = db.query(models.Releasedproduct)

    if design_name:
        query = query.filter(models.Releasedproduct.design_name.ilike(f"%{design_name}%"))

    if color_name:
        query = query.filter(models.Releasedproduct.color_name.ilike(f"%{color_name}%"))

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
