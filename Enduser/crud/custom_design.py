# Enduser/crud/custom_design.py
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db import models
from typing import Optional, Dict, Any
import math
from services.storage_service import storage_service
from fastapi import UploadFile


def get_images_paginated(
        db: Session,
        user_id: int,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        display_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """이미지 목록을 페이지네이션하여 조회"""

    query = db.query(models.Image)
    
    # exposed_users 필터링
    # exposed_users가 비어있거나 현재 사용자 ID가 포함된 이미지만 조회
    query = query.filter(
        or_(
            models.Image.exposed_users == None,  # exposed_users가 NULL인 경우
            models.Image.exposed_users == '',     # exposed_users가 빈 문자열인 경우
            models.Image.exposed_users.like(f'%{user_id}%')  # 현재 사용자 ID가 포함된 경우
        )
    )

    # 필터링
    if category:
        query = query.filter(models.Image.category == category)
    if display_name:
        query = query.filter(models.Image.display_name.contains(display_name))

    # 정렬
    if orderBy:
        from sqlalchemy import cast, Integer
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if column == 'display_name':
                # display_name이 숫자로만 이루어진 경우 숫자로 변환하여 정렬
                query = query.order_by(cast(models.Image.display_name, Integer).desc())
            elif hasattr(models.Image, column):
                query = query.order_by(getattr(models.Image, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if column == 'display_name':
                # display_name이 숫자로만 이루어진 경우 숫자로 변환하여 정렬
                query = query.order_by(cast(models.Image.display_name, Integer).asc())
            elif hasattr(models.Image, column):
                query = query.order_by(getattr(models.Image, column).asc())
    else:
        query = query.order_by(models.Image.uploaded_at.desc())

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_colors_paginated(
        db: Session,
        page: int = 1,
        size: int = 10,
        color_name: Optional[str] = None,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """색상 목록을 페이지네이션하여 조회"""

    query = db.query(models.Color)

    # 필터링
    if color_name:
        query = query.filter(models.Color.color_name.contains(color_name))

    # 정렬
    if orderBy:
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if hasattr(models.Color, column):
                query = query.order_by(getattr(models.Color, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if hasattr(models.Color, column):
                query = query.order_by(getattr(models.Color, column).asc())
    else:
        query = query.order_by(models.Color.updated_at.desc())

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_custom_design_detail(db: Session, design_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """커스텀 디자인 상세 정보 조회"""
    
    # username으로 AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id,
        models.AdminUser.is_deleted == False
    ).first()
    
    if not user:
        return None

    # user_id가 username(문자열) 또는 id(숫자 문자열)일 수 있으므로 둘 다 확인
    design = db.query(models.CustomDesign).filter(
        models.CustomDesign.id == design_id,
        or_(
            models.CustomDesign.user_id == str(user.id),  # 새로운 형식: id를 문자열로
            models.CustomDesign.user_id == user.username   # 오래된 형식: username
        )
    ).first()

    if not design:
        return None

    # 각 컴포넌트 정보 조회
    def get_component_info(image_id: str, color_id: str, transparency: str, size: str):
        if not image_id or not color_id:
            return None

        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        color = db.query(models.Color).filter(models.Color.id == color_id).first()

        if not image or not color:
            return None

        return {
            "image_id": image_id,
            "image_url": image.public_url,
            "image_name": image.display_name,
            "RGB_id": color_id,
            "RGB_color": color.color_values,
            "RGB_name": color.color_name,
            "size": int(size) if size else 100,
            "opacity": int(transparency) if transparency else 100
        }

    return {
        "item_name": design.item_name,
        "design_line": get_component_info(
            design.design_line_image_id,
            design.design_line_color_id,
            design.line_transparency,
            design.line_size
        ),
        "design_base1": get_component_info(
            design.design_base1_image_id,
            design.design_base1_color_id,
            design.base1_transparency,
            design.base1_size
        ),
        "design_base2": get_component_info(
            design.design_base2_image_id,
            design.design_base2_color_id,
            design.base2_transparency,
            design.base2_size
        ),
        "design_pupil": get_component_info(
            design.design_pupil_image_id,
            design.design_pupil_color_id,
            design.pupil_transparency,
            design.pupil_size
        ),
        "graphic_diameter": design.graphic_diameter,
        "optic_zone": design.optic_zone,
        "dia": design.dia
    }


def create_custom_design(
        db: Session,
        form_data: Dict[str, Any],
        user_id: str,
        main_image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None
) -> models.CustomDesign:
    """커스텀 디자인 생성 - Form 데이터와 업로드된 이미지 URL 방식"""
    
    # username으로 AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id,
        models.AdminUser.is_deleted == False
    ).first()
    
    if not user:
        raise ValueError(f"User not found: {user_id}")

    # 커스텀 디자인 생성
    # 프로덕션 DB는 user_id가 varchar(20)이므로 문자열로 변환
    db_design = models.CustomDesign(
        user_id=str(user.id),  # 문자열로 변환하여 프로덕션 DB와 호환
        item_name=form_data.get("item_name"),  # NULL 허용, get 메서드 사용으로 KeyError 방지
        main_image_url=main_image_url,  # 이미 업로드된 URL 직접 사용
        thumbnail_url=thumbnail_url,  # 썸네일 URL
        request_message=form_data.get("request_message"),
        design_line_image_id=form_data.get("design_line_image_id"),
        design_line_color_id=form_data.get("design_line_color_id"),
        design_base1_image_id=form_data.get("design_base1_image_id"),
        design_base1_color_id=form_data.get("design_base1_color_id"),
        design_base2_image_id=form_data.get("design_base2_image_id"),
        design_base2_color_id=form_data.get("design_base2_color_id"),
        design_pupil_image_id=form_data.get("design_pupil_image_id"),
        design_pupil_color_id=form_data.get("design_pupil_color_id"),
        line_transparency=form_data.get("line_transparency", "100"),
        base1_transparency=form_data.get("base1_transparency", "100"),
        base2_transparency=form_data.get("base2_transparency", "100"),
        pupil_transparency=form_data.get("pupil_transparency", "100"),
        line_size=form_data.get("line_size", "100"),
        base1_size=form_data.get("base1_size", "100"),
        base2_size=form_data.get("base2_size", "100"),
        pupil_size=form_data.get("pupil_size", "100"),
        graphic_diameter=form_data.get("graphic_diameter"),
        optic_zone=form_data.get("optic_zone"),
        dia=form_data.get("dia"),
        status="0"  # 기본값 '0' (대기) 상태로 설정
    )

    db.add(db_design)
    db.commit()
    db.refresh(db_design)

    return db_design



def get_user_custom_designs_paginated(
        db: Session,
        user_id: str,
        page: int = 1,
        size: int = 10,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """사용자의 커스텀 디자인 목록을 페이지네이션하여 조회"""
    
    # username으로 AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id,
        models.AdminUser.is_deleted == False
    ).first()
    
    if not user:
        return {"total_count": 0, "items": []}

    # user_id가 username 또는 id일 수 있으므로 둘 다 확인
    query = db.query(models.CustomDesign).filter(
        or_(
            models.CustomDesign.user_id == str(user.id),  # 새로운 형식
            models.CustomDesign.user_id == user.username   # 오래된 형식
        )
    )

    # 정렬
    if orderBy:
        if orderBy.lower().endswith(' desc'):
            column = orderBy.replace(' desc', '').strip()
            if hasattr(models.CustomDesign, column):
                query = query.order_by(getattr(models.CustomDesign, column).desc())
        elif orderBy.lower().endswith(' asc'):
            column = orderBy.replace(' asc', '').strip()
            if hasattr(models.CustomDesign, column):
                query = query.order_by(getattr(models.CustomDesign, column).asc())
    else:
        # 기본 정렬: status가 3인 경우를 우선으로 정렬
        # status 3: updated_at 내림차순
        # 나머지: created_at 내림차순
        from sqlalchemy import case
        query = query.order_by(
            case(
                (models.CustomDesign.status == '3', 0),
                else_=1
            ),
            case(
                (models.CustomDesign.status == '3', models.CustomDesign.updated_at),
                else_=None
            ).desc(),
            models.CustomDesign.created_at.desc()
        )

    # 전체 카운트
    total_count = query.count()

    # 페이지네이션
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return {
        "total_count": total_count,
        "items": items
    }


def get_design_by_id(db: Session, design_id: int, user_id: str) -> Optional[models.CustomDesign]:
    """ID로 커스텀 디자인 조회 (사용자 본인의 디자인만)"""
    
    # username으로 AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id,
        models.AdminUser.is_deleted == False
    ).first()
    
    if not user:
        return None
    
    # user_id가 username 또는 id일 수 있으므로 둘 다 확인
    return db.query(models.CustomDesign).filter(
        models.CustomDesign.id == design_id,
        or_(
            models.CustomDesign.user_id == str(user.id),  # 새로운 형식
            models.CustomDesign.user_id == user.username   # 오래된 형식
        )
    ).first()


def update_design_status(db: Session, design_id: int, user_id: str, status: str) -> Optional[models.CustomDesign]:
    """커스텀 디자인 상태 업데이트 - status가 3일 때 item_name 자동 생성"""
    
    # 디자인 조회
    db_design = get_design_by_id(db, design_id, user_id)
    if not db_design:
        return None
    
    # 기존 상태 저장
    old_status = db_design.status
    
    # 상태가 '3'(완료)로 변경되고 item_name이 없는 경우 코드 생성
    if status == '3' and (db_design.item_name is None or db_design.item_name == ''):
        # 사용자 정보 조회
        user = db.query(models.AdminUser).filter(
            models.AdminUser.username == user_id,
            models.AdminUser.is_deleted == False
        ).first()
        if user and user.account_code:
            # 해당 계정의 커스텀 디자인 중 마지막 순번 찾기
            # item_name이 숫자로만 이루어진 것들 중에서 찾기
            # user_id가 username 또는 id일 수 있으므로 둘 다 확인
            last_design = db.query(models.CustomDesign).filter(
                or_(
                    models.CustomDesign.user_id == str(user.id),  # 새로운 형식
                    models.CustomDesign.user_id == user.username   # 오래된 형식
                ),
                models.CustomDesign.item_name != None,
                models.CustomDesign.item_name.op('~')('^[0-9]+$')  # 숫자만으로 이루어진 item_name
            ).order_by(models.CustomDesign.id.desc()).first()
            
            if last_design and last_design.item_name:
                # 마지막 번호에서 다음 번호 계산
                try:
                    last_number = int(last_design.item_name)
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            # 새 코드 생성 (숫자만)
            new_code = str(next_number).zfill(4)
            db_design.item_name = new_code
    
    # 상태 업데이트
    db_design.status = status
    
    db.commit()
    db.refresh(db_design)
    
    return db_design