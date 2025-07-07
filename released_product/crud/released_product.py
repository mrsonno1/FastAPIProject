# crud/released_product.py
from sqlalchemy.orm import Session
from db import models
from released_product.schemas import released_product as released_product_schema
from typing import Optional
from fastapi import HTTPException


def create_released_product(db: Session, released_product: released_product_schema.ReleasedProductCreate, user_id: int):
    db_released_product = models.Releasedproduct(
        design_name=released_product.design_name,
        color_name=released_product.color_name,
        main_image_url=released_product.main_image_url,
        brand=released_product.brand,
        color_line=released_product.color_line.model_dump() if released_product.color_line else None,
        color_base1=released_product.color_base1.model_dump() if released_product.color_base1 else None,
        color_base2=released_product.color_base2.model_dump() if released_product.color_base2 else None,
        color_pupil=released_product.color_pupil.model_dump() if released_product.color_pupil else None,
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
