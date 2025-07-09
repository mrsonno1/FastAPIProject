from sqlalchemy.orm import Session
from custom_design.schemas import custom_design as custom_design_schema
from db import models
from typing import Optional # Optional 임포트
from datetime import date, timedelta # date, timedelta 임포트
from fastapi import HTTPException

def create_design(db: Session, design: custom_design_schema.CustomDesignCreate, user_id: str, code: str):
    db_design = models.CustomDesign(
        item_name=code,
        request_message=design.request_message,
        main_image_url=design.main_image_url,

        design_line_image_id=design.design_line_image_id,
        design_line_color_id=design.design_line_color_id,

        design_base1_image_id=design.design_base1_image_id,
        design_base1_color_id=design.design_base1_color_id,

        design_base2_image_id=design.design_base2_image_id,
        design_base2_color_id=design.design_base2_color_id,

        design_pupil_image_id=design.design_pupil_image_id,
        design_pupil_color_id=design.design_pupil_color_id,

        graphic_diameter=design.graphic_diameter,
        optic_zone=design.optic_zone,
        user_id=user_id
    )
    db.add(db_design)
    db.commit()
    db.refresh(db_design)
    return db_design



def get_design_by_id(db: Session, design_id: int):
    return db.query(models.CustomDesign).filter(models.CustomDesign.id == design_id).first()



def delete_custom_design_by_id(db: Session, design_id: int) -> bool:
    db_design = db.query(models.CustomDesign).filter(models.CustomDesign.id == design_id).first()
    if not db_design:
        return False

    # Check if the main_image_url is referenced in the Image model
    if db_design.main_image_url and db.query(models.Image).filter(models.Image.public_url == db_design.main_image_url).first():
        raise HTTPException(status_code=400, detail=f"Custom Design '{db_design.item_name}' cannot be deleted as its main image is referenced elsewhere.")

    db.delete(db_design)
    db.commit()
    return True


def get_all_designs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CustomDesign).order_by(models.CustomDesign.id.desc()).offset(skip).limit(limit).all()



def update_design_status(
        db: Session,
        design_id: int,
        status_update: custom_design_schema.CustomDesignStatusUpdate
):
    db_design = get_design_by_id(db, design_id)
    if db_design:
        db_design.status = status_update.status
        db.commit()
        db.refresh(db_design)
    return db_design



# ▼▼▼ get_all_designs 함수를 아래와 같이 검색 기능이 추가된 함수로 교체 ▼▼▼
def get_designs_paginated(
        db: Session,
        page: int,
        size: int,
        item_name: Optional[str] = None,
        user_name: Optional[str] = None,
        status: Optional[str] = None,
        orderBy: Optional[str] = None
):
    query = db.query(models.CustomDesign)

    if item_name:
        query = query.filter(models.CustomDesign.item_name.ilike(f"%{item_name}%"))

    if user_name:
        query = query.filter(models.CustomDesign.user_id.ilike(f"%{user_name}%"))

    if status:
        query = query.filter(models.CustomDesign.status.ilike(f"%{status}%"))

    # 정렬 옵션 적용
    if orderBy:
        try:
            order_column, order_direction = orderBy.split()
            if order_column == "item_name":
                if order_direction.lower() == "asc":
                    query = query.order_by(models.CustomDesign.item_name.asc())
                else:
                    query = query.order_by(models.CustomDesign.item_name.desc())
            elif order_column == "status":
                if order_direction.lower() == "asc":
                    query = query.order_by(models.CustomDesign.status.asc())
                else:
                    query = query.order_by(models.CustomDesign.status.desc())
            elif order_column == "created_at":
                if order_direction.lower() == "asc":
                    query = query.order_by(models.CustomDesign.created_at.asc())
                else:
                    query = query.order_by(models.CustomDesign.created_at.desc())
            else:
                # 기본 정렬
                query = query.order_by(models.CustomDesign.id.desc())
        except ValueError:
            # 형식이 잘못된 경우 기본 정렬
            query = query.order_by(models.CustomDesign.id.desc())
    else:
        # orderBy 미지정시 기본 정렬
        query = query.order_by(models.CustomDesign.id.desc())

    # 검색 조건에 맞는 총 개수 계산
    total_count = query.count()

    # 페이지네이션 적용
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}
