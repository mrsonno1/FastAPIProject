# progress_status/crud/progress_status.py
from sqlalchemy.orm import Session
from db import models
from datetime import timedelta, date
from Manager.progress_status.schemas import progress_status as progress_status_schema
from typing import Optional
from sqlalchemy import or_

def create_progress_status(
        db: Session,
        progress_status: progress_status_schema.ProgressStatusCreate
):
    # ID 값이 0이면 DB 저장을 위해 None으로 변환
    final_custom_design_id = progress_status.custom_design_id if progress_status.custom_design_id != 0 else None
    final_portfolio_id = progress_status.portfolio_id if progress_status.portfolio_id is not None and progress_status.portfolio_id != 0 else None


    db_progress_status = models.Progressstatus(
        user_id=progress_status.user_id,
        custom_design_id=final_custom_design_id,  # 0일 경우 None으로 변환된 값을 전달
        portfolio_id=final_portfolio_id,  # 0일 경우 None으로 변환된 값을 전달
        status=progress_status.status,
        notes=progress_status.notes,
        client_name=progress_status.client_name,
        number=progress_status.number,
        address=progress_status.address,
        status_note=progress_status.status_note,
    )
    db.add(db_progress_status)
    db.commit()
    db.refresh(db_progress_status)


    if db_progress_status.request_date:
        calculated_date = db_progress_status.request_date + timedelta(days=10)
        db_progress_status.expected_shipping_date = calculated_date.date()
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

