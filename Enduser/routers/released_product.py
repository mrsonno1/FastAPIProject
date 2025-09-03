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
from services.translate_service import translate_service
from core.dependencies import get_current_language_dependency

router = APIRouter(tags=["Released Product"])


@router.get("/released_product/list", response_model=released_product_schema.PaginatedReleasedProductResponse)
def get_released_product_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        brand_name: Optional[str] = Query(None, description="브랜드 이름"),
        item_name: Optional[str] = Query(None, description="디자인 이름으로 검색"),
        orderBy: Optional[str] = Query("popularity", description="정렬 기준 (popularity: 인기순-기본값, latest: 최신순)"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user),
        language: str = Depends(get_current_language_dependency)  # 추가
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

    # 브랜드명 번역 처리
    items = paginated_data["items"]
    if language == 'en':
        for item in items:
            if 'brand_name' in item:
                item['brand_name'] = translate_service.translate_text(
                    item['brand_name'],
                    target_lang='en',
                    source_lang='ko'
                )

    return released_product_schema.PaginatedReleasedProductResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=items
    )


# get_released_product_detail 함수 수정 - Depends에 언어 추가
@router.get("/released_product/by-id/{product_id}", response_model=released_product_schema.ReleasedProductDetailResponse)
def get_released_product_detail_by_id(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user),
        language: str = Depends(get_current_language_dependency)
):
    """
    ID로 출시 제품 상세 정보 조회
    
    출시 제품 ID로 상세 정보를 조회합니다.
    조회시 조회수가 증가합니다.
    """
    
    product_detail = released_product_crud.get_released_product_detail(
        db=db,
        product_id=product_id
    )
    
    if not product_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )
    
    # 브랜드명 번역 처리
    if language == 'en' and 'brand_name' in product_detail:
        product_detail['brand_name'] = translate_service.translate_text(
            product_detail['brand_name'],
            target_lang='en',
            source_lang='ko'
        )
    
    return released_product_schema.ReleasedProductDetailResponse(**product_detail)


@router.get("/released_product/{item_name}", response_model=released_product_schema.ReleasedProductDetailResponse)
def get_released_product_detail(
        item_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user),
        language: str = Depends(get_current_language_dependency)  # 추가
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

    # 브랜드명 번역 처리
    if language == 'en' and 'brand_name' in product_detail:
        product_detail['brand_name'] = translate_service.translate_text(
            product_detail['brand_name'],
            target_lang='en',
            source_lang='ko'
        )

    return released_product_schema.ReleasedProductDetailResponse(**product_detail)


@router.post("/released_product/enter/by-id/{product_id}", response_model=released_product_schema.RealtimeUsersResponse)
def enter_released_product_by_id(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 조회된 디자인 실시간 유저수 +1"""
    
    # 출시제품 존재 확인
    product = db.query(models.Releasedproduct).filter(
        models.Releasedproduct.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )
    
    # 유저 입장 처리 (ID 기반)
    realtime_users = realtime_users_crud.enter_content(
        db=db,
        user_id=current_user.username,
        content_type='released_product',
        content_id=product_id
    )
    
    return released_product_schema.RealtimeUsersResponse(
        item_name=product.design_name,
        realtime_users=realtime_users
    )


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


@router.post("/released_product/leave/by-id/{product_id}", response_model=released_product_schema.RealtimeUsersResponse)
def leave_released_product_by_id(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 조회된 디자인 실시간 유저수 -1"""
    
    # 출시제품 존재 확인
    product = db.query(models.Releasedproduct).filter(
        models.Releasedproduct.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )
    
    # 유저 퇴장 처리 (ID 기반)
    realtime_users = realtime_users_crud.leave_content(
        db=db,
        user_id=current_user.username,
        content_type='released_product',
        content_id=product_id
    )
    
    return released_product_schema.RealtimeUsersResponse(
        item_name=product.design_name,
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


@router.get("/released_product/realtime-users/by-id/{product_id}",
            response_model=released_product_schema.RealtimeUsersResponse)
def get_released_product_realtime_users_by_id(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 조회한 디자인 실시간 유저수 조회"""
    
    # 출시제품 존재 확인
    product = db.query(models.Releasedproduct).filter(
        models.Releasedproduct.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="출시 제품을 찾을 수 없습니다."
        )
    
    realtime_users = realtime_users_crud.get_realtime_users_count(
        db=db,
        content_type='released_product',
        content_id=product_id
    )
    
    return released_product_schema.RealtimeUsersResponse(
        item_name=product.design_name,
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