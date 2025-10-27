from sqlalchemy.orm import Session
from sqlalchemy import and_
from db import models
from typing import Optional, List, Dict, Any
from datetime import datetime


def get_cart_count(db: Session, user_id: str) -> int:
    """사용자의 장바구니에 담긴 상품 개수 조회"""
    return db.query(models.Cart).filter(
        models.Cart.user_id == user_id
    ).count()


def get_cart_count_by_category(db: Session, user_id: str, category: str) -> int:
    """사용자의 카테고리별 장바구니 개수 조회"""
    return db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.category == category
        )
    ).count()


def get_cart_items(
        db: Session,
        user_id: str,
        category: Optional[str] = None,
        orderBy: Optional[str] = None
) -> List[Dict[str, Any]]:
    """사용자의 장바구니 목록 조회 (최대 40개)"""

    query = db.query(models.Cart).filter(
        models.Cart.user_id == user_id
    )

    # 카테고리 필터링
    if category:
        query = query.filter(models.Cart.category == category)

    # 정렬
    if orderBy == "oldest":
        query = query.order_by(models.Cart.created_at.asc())
    else:
        # 기본값: 최신순
        query = query.order_by(models.Cart.created_at.desc())

    # 최대 40개 제한
    cart_items = query.limit(40).all()
    
    # 현재 사용자 정보 조회 (삭제되지 않은 사용자만)
    current_user = db.query(models.AdminUser).filter(
        models.AdminUser.username == user_id,
        models.AdminUser.is_deleted == False
    ).first()
    
    # 결과 포맷팅
    formatted_items = []
    for item in cart_items:
        account_code = None
        thumbnail_url = None
        portfolio_id = None
        custom_design_id = None

        if item.category == '커스텀디자인':
            # 커스텀디자인인 경우 현재 로그인한 사용자의 account_code
            account_code = current_user.account_code if current_user else None

            # 커스텀디자인에서 썸네일 URL 가져오기
            custom_design = db.query(models.CustomDesign).filter(
                models.CustomDesign.item_name == item.item_name,
                models.CustomDesign.user_id == user_id
            ).first()

            if custom_design:
                thumbnail_url = custom_design.thumbnail_url
                custom_design_id = custom_design.id

        elif item.category == '포트폴리오':
            # 포트폴리오인 경우 portfolio의 user_id로 account_code 조회
            portfolio = db.query(models.Portfolio).filter(
                models.Portfolio.design_name == item.item_name,
                models.Portfolio.is_deleted == False
            ).first()

            if portfolio:
                thumbnail_url = portfolio.thumbnail_url
                portfolio_id = portfolio.id
                portfolio_user = db.query(models.AdminUser).filter(
                    models.AdminUser.id == portfolio.user_id,
                    models.AdminUser.is_deleted == False
                ).first()
                account_code = portfolio_user.account_code if portfolio_user else None

        formatted_items.append({
            "item_name": item.item_name,
            "main_image_url": item.main_image_url,
            "thumbnail_url": thumbnail_url,
            "category": item.category,
            "account_code": account_code,
            "portfolio_id": portfolio_id,
            "custom_design_id": custom_design_id
        })
    
    return formatted_items


def add_to_cart(
        db: Session,
        user_id: str,
        item_name: str,
        main_image_url: Optional[str],
        category: str
) -> models.Cart:
    """장바구니에 상품 추가 (카테고리별 최대 20개 제한)"""

    # 이미 장바구니에 있는지 확인
    existing_item = db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.item_name == item_name,
            models.Cart.category == category
        )
    ).first()

    if existing_item:
        # 이미 존재하면 업데이트만 수행 (이미지 URL이 변경되었을 수 있음)
        existing_item.main_image_url = main_image_url
        db.commit()
        db.refresh(existing_item)
        return existing_item

    # 해당 카테고리의 현재 개수 확인
    category_count = db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.category == category
        )
    ).count()

    # 카테고리별 20개 제한
    if category_count >= 20:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"{category} 카테고리는 최대 20개까지만 장바구니에 담을 수 있습니다."
        )

    # 새로 추가
    new_cart_item = models.Cart(
        user_id=user_id,
        item_name=item_name,
        main_image_url=main_image_url,
        category=category
    )

    db.add(new_cart_item)
    db.commit()
    db.refresh(new_cart_item)

    return new_cart_item


def delete_cart_item(
        db: Session,
        user_id: str,
        item_name: str,
        category: str
) -> bool:
    """장바구니에서 단일 상품 삭제"""

    cart_item = db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.item_name == item_name,
            models.Cart.category == category
        )
    ).first()

    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True

    return False


def delete_cart_by_category(
        db: Session,
        user_id: str,
        category: str
) -> int:
    """장바구니에서 카테고리별 일괄 삭제"""

    deleted_count = db.query(models.Cart).filter(
        and_(
            models.Cart.user_id == user_id,
            models.Cart.category == category
        )
    ).delete()

    db.commit()

    return deleted_count


def add_to_cart_by_id(
        db: Session,
        user_id: str,
        portfolio_id: Optional[int] = None,
        custom_design_id: Optional[int] = None,
        main_image_url: Optional[str] = None
) -> models.Cart:
    """ID 기반 장바구니 추가 (카테고리별 최대 20개 제한)"""

    if not portfolio_id and not custom_design_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="portfolio_id 또는 custom_design_id 중 하나는 필수입니다."
        )

    if portfolio_id and custom_design_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="portfolio_id와 custom_design_id는 동시에 지정할 수 없습니다."
        )

    # 포트폴리오 또는 커스텀디자인 조회
    if portfolio_id:
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.id == portfolio_id,
            models.Portfolio.is_deleted == False
        ).first()

        if not portfolio:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

        item_name = portfolio.design_name
        category = '포트폴리오'
        if not main_image_url:
            main_image_url = portfolio.main_image_url
    else:
        custom_design = db.query(models.CustomDesign).filter(
            models.CustomDesign.id == custom_design_id,
            models.CustomDesign.user_id == user_id,
            models.CustomDesign.status == "3"
        ).first()

        if not custom_design:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="커스텀디자인을 찾을 수 없습니다.")

        item_name = custom_design.item_name
        category = '커스텀디자인'
        if not main_image_url:
            main_image_url = custom_design.main_image_url

    # 기존 add_to_cart 함수 재사용
    return add_to_cart(
        db=db,
        user_id=user_id,
        item_name=item_name,
        main_image_url=main_image_url,
        category=category
    )


def delete_cart_item_by_id(
        db: Session,
        user_id: str,
        portfolio_id: Optional[int] = None,
        custom_design_id: Optional[int] = None
) -> bool:
    """ID 기반 장바구니 단일 삭제"""

    if not portfolio_id and not custom_design_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="portfolio_id 또는 custom_design_id 중 하나는 필수입니다."
        )

    if portfolio_id and custom_design_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="portfolio_id와 custom_design_id는 동시에 지정할 수 없습니다."
        )

    # 포트폴리오 또는 커스텀디자인 조회
    if portfolio_id:
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.id == portfolio_id,
            models.Portfolio.is_deleted == False
        ).first()

        if not portfolio:
            return False

        item_name = portfolio.design_name
        category = '포트폴리오'
    else:
        custom_design = db.query(models.CustomDesign).filter(
            models.CustomDesign.id == custom_design_id,
            models.CustomDesign.user_id == user_id
        ).first()

        if not custom_design:
            return False

        item_name = custom_design.item_name
        category = '커스텀디자인'

    # 기존 delete_cart_item 함수 재사용
    return delete_cart_item(
        db=db,
        user_id=user_id,
        item_name=item_name,
        category=category
    )