from sqlalchemy.orm import Session
from custom_design.schemas import custom_design as custom_design_schema
from db import models
from typing import Optional # Optional 임포트
from datetime import date, timedelta # date, timedelta 임포트
from fastapi import HTTPException

def create_design(db: Session, design: custom_design_schema.CustomDesignCreate, user_id: int, code: str):
    db_design = models.CustomDesign(
        item_name=code,
        request_message=design.request_message,
        main_image_url=design.main_image_url,
        design_line=design.design_line.model_dump() if design.design_line else None,
        design_base1=design.design_base1.model_dump() if design.design_base1 else None,
        design_base2=design.design_base2.model_dump() if design.design_base2 else None,
        design_pupil=design.design_pupil.model_dump() if design.design_pupil else None,
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
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        orderBy: Optional[str] = None,
):
    query = db.query(models.CustomDesign)

    # 1. 디자인명(code_name) 검색 (부분 일치, 대소문자 무시)
    if item_name:
        query = query.filter(models.CustomDesign.item_name.ilike(f"%{item_name}%"))

    # 2. 등록일자(created_at) 기간 검색
    if start_date:
        query = query.filter(models.CustomDesign.created_at >= start_date)
    if end_date:
        # end_date의 자정까지 포함하기 위해 날짜에 1을 더해 그 이전까지로 설정
        query = query.filter(models.CustomDesign.created_at < end_date + timedelta(days=1))

    # 3. 컬러명(color_name) 검색 (JSON 필드 내부 검색)
    if status:
        query = query.filter(models.CustomDesign.status.ilike(f"%{status}%"))

    if orderBy:
        try:
            order_column, order_direction = orderBy.split()
            if order_column == "user_name":
                query = query.outerjoin(models.AdminUser, models.CustomDesign.user_id == models.AdminUser.id)
                if order_direction.lower() == "asc":
                    query = query.order_by(models.AdminUser.username.asc())
                else:
                    query = query.order_by(models.AdminUser.username.desc())
            elif order_column == "item_name":
                if order_direction.lower() == "asc":
                    query = query.order_by(models.CustomDesign.item_name.asc())
                else:
                    query = query.order_by(models.CustomDesign.item_name.desc())
            else:
                # Default sort if orderBy is not recognized
                query = query.order_by(models.CustomDesign.id.desc())
        except Exception: # Catch all exceptions for robustness
            # Default sort if orderBy is not in 'column direction' format or other error occurs
            query = query.order_by(models.CustomDesign.id.desc())
    else:
        query = query.order_by(models.CustomDesign.id.desc())

    # 검색 조건에 맞는 총 개수 계산
    total_count = query.count()

    # 페이지네이션 적용
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}
