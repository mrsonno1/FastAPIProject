# crud/released_product.py
from sqlalchemy.orm import Session
from db import models
from released_product.schemas import released_product as released_product_schema
from typing import Optional


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