def process_component_details(db, result, design_obj):
    """디자인 객체(Portfolio 또는 CustomDesign)에서 컴포넌트 세부 정보를 추출하여 결과에 추가합니다."""

    # 커스텀 디자인인지 확인
    is_custom_design = isinstance(design_obj, models.CustomDesign)

    # 디자인 라인 정보
    if hasattr(design_obj, 'design_line_image_id') and design_obj.design_line_image_id:
        design_line = db.query(models.Image).filter(models.Image.id == design_obj.design_line_image_id).first()
        if design_line:
            line_data = {
                'id': design_line.id,
                'display_name': design_line.display_name,
                'public_url': design_line.public_url,
            }

            # 커스텀 디자인이면 투명도 정보 추가
            if is_custom_design and hasattr(design_obj, 'line_transparency') and design_obj.line_transparency:
                try:
                    line_data['opacity'] = int(design_obj.line_transparency)
                except (ValueError, TypeError):
                    pass

            result['design_line'] = line_data
    else:
        result['design_line'] = None

    # 디자인 라인 컬러 정보
    if hasattr(design_obj, 'design_line_color_id') and design_obj.design_line_color_id:
        design_line_color = db.query(models.Color).filter(models.Color.id == design_obj.design_line_color_id).first()
        if design_line_color:
            result['design_line_color'] = {
                'id': design_line_color.id,
                'color_name': design_line_color.color_name,
                'color_values': design_line_color.color_values
            }
    else:
        result['design_line_color'] = None

    # 디자인 base1 정보
    if hasattr(design_obj, 'design_base1_image_id') and design_obj.design_base1_image_id:
        design_base1 = db.query(models.Image).filter(models.Image.id == design_obj.design_base1_image_id).first()
        if design_base1:
            base1_data = {
                'id': design_base1.id,
                'display_name': design_base1.display_name,
                'public_url': design_base1.public_url
            }

            # 커스텀 디자인이면 투명도 정보 추가
            if is_custom_design and hasattr(design_obj, 'base1_transparency') and design_obj.base1_transparency:
                try:
                    base1_data['opacity'] = int(design_obj.base1_transparency)
                except (ValueError, TypeError):
                    pass

            result['design_base1'] = base1_data
    else:
        result['design_base1'] = None

    # 디자인 base1 컬러 정보
    if hasattr(design_obj, 'design_base1_color_id') and design_obj.design_base1_color_id:
        design_base1_color = db.query(models.Color).filter(models.Color.id == design_obj.design_base1_color_id).first()
        if design_base1_color:
            result['design_base1_color'] = {
                'id': design_base1_color.id,
                'color_name': design_base1_color.color_name,
                'color_values': design_base1_color.color_values
            }
    else:
        result['design_base1_color'] = None

    # 디자인 base2 정보
    if hasattr(design_obj, 'design_base2_image_id') and design_obj.design_base2_image_id:
        design_base2 = db.query(models.Image).filter(models.Image.id == design_obj.design_base2_image_id).first()
        if design_base2:
            base2_data = {
                'id': design_base2.id,
                'display_name': design_base2.display_name,
                'public_url': design_base2.public_url
            }

            # 커스텀 디자인이면 투명도 정보 추가
            if is_custom_design and hasattr(design_obj, 'base2_transparency') and design_obj.base2_transparency:
                try:
                    base2_data['opacity'] = int(design_obj.base2_transparency)
                except (ValueError, TypeError):
                    pass

            result['design_base2'] = base2_data
    else:
        result['design_base2'] = None

    # 디자인 base2 컬러 정보
    if hasattr(design_obj, 'design_base2_color_id') and design_obj.design_base2_color_id:
        design_base2_color = db.query(models.Color).filter(models.Color.id == design_obj.design_base2_color_id).first()
        if design_base2_color:
            result['design_base2_color'] = {
                'id': design_base2_color.id,
                'color_name': design_base2_color.color_name,
                'color_values': design_base2_color.color_values
            }
    else:
        result['design_base2_color'] = None

    # 디자인 pupil 정보
    if hasattr(design_obj, 'design_pupil_image_id') and design_obj.design_pupil_image_id:
        design_pupil = db.query(models.Image).filter(models.Image.id == design_obj.design_pupil_image_id).first()
        if design_pupil:
            pupil_data = {
                'id': design_pupil.id,
                'display_name': design_pupil.display_name,
                'public_url': design_pupil.public_url,
            }

            # 커스텀 디자인이면 투명도 정보 추가
            if is_custom_design and hasattr(design_obj, 'pupil_transparency') and design_obj.pupil_transparency:
                try:
                    pupil_data['opacity'] = int(design_obj.pupil_transparency)
                except (ValueError, TypeError):
                    pass

            result['design_pupil'] = pupil_data
    else:
        result['design_pupil'] = None

    # 디자인 pupil 컬러 정보
    if hasattr(design_obj, 'design_pupil_color_id') and design_obj.design_pupil_color_id:
        design_pupil_color = db.query(models.Color).filter(models.Color.id == design_obj.design_pupil_color_id).first()
        if design_pupil_color:
            result['design_pupil_color'] = {
                'id': design_pupil_color.id,
                'color_name': design_pupil_color.color_name,
                'color_values': design_pupil_color.color_values
            }
    else:
        result['design_pupil_color'] = None


def get_progress_status_detail(db: Session, progress_status_id: int):
    """ID로 단일 진행 상태의 상세 정보를 조회합니다."""
    progress_status = get_progress_status_by_id(db, progress_status_id)
    if not progress_status:
        return None

    # 상세 정보 구성
    result = {}
    result['id'] = progress_status.id
    result['status'] = progress_status.status
    result['notes'] = progress_status.notes
    result['request_date'] = progress_status.created_at

    # progress_status 테이블에서 직접 가져오는 필드들
    result['client_name'] = progress_status.client_name
    result['number'] = progress_status.number
    result['address'] = progress_status.address
    result['status_note'] = progress_status.status_note


    # 사용자 정보 조회
    user = db.query(models.AdminUser).filter(models.AdminUser.id == progress_status.user_id).first()
    if user:
        result['user_name'] = user.username
    else:
        result['user_name'] = "Unknown"

    # 예상 배송일
    if hasattr(progress_status, 'expected_shipping_date') and progress_status.expected_shipping_date:
        result['expected_shipping_date'] = progress_status.expected_shipping_date
    else:
        from datetime import timedelta
        # 날짜 처리 수정 - 시간 정보 유지
        shipping_date = progress_status.created_at + timedelta(days=10)
        result['expected_shipping_date'] = shipping_date.date()

    # 타입 및 관련 데이터 처리
    if progress_status.portfolio_id:
        # 포트폴리오 타입(1)
        result['type'] = 1
        result['type_id'] = progress_status.portfolio_id

        portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == progress_status.portfolio_id).first()
        if portfolio:
            result['type_name'] = portfolio.design_name
            result['image_url'] = portfolio.main_image_url
            result['graphic_diameter'] = portfolio.graphic_diameter
            result['optic_zone'] = portfolio.optic_zone
            # 디자인 정보 구성
            process_component_details(db, result, portfolio)

    elif progress_status.custom_design_id:
        # 커스텀 디자인 타입(0)
        result['type'] = 0
        result['type_id'] = progress_status.custom_design_id

        custom_design = db.query(models.CustomDesign).filter(models.CustomDesign.id == progress_status.custom_design_id).first()
        if custom_design:
            result['type_name'] = custom_design.item_name
            result['image_url'] = custom_design.main_image_url
            result['graphic_diameter'] = custom_design.graphic_diameter
            result['optic_zone'] = custom_design.optic_zone
            # 디자인 정보 구성
            process_component_details(db, result, custom_design)

    return result


