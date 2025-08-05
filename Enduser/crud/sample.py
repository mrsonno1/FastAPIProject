from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from db import models
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date


def get_samples_paginated(
        db: Session,
        user_id: str,
        page: int = 1,
        size: int = 10,
        orderBy: Optional[str] = None
) -> Dict[str, Any]:
    """사용자의 샘플 요청(progressstatus) 목록을 페이지네이션하여 조회"""

    # AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id
    ).first()

    if not user:
        return {"total_count": 0, "items": []}

    # progressstatus 조회
    query = db.query(
        models.Progressstatus,
        models.CustomDesign,
        models.Portfolio
    ).filter(
        models.Progressstatus.user_id == user.id
    ).outerjoin(
        models.CustomDesign,
        models.Progressstatus.custom_design_id == models.CustomDesign.id
    ).outerjoin(
        models.Portfolio,
        models.Progressstatus.portfolio_id == models.Portfolio.id
    )

    # 전체 카운트
    total_count = query.count()

    # 정렬
    if orderBy == "oldest":
        query = query.order_by(models.Progressstatus.created_at.asc())
    else:
        # 기본값: 최신순
        query = query.order_by(models.Progressstatus.created_at.desc())

    # 페이지네이션
    offset = (page - 1) * size
    results = query.offset(offset).limit(size).all()

    # 결과 포맷팅
    formatted_items = []
    for progress_status, custom_design, portfolio in results:
        # 카테고리 및 아이템 정보 결정
        if portfolio:
            item_name = portfolio.design_name
            main_image_url = portfolio.main_image_url
            thumbnail_url = portfolio.thumbnail_url
            category = '포트폴리오'
            design_obj = portfolio
        elif custom_design:
            item_name = custom_design.item_name
            main_image_url = custom_design.main_image_url
            thumbnail_url = custom_design.thumbnail_url
            category = '커스텀디자인'
            design_obj = custom_design
        else:
            continue

        # 디자인 컴포넌트 정보 조회
        design_components = get_design_components(db, design_obj, category)

        # 상태 매핑 (0: 대기, 1: 진행중, 2: 지연, 3: 배송완료)
        status_map = {'0': '대기', '1': '진행중', '2': '지연', '3': '발송완료'}
        status_text = status_map.get(progress_status.status, progress_status.status)

        # shipped_date는 status가 '3'일 때만
        shipped_date = None
        if progress_status.status == '3' and hasattr(progress_status, 'updated_at'):
            shipped_date = progress_status.updated_at
        
        # account_code 설정
        account_code = None
        if category == '커스텀디자인':
            # 커스텀디자인인 경우 현재 로그인한 사용자의 account_code
            account_code = user.account_code if user else None
        elif category == '포트폴리오' and portfolio:
            # 포트폴리오인 경우 portfolio의 user_id로 account_code 조회
            portfolio_user = db.query(models.AdminUser).filter(
                models.AdminUser.id == portfolio.user_id
            ).first()
            account_code = portfolio_user.account_code if portfolio_user else None

        formatted_items.append({
            "id": progress_status.id,
            "item_name": item_name,
            "main_image_url": main_image_url,
            "thumbnail_url": thumbnail_url,
            "category": category,
            "design_line": design_components.get("design_line"),
            "design_base1": design_components.get("design_base1"),
            "design_base2": design_components.get("design_base2"),
            "design_pupil": design_components.get("design_pupil"),
            "graphic_diameter": design_obj.graphic_diameter if design_obj else None,
            "optic_zone": design_obj.optic_zone if design_obj else None,
            "dia": design_obj.dia if design_obj else None,
            "created_at": progress_status.created_at,
            "estimated_ship_date": progress_status.expected_shipping_date,
            "status": status_text,
            "shipped_date": shipped_date,
            "request_note": progress_status.notes,
            "account_code": account_code
        })

    return {
        "total_count": total_count,
        "items": formatted_items
    }


def get_sample_detail(db: Session, user_id: str, progress_id: int) -> Optional[Dict[str, Any]]:
    """샘플 요청(progressstatus) 항목의 상세 정보 조회"""

    # AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id
    ).first()

    if not user:
        return None

    progress_status = db.query(models.Progressstatus).filter(
        and_(
            models.Progressstatus.user_id == user.id,
            models.Progressstatus.id == progress_id
        )
    ).first()

    if not progress_status:
        return None

    # tracking_number는 status_note에서 가져옴
    tracking_number = None
    if progress_status.status == '3' and progress_status.status_note:
        # status_note에서 송장번호 추출 (예: "송장번호: 123456789")
        tracking_number = progress_status.status_note

    return {
        "recipient_name": progress_status.client_name,
        "recipient_phone": progress_status.number,
        "recipient_address": progress_status.address,
        "tracking_number": tracking_number,
        "request_note": progress_status.notes
    }


def delete_sample(db: Session, user_id: str, progress_id: int) -> bool:
    """샘플 요청(progressstatus) 항목 삭제 (대기 상태만 가능)"""

    # AdminUser의 id 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id
    ).first()

    if not user:
        return False

    progress_status = db.query(models.Progressstatus).filter(
        and_(
            models.Progressstatus.user_id == user.id,
            models.Progressstatus.id == progress_id
        )
    ).first()

    if not progress_status:
        return False

    # 대기 상태가 아니면 삭제 불가
    if progress_status.status != '0':
        return False

    db.delete(progress_status)
    db.commit()

    return True


