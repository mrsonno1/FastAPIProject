from sqlalchemy.orm import Session
from Manager.custom_design.schemas import custom_design as custom_design_schema
from db import models
from typing import Optional, Dict, Any
from fastapi import HTTPException
from Manager.progress_status.crud import progress_status as progress_status_crud


def create_design(db: Session, design: custom_design_schema.CustomDesignCreate, user_id: str):
    db_design = models.CustomDesign(
        item_name=design.item_name,
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
        line_transparency=design.line_transparency,
        base1_transparency=design.base1_transparency,
        base2_transparency=design.base2_transparency,
        pupil_transparency=design.pupil_transparency,
        graphic_diameter=design.graphic_diameter,
        optic_zone=design.optic_zone,
        user_id=user_id
    )
    db.add(db_design)
    db.commit()
    db.refresh(db_design)

    return db_design


def update_design(db: Session, db_design: models.CustomDesign, update_data: Dict[str, Any]):
    """
    제공된 데이터로 커스텀 디자인 객체를 업데이트합니다.
    """
    # 기존 상태 저장
    old_status = db_design.status

    for key, value in update_data.items():
        setattr(db_design, key, value)

    db.commit()
    db.refresh(db_design)

    # status가 '3'으로 변경되었으면 progress_status 생성
    if 'status' in update_data and update_data['status'] == '3' and old_status != '3':
        # AdminUser에서 user_id 가져오기
        user = db.query(models.AdminUser).filter(
            models.AdminUser.username == db_design.user_id
        ).first()

        if user:
            progress_status_crud.check_and_create_progress_status_for_custom_design(
                db=db,
                custom_design_id=db_design.id,
                user_id=user.id
            )

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


def get_design_detail_formatted(db: Session, design_id: int):
    """ID로 커스텀 디자인의 상세 정보를 조회하고 지정된 형식으로 가공합니다."""

    db_design = get_design_by_id(db, design_id)
    if not db_design:
        return None

    def get_image_details(image_id: Optional[str], opacity: Optional[str]):
        if not image_id:
            return None
        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        if not image:
            return None
        try:
            opacity_int = int(opacity) if opacity is not None else None
        except (ValueError, TypeError):
            opacity_int = None
        return {
            "id": image.id,
            "display_name": image.display_name,
            "public_url": image.public_url,
            "opacity": opacity_int
        }

    def get_color_details(color_id: Optional[str]):
        if not color_id:
            return None
        color = db.query(models.Color).filter(models.Color.id == color_id).first()
        if not color:
            return None
        return {
            "id": color.id,
            "color_name": color.color_name,
            "color_values": color.color_values
        }

    # 각 컴포넌트 정보 조회
    design_line_details = get_image_details(db_design.design_line_image_id, db_design.line_transparency)
    design_line_color_details = get_color_details(db_design.design_line_color_id)

    design_base1_details = get_image_details(db_design.design_base1_image_id, db_design.base1_transparency)
    design_base1_color_details = get_color_details(db_design.design_base1_color_id)

    design_base2_details = get_image_details(db_design.design_base2_image_id, db_design.base2_transparency)
    design_base2_color_details = get_color_details(db_design.design_base2_color_id)

    design_pupil_details = get_image_details(db_design.design_pupil_image_id, db_design.pupil_transparency)
    design_pupil_color_details = get_color_details(db_design.design_pupil_color_id)

    # 최종 응답 데이터 구성
    response_data = {
        "id": db_design.id,
        "item_name": db_design.item_name,
        "user_name": db_design.user_id,
        "status": db_design.status,
        "request_message": db_design.request_message,
        "main_image_url": db_design.main_image_url,

        "design_line": design_line_details,
        "design_line_color": design_line_color_details,

        "design_base1": design_base1_details,
        "design_base1_color": design_base1_color_details,

        "design_base2": design_base2_details,
        "design_base2_color": design_base2_color_details,

        "design_pupil": design_pupil_details,
        "design_pupil_color": design_pupil_color_details,

        "graphic_diameter": db_design.graphic_diameter,
        "optic_zone": db_design.optic_zone,

        "created_at": db_design.created_at,
        "updated_at": db_design.updated_at
    }

    return response_data




# ▼▼▼ get_all_designs 함수를 아래와 같이 검색 기능이 추가된 함수로 교체 ▼▼▼
def get_designs_paginated(
        db: Session,
        page: int,
        size: int,
        item_name: Optional[str] = None,
        user_name: Optional[str] = None,
        status: Optional[str] = None,
):
    # --- [수정 1] 기본 쿼리를 account 테이블과 JOIN하도록 변경 ---
    # CustomDesign 객체와 Account 객체를 함께 조회합니다.
    query = db.query(models.CustomDesign, models.AdminUser).join(
        models.AdminUser, models.CustomDesign.user_id == models.AdminUser.username
    )

    # --- [수정 2] 필터링 로직 수정 ---
    if item_name:
        query = query.filter(models.CustomDesign.item_name.ilike(f"%{item_name}%"))

    if user_name:
        # user_name 파라미터로 AdminUser의 username 또는 contact_name을 검색
        query = query.filter(
            (models.AdminUser.username.ilike(f"%{user_name}%")) |
            (models.AdminUser.contact_name.ilike(f"%{user_name}%"))
        )

    if status:
        query = query.filter(models.CustomDesign.status.ilike(f"%{status}%"))

    # 검색 조건에 맞는 총 개수 계산
    total_count = query.count()

    # 페이지네이션 적용
    offset = (page - 1) * size
    results = query.order_by(models.CustomDesign.created_at.desc()).offset(offset).limit(size).all()

    # --- [수정 3] 결과를 새로운 형식에 맞게 가공 ---
    formatted_items = []
    for design, user in results:
        formatted_items.append({
            "id": design.id,
            # user_name은 AdminUser의 contact_name을 우선으로, 없으면 username을 사용
            "user_name": user.contact_name or user.username,
            "main_image_url": design.main_image_url,
            "item_name": design.item_name,
            "user_id": design.user_id,
            "created_at": design.created_at,
            "status": design.status,
            "updated_at": design.updated_at
        })

    return {"items": formatted_items, "total_count": total_count}
