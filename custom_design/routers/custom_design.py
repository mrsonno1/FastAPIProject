from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from custom_design.crud import custom_design as custom_design_CRUD
import math # math 임포트
from datetime import date # date 임포트
from db.database import get_db
from custom_design.schemas import custom_design as custom_design_schema
from db import models
from core.security import get_current_user # 인증 의존성 임포트
from typing import Optional # Optional 임포트

router = APIRouter(prefix="/custom-designs", tags=["Custom Designs"])


@router.post("/", response_model=custom_design_schema.CustomDesignApiResponse, status_code=status.HTTP_201_CREATED)
def create_new_custom_design(
    design: custom_design_schema.CustomDesignCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """새로운 커스텀 디자인 요청을 생성합니다."""
    # 코드명 중복 검사
    if db.query(models.CustomDesign).filter(models.CustomDesign.item_name == design.item_name).first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이템명입니다.")

    #데이터 베이스 적용
    created_customdesign = custom_design_CRUD.create_design(
        db=db,
        design=design,
        user_id=current_user.id
    )

    #리스폰 모델로 변환
    response_data = custom_design_schema.CustomDesignResponse.model_validate(created_customdesign)


    #반환값 생성
    return custom_design_schema.CustomDesignApiResponse(
        success=True,
        message="커스텀디자인이 성공적으로 생성되었습니다.",
        data=response_data
    )

    #return custom_design_CRUD.create_design(db=db, design=design, user_id=current_user.id)


@router.get("/list", response_model=custom_design_schema.PaginatedCustomDesignResponse)
def read_all_custom_designs(
        # 페이지네이션 파라미터
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),

        # 검색 필터 파라미터
        item_name: Optional[str] = Query(None, description="디자인명(코드명)으로 검색"),
        status: Optional[str] = Query(None, description="상태 검색"),
        start_date: Optional[date] = Query(None, description="검색 시작일 (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="검색 종료일 (YYYY-MM-DD)"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'user_name asc', 'code_name desc')"),

        db: Session = Depends(get_db)
):
    """
    모든 커스텀 디자인 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    paginated_data = custom_design_CRUD.get_designs_paginated(
        db,
        page=page,
        size=size,
        item_name=item_name,
        status=status,
        start_date=start_date,
        end_date=end_date,
        orderBy=orderBy
    )

    total_count = paginated_data["total_count"]
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": paginated_data["items"],
    }



@router.get("/{design_id}", response_model=custom_design_schema.CustomDesignResponse)
def read_single_custom_design(design_id: int, db: Session = Depends(get_db)):

    db_design = custom_design_CRUD.get_design_by_id(db, design_id)
    if db_design is None:
        raise HTTPException(status_code=404, detail="디자인을 찾을 수 없습니다.")
    return db_design


@router.patch("/status/{design_id}", response_model=custom_design_schema.CustomDesignResponse)
def update_status_of_design(
    design_id: int,
    status_update: custom_design_schema.CustomDesignStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):

    updated_design = custom_design_CRUD.update_design_status(db, design_id, status_update)
    if updated_design is None:
        raise HTTPException(status_code=404, detail="디자인을 찾을 수 없습니다.")

    return updated_design