def create_progress_status_from_cart(
        db: Session,
        user_id: str,
        item_name: str,
        category: str,
        client_name: str,
        number: str,
        address: str,
        request_note: Optional[str] = None
) -> bool:
    """장바구니 아이템으로부터 progress_status 생성"""

    # 장바구니에서 아이템 찾기
    cart_item = db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.item_name == item_name,
            models.Cart.category == category
        )
    ).first()

    if not cart_item:
        return False

    # 사용자 정보 조회
    user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id
    ).first()

    if not user:
        return False

    # custom_design_id 또는 portfolio_id 찾기
    custom_design_id = None
    portfolio_id = None

    if category == '커스텀디자인':
        custom_design = db.query(models.CustomDesign).filter(
            models.CustomDesign.item_name == item_name,
            models.CustomDesign.user_id == user_id
        ).first()

        if custom_design:
            custom_design_id = custom_design.id
            # Case 122: 커스텀 디자인의 완료 시 저장된 요청사항 사용
            final_request_note = custom_design.request_message or request_note or f"{category} 샘플 제작 요청"
        else:
            final_request_note = request_note or f"{category} 샘플 제작 요청"
    else:  # 포트폴리오
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.design_name == item_name,
            models.Portfolio.is_deleted == False
        ).first()

        if portfolio:
            portfolio_id = portfolio.id
        final_request_note = request_note or f"{category} 샘플 제작 요청"

    # progress_status 생성
    progress_status = models.Progressstatus(
        user_id=user.id,  # AdminUser의 id
        custom_design_id=custom_design_id,
        portfolio_id=portfolio_id,
        status='0',  # 대기 상태
        notes=final_request_note,  # 커스텀 디자인의 경우 완료 시의 요청사항 사용
        client_name=client_name,
        number=number,
        address=address,
        request_date=datetime.now(),
        expected_shipping_date=datetime.now().date() + timedelta(days=10)
    )

    db.add(progress_status)

    # 장바구니에서 제거
    db.delete(cart_item)

    db.commit()

    return True


# Enduser/crud/sample.py (get_design_components 함수 부분만)
def get_design_components(db: Session, design_obj: Any, category: str) -> Dict[str, Any]:
    """디자인 컴포넌트 정보 조회"""

    def get_component_info(image_id: str, color_id: str, transparency: Optional[str] = None,
                           size: Optional[str] = None):
        if not image_id or not color_id:
            return None

        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        color = db.query(models.Color).filter(models.Color.id == color_id).first()

        if not image or not color:
            return None

        # 커스텀디자인이면 투명도와 크기 사용, 포트폴리오면 100 고정
        opacity = 100
        component_size = 100

        if category == '커스텀디자인':
            if transparency:
                try:
                    opacity = int(transparency)
                except (ValueError, TypeError):
                    opacity = 100
            if size:
                try:
                    component_size = int(size)
                except (ValueError, TypeError):
                    component_size = 100

        return {
            "image_id": image_id,
            "image_url": image.public_url,
            "image_name": image.display_name,
            "RGB_id": color_id,
            "RGB_color": color.color_values,
            "RGB_name": color.color_name,
            "size": component_size,
            "opacity": opacity
        }

    return {
        "design_line": get_component_info(
            design_obj.design_line_image_id if hasattr(design_obj, 'design_line_image_id') else None,
            design_obj.design_line_color_id if hasattr(design_obj, 'design_line_color_id') else None,
            design_obj.line_transparency if hasattr(design_obj, 'line_transparency') else None,
            design_obj.line_size if hasattr(design_obj, 'line_size') else None
        ),
        "design_base1": get_component_info(
            design_obj.design_base1_image_id if hasattr(design_obj, 'design_base1_image_id') else None,
            design_obj.design_base1_color_id if hasattr(design_obj, 'design_base1_color_id') else None,
            design_obj.base1_transparency if hasattr(design_obj, 'base1_transparency') else None,
            design_obj.base1_size if hasattr(design_obj, 'base1_size') else None
        ),
        "design_base2": get_component_info(
            design_obj.design_base2_image_id if hasattr(design_obj, 'design_base2_image_id') else None,
            design_obj.design_base2_color_id if hasattr(design_obj, 'design_base2_color_id') else None,
            design_obj.base2_transparency if hasattr(design_obj, 'base2_transparency') else None,
            design_obj.base2_size if hasattr(design_obj, 'base2_size') else None
        ),
        "design_pupil": get_component_info(
            design_obj.design_pupil_image_id if hasattr(design_obj, 'design_pupil_image_id') else None,
            design_obj.design_pupil_color_id if hasattr(design_obj, 'design_pupil_color_id') else None,
            design_obj.pupil_transparency if hasattr(design_obj, 'pupil_transparency') else None,
            design_obj.pupil_size if hasattr(design_obj, 'pupil_size') else None
        )
    }