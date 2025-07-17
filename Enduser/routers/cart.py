from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import cart as cart_schema
from Enduser.crud import cart as cart_crud

router = APIRouter(tags=["Cart"])


@router.get("/cart/count", response_model=cart_schema.CartCountResponse)
def get_cart_count(
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니(샘플제작요청 담기 목록) 담긴 상품 개수 조회"""

    count = cart_crud.get_cart_count(
        db=db,
        user_id=current_user.username
    )

    return cart_schema.CartCountResponse(count=count)


@router.get("/cart/list", response_model=cart_schema.CartListResponse)
def get_cart_list(
        category: Optional[str] = Query(None, description="카테고리 필터링 (커스텀디자인/포트폴리오)"),
        orderBy: Optional[str] = Query("latest", description="정렬 기준 (latest: 최신순-기본값, oldest: 오래된순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니 목록 조회 (최대 40개)"""

    # 카테고리 검증
    if category and category not in ['커스텀디자인', '포트폴리오']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다."
        )

    items = cart_crud.get_cart_items(
        db=db,
        user_id=current_user.username,
        category=category,
        orderBy=orderBy
    )

    cart_items = [
        cart_schema.CartItem(
            item_name=item.item_name,
            main_image_url=item.main_image_url
        )
        for item in items
    ]

    return cart_schema.CartListResponse(items=cart_items)


@router.post("/cart", response_model=cart_schema.CartCountResponse)
def add_to_cart(
        cart_data: cart_schema.CartAddRequest,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니 추가"""

    # 카테고리 검증
    if cart_data.category not in ['커스텀디자인', '포트폴리오']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다."
        )

    # 해당 아이템이 실제로 존재하는지 확인
    if cart_data.category == '커스텀디자인':
        # 커스텀디자인 확인
        design = db.query(models.CustomDesign).filter(
            models.CustomDesign.item_name == cart_data.item_name,
            models.CustomDesign.user_id == current_user.username,
            models.CustomDesign.status == "1"  # 완료된 디자인만
        ).first()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 커스텀디자인을 찾을 수 없습니다."
            )
    else:
        # 포트폴리오 확인
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.design_name == cart_data.item_name,
            models.Portfolio.is_deleted == False
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 포트폴리오를 찾을 수 없습니다."
            )

    # 장바구니에 추가
    cart_crud.add_to_cart(
        db=db,
        user_id=current_user.username,
        item_name=cart_data.item_name,
        main_image_url=cart_data.main_image_url,
        category=cart_data.category
    )

    # 추가 후 전체 개수 반환
    count = cart_crud.get_cart_count(
        db=db,
        user_id=current_user.username
    )

    return cart_schema.CartCountResponse(count=count)


@router.delete("/cart/{item_name}", response_model=cart_schema.CartCountResponse)
def delete_cart_item(
        item_name: str,
        delete_data: cart_schema.CartDeleteRequest,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니 단일 삭제"""

    # 카테고리 검증
    if delete_data.category not in ['커스텀디자인', '포트폴리오']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다."
        )

    # 삭제 수행
    success = cart_crud.delete_cart_item(
        db=db,
        user_id=current_user.username,
        item_name=item_name,
        category=delete_data.category
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장바구니에서 해당 상품을 찾을 수 없습니다."
        )

    # 삭제 후 전체 개수 반환
    count = cart_crud.get_cart_count(
        db=db,
        user_id=current_user.username
    )

    return cart_schema.CartCountResponse(count=count)


@router.delete("/cart", response_model=cart_schema.CartCountResponse)
def delete_cart_by_category(
        delete_data: cart_schema.CartDeleteRequest,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """장바구니 카테고리 목록 일괄 삭제"""

    # 카테고리 검증
    if delete_data.category not in ['커스텀디자인', '포트폴리오']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다."
        )

    # 일괄 삭제 수행
    deleted_count = cart_crud.delete_cart_by_category(
        db=db,
        user_id=current_user.username,
        category=delete_data.category
    )

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"장바구니에 {delete_data.category} 카테고리의 상품이 없습니다."
        )

    # 삭제 후 전체 개수 반환
    count = cart_crud.get_cart_count(
        db=db,
        user_id=current_user.username
    )

    return cart_schema.CartCountResponse(count=count)