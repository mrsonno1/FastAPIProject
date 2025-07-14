# progress_status/crud/progress_status.py
from sqlalchemy.orm import Session
from db import models
from progress_status.schemas import progress_status as progress_status_schema
from typing import Optional
from fastapi import HTTPException


def create_progress_status(
        db: Session,
        progress_status: progress_status_schema.ProgressStatusCreate
):
    """새로운 진행 상태를 생성합니다."""
    db_progress_status = models.Progressstatus(
        user_id=progress_status.user_id,
        custom_design_id=progress_status.custom_design_id,
        portfolio_id=progress_status.portfolio_id,
        status=progress_status.status,
        notes=progress_status.notes
    )
    db.add(db_progress_status)
    db.commit()
    db.refresh(db_progress_status)
    return db_progress_status


def check_and_create_progress_status_for_custom_design(
        db: Session,
        custom_design_id: int,
        user_id: int
):
    """커스텀 디자인의 상태가 3일 때 progress_status가 없으면 생성합니다."""
    # 이미 progress_status가 있는지 확인
    existing = db.query(models.Progressstatus).filter(
        models.Progressstatus.custom_design_id == custom_design_id
    ).first()

    if not existing:
        # progress_status 생성
        progress_status_data = progress_status_schema.ProgressStatusCreate(
            user_id=user_id,
            custom_design_id=custom_design_id,
            portfolio_id=None,
            status="0",  # 대기 상태로 시작
            notes="커스텀 디자인 완료로 인한 자동 생성"
        )
        return create_progress_status(db, progress_status_data)
    return existing


def create_progress_status_for_portfolio(
        db: Session,
        portfolio_id: int,
        custom_design_id: int,
        user_id: int
):
    """포트폴리오 생성 시 progress_status를 생성합니다. (업데이트 하지 않음)"""
    # 새로운 progress_status 생성
    progress_status_data = progress_status_schema.ProgressStatusCreate(
        user_id=user_id,
        custom_design_id=custom_design_id,
        portfolio_id=portfolio_id,
        status="0",  # 대기 상태로 시작
        notes="포트폴리오 생성으로 인한 자동 생성"
    )
    return create_progress_status(db, progress_status_data)


def sync_existing_data(db: Session):
    """기존 데이터를 기반으로 progress_status를 일괄 생성합니다."""
    created_count = 0

    # 1. status가 '3'인 모든 custom_design 찾기
    completed_designs = db.query(models.CustomDesign).filter(
        models.CustomDesign.status == '3'
    ).all()

    for design in completed_designs:
        # progress_status가 없으면 생성
        existing = db.query(models.Progressstatus).filter(
            models.Progressstatus.custom_design_id == design.id,
            models.Progressstatus.portfolio_id.is_(None)  # portfolio_id가 없는 것만
        ).first()

        if not existing:
            # AdminUser에서 user_id 가져오기
            user = db.query(models.AdminUser).filter(
                models.AdminUser.username == design.user_id
            ).first()

            if user:
                progress_status_data = progress_status_schema.ProgressStatusCreate(
                    user_id=user.id,
                    custom_design_id=design.id,
                    portfolio_id=None,
                    status="0",
                    notes="기존 데이터 동기화 - custom_design"
                )
                create_progress_status(db, progress_status_data)
                created_count += 1

    # 2. 모든 portfolio에 대해 progress_status 생성 (업데이트 하지 않고 새로 생성)
    portfolios = db.query(models.Portfolio).all()

    for portfolio in portfolios:
        # 포트폴리오와 연관된 custom_design 찾기
        user = db.query(models.AdminUser).filter(
            models.AdminUser.id == portfolio.user_id
        ).first()

        if user:
            # 해당 사용자의 custom_design 찾기
            custom_designs = db.query(models.CustomDesign).filter(
                models.CustomDesign.user_id == user.username
            ).order_by(models.CustomDesign.created_at.desc()).all()

            if custom_designs:
                # 가장 최근의 custom_design 사용
                latest_design = custom_designs[0]

                # 해당 portfolio_id를 가진 progress_status가 있는지 확인
                existing = db.query(models.Progressstatus).filter(
                    models.Progressstatus.portfolio_id == portfolio.id
                ).first()

                if not existing:
                    # 새로 생성
                    progress_status_data = progress_status_schema.ProgressStatusCreate(
                        user_id=portfolio.user_id,
                        custom_design_id=latest_design.id,
                        portfolio_id=portfolio.id,
                        status="0",
                        notes="기존 데이터 동기화 - portfolio"
                    )
                    create_progress_status(db, progress_status_data)
                    created_count += 1

    return created_count


