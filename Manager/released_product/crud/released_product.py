# crud/released_product.py
from sqlalchemy.orm import Session
from db import models
from Manager.released_product.schemas import released_product as released_product_schema
from typing import Optional
from fastapi import HTTPException
from datetime import date


def create_released_product(db: Session, released_product: dict, user_id: int):
    db_released_product = models.Releasedproduct(
        design_name=released_product.design_name,
        color_name=released_product.color_name,
        brand_id=released_product.brand_id,
        main_image_url=released_product.main_image_url,
        thumbnail_url=released_product.thumbnail_url if hasattr(released_product, 'thumbnail_url') else None,
        color_line_color_id=released_product.color_line_color_id,
        color_base1_color_id=released_product.color_base1_color_id,
        color_base2_color_id=released_product.color_base2_color_id,
        color_pupil_color_id=released_product.color_pupil_color_id,
        graphic_diameter=released_product.graphic_diameter,
        optic_zone=released_product.optic_zone,
        dia=released_product.dia,
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
        released_product_update
):
    # SimpleNamespace 또는 Pydantic 모델 모두 처리 가능하도록 수정
    if hasattr(released_product_update, 'model_dump'):
        # Pydantic 모델인 경우
        update_data = released_product_update.model_dump(exclude_unset=True)
    else:
        # SimpleNamespace인 경우
        update_data = vars(released_product_update)
    
    for key, value in update_data.items():
        # JSON 필드는 model_dump()를 통해 딕셔너리로 변환하여 저장
        if key in ["color_line", "color_base1", "color_base2", "color_pupil"] and value is not None and hasattr(value, 'model_dump'):
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
    query = db.query(models.Releasedproduct, models.Brand).join(
        models.Brand, models.Releasedproduct.brand_id == models.Brand.id
    )

    if brandname:
        query = query.filter(models.Brand.brand_name.ilike(f"%{brandname}%"))
    if design_name:
        query = query.filter(models.Releasedproduct.design_name.ilike(f"%{design_name}%"))
    if color_name:
        # 빈 문자열인 경우 NULL 값 검색, 아닌 경우 LIKE 검색
        if color_name.strip() == "":
            query = query.filter(models.Releasedproduct.color_name.is_(None))
        else:
            query = query.filter(models.Releasedproduct.color_name.ilike(f"%{color_name}%"))

    print("=" * 20)
    print("Query after filtering:")
    print(str(query.statement.compile(compile_kwargs={"literal_binds": True})))
    print("=" * 20)

    total_count = query.count()


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


    offset = (page - 1) * size
    results = query.order_by(models.Releasedproduct.id.desc()).offset(offset).limit(size).all()


    formatted_items = []

    # N+1 문제 최적화를 위해 필요한 모든 color_id 수집
    all_color_ids = set()
    for product, brand in results:
        ids_to_add = [
            product.color_line_color_id, product.color_base1_color_id,
            product.color_base2_color_id, product.color_pupil_color_id
        ]
        all_color_ids.update(id for id in ids_to_add if id)

    # color_id로 color 정보 한 번에 조회
    colors_map = {str(col.id): col for col in
                  db.query(models.Color).filter(models.Color.id.in_(list(all_color_ids))).all()}

    def get_color_name(col_id):
        return colors_map.get(str(col_id)).color_name if str(col_id) in colors_map else ""

    def get_rgb(col_id):
        if str(col_id) in colors_map:
            return ",".join(colors_map[str(col_id)].color_values.split(',')[:3])
        return ""


    def get_color_details(color_id: Optional[str]):
        if not color_id:
            return None
        return db.query(models.Color).filter(models.Color.id == color_id).first()


    for product, brand in results:
        formatted_items.append({
            "id": product.id,
            "brand_id": brand.id,
            "brand_name": brand.brand_name,
            "brand_image_url": brand.brand_image_url,
            "design_name": product.design_name,
            "color_name": product.color_name,
            "image": product.main_image_url,  # 이 라인을 추가합니다.
            "thumbnail_url": product.thumbnail_url,
            "color_line_color": get_color_details(product.color_line_color_id),
            "color_base1_color": get_color_details(product.color_base1_color_id),
            "color_base2_color": get_color_details(product.color_base2_color_id),
            "color_pupil_color": get_color_details(product.color_pupil_color_id),
            "graphic_diameter": product.graphic_diameter,
            "optic": product.optic_zone,
            "dia": product.dia,
            "base_curve": product.base_curve,
            "view_count": product.views,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        })

    return {"items": formatted_items, "total_count": total_count}


def get_released_product_by_id(db: Session, product_id: int):
    """ID로 출시 제품 정보 조회"""
    return db.query(models.Releasedproduct).filter(models.Releasedproduct.id == product_id).first()


def get_released_product_detail(db: Session, product_id: int):
    """ID로 출시 제품의 상세 정보를 조회하고 포맷팅합니다."""
    product = get_released_product_by_id(db, product_id)
    if not product:
        return None

    # Manager API에서는 조회수를 증가시키지 않음
    # (Enduser API에서만 조회수 증가)
    
    # --- [수정] 색상 상세 정보를 가져오는 로직 ---
    def get_color_details(color_id: Optional[str]):
        if not color_id:
            return None
        return db.query(models.Color).filter(models.Color.id == color_id).first()

    brand_name = ""
    brand_image_url = None
    if product.brand_id:
        brand = db.query(models.Brand).filter(models.Brand.id == product.brand_id).first()
        if brand:
            brand_name = brand.brand_name
            brand_image_url = brand.brand_image_url

    # --- [수정] 최종 응답 데이터 구성 ---
    response_data = {
        "id": product.id,
        "brand_id": product.brand_id,
        "brand_name": brand_name,
        "brand_image_url": brand_image_url,
        "design_name": product.design_name,
        "color_name": product.color_name,
        "image": product.main_image_url,
        "thumbnail_url": product.thumbnail_url,
        # 각 색상 ID로 전체 Color 객체를 조회하여 할당
        "color_line_color": get_color_details(product.color_line_color_id),
        "color_base1_color": get_color_details(product.color_base1_color_id),
        "color_base2_color": get_color_details(product.color_base2_color_id),
        "color_pupil_color": get_color_details(product.color_pupil_color_id),
        "g_dia": product.graphic_diameter,
        "optic": product.optic_zone,
        "dia": product.dia,
        "base_curve": product.base_curve
    }

    # Manager API는 조회만 하므로 commit 불필요
    return response_data
