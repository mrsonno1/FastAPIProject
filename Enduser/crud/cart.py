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


def get_cart_items(
        db: Session,
        user_id: str,
        category: Optional[str] = None,
        orderBy: Optional[str] = None
) -> List[models.Cart]:
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
    return query.limit(40).all()


def add_to_cart(
        db: Session,
        user_id: str,
        item_name: str,
        main_image_url: Optional[str],
        category: str
) -> models.Cart:
    """장바구니에 상품 추가"""

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