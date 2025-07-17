from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import released_product as released_product_schema
from Enduser.crud import released_product as released_product_crud
from Enduser.crud import realtime_users as realtime_users_crud
import math

router = APIRouter(tags=["Released Product"])


@router.get("/released_product/list", response_model=released_product_schema.PaginatedReleasedProductResponse)
def get_released_product_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        brand_name: Optional[str] = Query(None, description="브랜드 이름"),
        item_name: Optional[str] = Query(None, description="디자인 이름으로 검색"),
        orderBy: Optional[str] = Query("popularity", description="정렬 기준 (popularity: 인기순-기본값, latest: 최신순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """선택된 브랜드에 해당하는 디자인 목록 조회"""

    # orderBy 검증
    if orderBy not in ['popularity', 'latest']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="orderBy는 'popularity' 또는 'latest'여야 합니다."
        )

    paginated_data = released_product_crud.get_released_products_paginated(
        db=db,
        page=page,
        size=size,
        brand_name=brand_name,
        item_name=item_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return released_product_schema.PaginatedReleasedProductResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/released_product/{item_name}", response_model=released_product_schema.ReleasedProductDetailResponse)
def get_released_product_detail(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    선택된 디자인 정보 조회

    디자인 이름으로 출시 제품의 상세 정보를 조회합니다.
    조회시 조회수가 증가합니다.
    """

    product_detail = released_product_crud.get_released_product_detail(
        db=db,
        item_name=item_name
    )

    if not product_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )

    return released_product_schema.ReleasedProductDetailResponse(**product_detail)


@router.post("/released_product/enter/{item_name}", response_model=released_product_schema.RealtimeUsersResponse)
def enter_released_product(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """조회된 디자인 실시간 유저수 +1"""

    # 출시제품 존재 확인
    product = db.query(models.Releasedproduct).filter(
        models.Releasedproduct.design_name == item_name
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )

    # 유저 입장 처리
    realtime_users = realtime_users_crud.enter_content(
        db=db,
        user_id=current_user.username,
        content_type='released_product',
        content_name=item_name
    )

    return released_product_schema.RealtimeUsersResponse(
        item_name=item_name,
        realtime_users=realtime_users
    )


@router.post("/released_product/leave/{item_name}", response_model=released_product_schema.RealtimeUsersResponse)
def leave_released_product(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """조회된 디자인 실시간 유저수 -1"""

    # 유저 퇴장 처리
    realtime_users = realtime_users_crud.leave_content(
        db=db,
        user_id=current_user.username,
        content_type='released_product',
        content_name=item_name
    )

    return released_product_schema.RealtimeUsersResponse(
        item_name=item_name,
        realtime_users=realtime_users
    )


@router.get("/released_product/realtime-users/{item_name}",
            response_model=released_product_schema.RealtimeUsersResponse)
def get_released_product_realtime_users(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """조회한 디자인 실시간 유저수 조회"""

    realtime_users = realtime_users_crud.get_realtime_users_count(
        db=db,
        content_type='released_product',
        content_name=item_name
    )

    return released_product_schema.RealtimeUsersResponse(
        item_name=item_name,
        realtime_users=realtime_users
    )