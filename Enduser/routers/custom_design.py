from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import custom_design as custom_design_schema
from Enduser.crud import custom_design as custom_design_crud
import math

router = APIRouter(tags=["Custom Design"])


@router.get("/images/list", response_model=custom_design_schema.PaginatedImageResponse)
def get_images_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        category: Optional[str] = Query(None, description="카테고리 필터링"),
        display_name: Optional[str] = Query(None, description="디자인 번호로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """관리자가 등록한 라인/바탕1/바탕2/동공 디자인 목록 조회"""

    paginated_data = custom_design_crud.get_images_paginated(
        db=db,
        page=page,
        size=size,
        category=category,
        display_name=display_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return custom_design_schema.PaginatedImageResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/colors/list", response_model=custom_design_schema.PaginatedColorResponse)
def get_colors_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        color_name: Optional[str] = Query(None, description="색상 번호로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """관리자가 등록한 색상 목록 조회"""

    paginated_data = custom_design_crud.get_colors_paginated(
        db=db,
        page=page,
        size=size,
        color_name=color_name,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return custom_design_schema.PaginatedColorResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=paginated_data["items"]
    )


@router.get("/my-designs/{design_id}", response_model=custom_design_schema.CustomDesignDetailResponse)
def get_my_design_detail(
        design_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """내 커스텀디자인 항목 조회"""

    design_detail = custom_design_crud.get_custom_design_detail(
        db=db,
        design_id=design_id,
        user_id=current_user.username
    )

    if not design_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커스텀 디자인을 찾을 수 없습니다."
        )

    return custom_design_schema.CustomDesignDetailResponse(**design_detail)


@router.post("/my-designs", response_model=custom_design_schema.CustomDesignCreateResponse)
def create_my_design(
        design_data: custom_design_schema.CustomDesignCreateRequest,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 추가 - Manager 버전과 동일한 구조"""

    # 디자인명 중복 검사
    existing_design = db.query(models.CustomDesign).filter(
        models.CustomDesign.item_name == design_data.item_name,
        models.CustomDesign.user_id == current_user.username
    ).first()

    if existing_design:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 디자인명입니다."
        )

    try:
        # Manager 버전과 동일한 방식으로 커스텀 디자인 생성
        created_design = custom_design_crud.create_custom_design(
            db=db,
            design_data=design_data.dict(),
            user_id=current_user.username
        )

        return custom_design_schema.CustomDesignCreateResponse(
            id=created_design.id,
            item_name=created_design.item_name,
            main_image_url=created_design.main_image_url or ""
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"커스텀 디자인 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/my-designs/list", response_model=custom_design_schema.PaginatedCustomDesignResponse)
def get_my_designs_list(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        orderBy: Optional[str] = Query(None, description="정렬 기준"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """커스텀디자인 완료 목록 조회 - Manager 버전과 동일한 구조"""

    paginated_data = custom_design_crud.get_user_custom_designs_paginated(
        db=db,
        user_id=current_user.username,
        page=page,
        size=size,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    # 응답 형식에 맞게 변환
    items = []
    for design in paginated_data["items"]:
        items.append(custom_design_schema.CustomDesignListItem(
            id=design.id,
            item_name=design.item_name,
            main_image_url=design.main_image_url or ""
        ))

    return custom_design_schema.PaginatedCustomDesignResponse(
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        size=size,
        items=items
    )