def get_progress_status_by_id(db: Session, progress_status_id: int):
    """ID로 진행 상태 조회"""
    return db.query(models.Progressstatus).filter(
        models.Progressstatus.id == progress_status_id
    ).first()


def update_progress_status(
        db: Session,
        db_progress_status: models.Progressstatus,
        progress_status_update: progress_status_schema.ProgressStatusUpdate
):
    """진행 상태 정보를 업데이트합니다."""
    update_data = progress_status_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_progress_status, key, value)
    db.commit()
    db.refresh(db_progress_status)
    return db_progress_status


def delete_progress_status_by_id(db: Session, progress_status_id: int) -> bool:
    """ID로 진행 상태를 삭제합니다."""
    db_progress_status = db.query(models.Progressstatus).filter(
        models.Progressstatus.id == progress_status_id
    ).first()
    if not db_progress_status:
        return False

    db.delete(db_progress_status)
    db.commit()
    return True


def get_progress_status_paginated(
        db: Session,
        page: int,
        size: int,
        user_name: Optional[str] = None,
        custom_design_name: Optional[str] = None,
        portfolio_name: Optional[str] = None,
        status: Optional[str] = None,
):
    """진행 상태 목록을 페이지네이션하여 조회합니다."""

    # 기본 쿼리 - 필요한 테이블들을 조인
    query = db.query(
        models.Progressstatus,
        models.AdminUser,
        models.CustomDesign,
        models.Portfolio
    ).join(
        models.AdminUser, models.Progressstatus.user_id == models.AdminUser.id
    ).join(
        models.CustomDesign, models.Progressstatus.custom_design_id == models.CustomDesign.id
    ).outerjoin(  # portfolio는 optional이므로 left outer join
        models.Portfolio, models.Progressstatus.portfolio_id == models.Portfolio.id
    )

    # 필터링 적용
    if user_name:
        query = query.filter(
            (models.AdminUser.username.ilike(f"%{user_name}%")) |
            (models.AdminUser.contact_name.ilike(f"%{user_name}%"))
        )

    if custom_design_name:
        query = query.filter(
            models.CustomDesign.item_name.ilike(f"%{custom_design_name}%")
        )

    if portfolio_name:
        query = query.filter(
            models.Portfolio.design_name.ilike(f"%{portfolio_name}%")
        )

    if status:
        query = query.filter(models.Progressstatus.status == status)

    # 총 개수 계산
    total_count = query.count()

    # 페이지네이션 적용
    offset = (page - 1) * size
    results = query.order_by(
        models.Progressstatus.created_at.desc()
    ).offset(offset).limit(size).all()

    # 모든 필요한 ID들을 먼저 수집 (N+1 문제 방지)
    all_image_ids = set()
    all_color_ids = set()

    for progress_status, user, custom_design, portfolio in results:
        # portfolio가 있으면 portfolio의 ID들 수집
        if portfolio:
            ids_to_add = [
                portfolio.design_line_image_id, portfolio.design_base1_image_id,
                portfolio.design_base2_image_id, portfolio.design_pupil_image_id
            ]
            all_image_ids.update(filter(None, ids_to_add))

            color_ids_to_add = [
                portfolio.design_line_color_id, portfolio.design_base1_color_id,
                portfolio.design_base2_color_id, portfolio.design_pupil_color_id
            ]
            all_color_ids.update(filter(None, color_ids_to_add))
        else:
            # portfolio가 없으면 custom_design의 ID들 수집
            ids_to_add = [
                custom_design.design_line_image_id, custom_design.design_base1_image_id,
                custom_design.design_base2_image_id, custom_design.design_pupil_image_id
            ]
            all_image_ids.update(filter(None, ids_to_add))

            color_ids_to_add = [
                custom_design.design_line_color_id, custom_design.design_base1_color_id,
                custom_design.design_base2_color_id, custom_design.design_pupil_color_id
            ]
            all_color_ids.update(filter(None, color_ids_to_add))

    # ID를 한 번에 조회하여 딕셔너리로 만듦
    images_map = {str(img.id): img for img in
                  db.query(models.Image).filter(
                      models.Image.id.in_(list(all_image_ids))).all()} if all_image_ids else {}
    colors_map = {str(col.id): col for col in
                  db.query(models.Color).filter(
                      models.Color.id.in_(list(all_color_ids))).all()} if all_color_ids else {}

    # 헬퍼 함수
    def get_image_details(image_id):
        if not image_id:
            return None
        img = images_map.get(str(image_id))
        if img:
            return {
                "id": img.id,
                "display_name": img.display_name,
                "public_url": img.public_url
            }
        return None

    def get_color_details(color_id):
        if not color_id:
            return None
        col = colors_map.get(str(color_id))
        if col:
            return {
                "id": col.id,
                "color_name": col.color_name,
                "color_values": col.color_values
            }
        return None

    # 결과를 원하는 형식으로 가공
    formatted_items = []
    for progress_status, user, custom_design, portfolio in results:
        # portfolio가 있으면 portfolio 정보 사용, 없으면 custom_design 정보 사용
        if portfolio:
            item = {
                "id": progress_status.id,
                "user_name": user.contact_name or user.username,
                "image_url": portfolio.main_image_url,
                "type": 1,  # portfolio
                "type_id": portfolio.id,
                "type_name": portfolio.design_name,
                "design_line": get_image_details(portfolio.design_line_image_id),
                "design_line_color": get_color_details(portfolio.design_line_color_id),
                "design_base1": get_image_details(portfolio.design_base1_image_id),
                "design_base1_color": get_color_details(portfolio.design_base1_color_id),
                "design_base2": get_image_details(portfolio.design_base2_image_id),
                "design_base2_color": get_color_details(portfolio.design_base2_color_id),
                "design_pupil": get_image_details(portfolio.design_pupil_image_id),
                "design_pupil_color": get_color_details(portfolio.design_pupil_color_id),
            }
        else:
            item = {
                "id": progress_status.id,
                "user_name": user.contact_name or user.username,
                "image_url": custom_design.main_image_url,
                "type": 0,  # custom_design
                "type_id": custom_design.id,
                "type_name": custom_design.item_name,
                "design_line": get_image_details(custom_design.design_line_image_id),
                "design_line_color": get_color_details(custom_design.design_line_color_id),
                "design_base1": get_image_details(custom_design.design_base1_image_id),
                "design_base1_color": get_color_details(custom_design.design_base1_color_id),
                "design_base2": get_image_details(custom_design.design_base2_image_id),
                "design_base2_color": get_color_details(custom_design.design_base2_color_id),
                "design_pupil": get_image_details(custom_design.design_pupil_image_id),
                "design_pupil_color": get_color_details(custom_design.design_pupil_color_id),
            }

        # 공통 필드 추가
        item.update({
            "status": progress_status.status,
            "notes": progress_status.notes,
            "created_at": progress_status.created_at,
            "updated_at": progress_status.updated_at
        })

        formatted_items.append(item)

    return {"items": formatted_items, "total_count": total_count}