def get_progress_status_paginated(
        db: Session,
        page: int,
        size: int,
        user_name: Optional[str] = None,
        custom_design_name: Optional[str] = None,
        type: Optional[int] = None,
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
    ).outerjoin(
        models.CustomDesign, models.Progressstatus.custom_design_id == models.CustomDesign.id
    ).outerjoin(
        models.Portfolio, models.Progressstatus.portfolio_id == models.Portfolio.id
    )

    # 필터링 적용
    if user_name:
        query = query.filter(
            (models.AdminUser.username.ilike(f"%{user_name}%")) |
            (models.AdminUser.contact_name.ilike(f"%{user_name}%"))
        )

    if custom_design_name:
        if type is None:
            query = query.filter(
                or_(
                    models.CustomDesign.item_name.ilike(f"%{custom_design_name}%"),
                    models.Portfolio.design_name.ilike(f"%{custom_design_name}%")
                )
            )
        elif type == 0:
            query = query.filter(
                models.CustomDesign.item_name.ilike(f"%{custom_design_name}%")
            )
        elif type == 1:
            query = query.filter(
                models.Portfolio.design_name.ilike(f"%{custom_design_name}%")
            )

    if type is not None:
        if type == 0:  # 커스텀 디자인
            query = query.filter(models.Progressstatus.portfolio_id.is_(None))
        elif type == 1:  # 포트폴리오
            query = query.filter(models.Progressstatus.portfolio_id.isnot(None))

    if status:
        query = query.filter(models.Progressstatus.status == status)

    # 총 개수 계산
    total_count = query.count()

    # 페이지네이션 적용
    offset = (page - 1) * size
    results = query.order_by(
        models.Progressstatus.created_at.desc()
    ).offset(offset).limit(size).all()

    # --- [수정 1] 배송 지연 상태 자동 업데이트 ---
    # 먼저 메모리상에서 지연 상태를 확인하고 DB에 일괄 반영합니다.
    today = date.today()
    needs_commit = False
    for progress_status, user, custom_design, portfolio in results:
        # '대기(0)' 또는 '진행중(1)' 상태만 확인
        if progress_status.status in ['0', '1']:
            if progress_status.expected_shipping_date and today > progress_status.expected_shipping_date:
                progress_status.status = '2'  # '지연' 상태로 변경
                needs_commit = True

    if needs_commit:
        db.commit()

    # N+1 문제 해결을 위한 ID 사전 수집 로직 (기존과 동일)
    all_image_ids = set()
    all_color_ids = set()

    for progress_status, user, custom_design, portfolio in results:
        item_to_process = portfolio if portfolio else custom_design
        if item_to_process:
            image_ids = [
                item_to_process.design_line_image_id, item_to_process.design_base1_image_id,
                item_to_process.design_base2_image_id, item_to_process.design_pupil_image_id
            ]
            color_ids = [
                item_to_process.design_line_color_id, item_to_process.design_base1_color_id,
                item_to_process.design_base2_color_id, item_to_process.design_pupil_color_id
            ]
            all_image_ids.update(filter(None, image_ids))
            all_color_ids.update(filter(None, color_ids))

    # ID를 한 번에 조회하여 딕셔너리로 만듦
    images_map = {str(img.id): img for img in
                  db.query(models.Image).filter(models.Image.id.in_(list(all_image_ids))).all()} if all_image_ids else {}
    colors_map = {str(col.id): col for col in
                  db.query(models.Color).filter(models.Color.id.in_(list(all_color_ids))).all()} if all_color_ids else {}

    # 헬퍼 함수
    def get_image_details(image_id):
        if not image_id: return None
        img = images_map.get(str(image_id))
        return {"id": img.id, "display_name": img.display_name, "public_url": img.public_url} if img else None

    def get_custom_design_image_details(image_id, opacity: Optional[str]):
        details = get_image_details(image_id)
        if details:
            details["opacity"] = opacity
        return details

    def get_color_details(color_id):
        if not color_id: return None
        col = colors_map.get(str(color_id))
        return {"id": col.id, "color_name": col.color_name, "color_values": col.color_values} if col else None

    # --- [수정 2] 결과를 가공하면서 업데이트된 상태를 기준으로 필터링 ---
    formatted_items = []
    for progress_status, user, custom_design, portfolio in results:
        # API 요청 시 status 필터가 있었고, DB 업데이트 후 현재 아이템의 상태가
        # 해당 필터와 일치하지 않으면 최종 결과 목록에서 제외합니다.
        if status and progress_status.status != status:
            continue

        item = {}
        # portfolio가 있으면 portfolio 정보 사용, 없으면 custom_design 정보 사용
        if portfolio:
            item = {
                "type": 1,  # portfolio
                "type_id": portfolio.id,
                "type_name": portfolio.design_name,
                "image_url": portfolio.main_image_url,
                "design_line": get_image_details(portfolio.design_line_image_id),
                "design_line_color": get_color_details(portfolio.design_line_color_id),
                "design_base1": get_image_details(portfolio.design_base1_image_id),
                "design_base1_color": get_color_details(portfolio.design_base1_color_id),
                "design_base2": get_image_details(portfolio.design_base2_image_id),
                "design_base2_color": get_color_details(portfolio.design_base2_color_id),
                "design_pupil": get_image_details(portfolio.design_pupil_image_id),
                "design_pupil_color": get_color_details(portfolio.design_pupil_color_id),
                "graphic_diameter": portfolio.graphic_diameter,
                "optic_zone": portfolio.optic_zone,
            }
        elif custom_design:  # custom_design이 있을 때만 처리
            item = {
                "type": 0,  # custom_design
                "type_id": custom_design.id,
                "type_name": custom_design.item_name,
                "image_url": custom_design.main_image_url,
                "design_line": get_custom_design_image_details(custom_design.design_line_image_id, custom_design.line_transparency),
                "design_line_color": get_color_details(custom_design.design_line_color_id),
                "design_base1": get_custom_design_image_details(custom_design.design_base1_image_id, custom_design.base1_transparency),
                "design_base1_color": get_color_details(custom_design.design_base1_color_id),
                "design_base2": get_custom_design_image_details(custom_design.design_base2_image_id, custom_design.base2_transparency),
                "design_base2_color": get_color_details(custom_design.design_base2_color_id),
                "design_pupil": get_custom_design_image_details(custom_design.design_pupil_image_id, custom_design.pupil_transparency),
                "design_pupil_color": get_color_details(custom_design.design_pupil_color_id),
                "graphic_diameter": custom_design.graphic_diameter,
                "optic_zone": custom_design.optic_zone,
            }
        else:
            continue

        # 공통 필드 추가
        item.update({
            "id": progress_status.id,
            "user_name": user.contact_name or user.username,
            "expected_shipping_date": progress_status.expected_shipping_date,
            "status": progress_status.status,
            "notes": progress_status.notes,
            "created_at": progress_status.created_at,
            "updated_at": progress_status.updated_at
        })
        formatted_items.append(item)

    # total_count는 업데이트 전 기준이지만, 페이지네이션의 일관성을 위해 그대로 반환합니다.
    return {"items": formatted_items, "total_count": total_count}