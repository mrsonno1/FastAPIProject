# progress_status/routers/progress_status.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from db.database import get_db
from progress_status.schemas import progress_status as progress_status_schema
from progress_status.crud import progress_status as progress_status_crud
from db import models
from core.security import get_current_user

router = APIRouter(prefix="/progress-status", tags=["Progress Status"])


@router.post("/", response_model=progress_status_schema.ProgressStatusApiResponse,
             status_code=status.HTTP_201_CREATED)
def create_new_progress_status(
        progress_status: progress_status_schema.ProgressStatusCreate,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    새로운 진행 상태를 생성합니다.

    - **user_id**: 사용자 ID
    - **custom_design_id**: 커스텀 디자인 ID (필수)
    - **portfolio_id**: 포트폴리오 ID (선택)
    - **status**: 진행 상태 (0: 대기, 1: 진행중, 2: 지연, 3: 배송완료)
    - **notes**: 메모 (선택)
    """
    # 권한 검사 (필요시 추가)
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="진행 상태를 생성할 권한이 없습니다."
        )

    # 커스텀 디자인이 존재하는지 확인
    custom_design = db.query(models.CustomDesign).filter(
        models.CustomDesign.id == progress_status.custom_design_id
    ).first()
    if not custom_design:
        raise HTTPException(
            status_code=404,
            detail="해당 ID의 커스텀 디자인을 찾을 수 없습니다."
        )

    # 포트폴리오 ID가 제공된 경우 존재하는지 확인
    if progress_status.portfolio_id:
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.id == progress_status.portfolio_id
        ).first()
        if not portfolio:
            raise HTTPException(
                status_code=404,
                detail="해당 ID의 포트폴리오를 찾을 수 없습니다."
            )

    created_progress_status = progress_status_crud.create_progress_status(
        db=db,
        progress_status=progress_status
    )

    response_data = progress_status_schema.ProgressStatusResponse.model_validate(
        created_progress_status
    )

    return progress_status_schema.ProgressStatusApiResponse(
        success=True,
        message="진행 상태가 성공적으로 생성되었습니다.",
        data=response_data
    )


@router.get("/list", response_model=progress_status_schema.PaginatedProgressStatusResponse)
def list_all_progress_status(
        # 페이지네이션 파라미터
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),

        # 검색 필터 파라미터
        user_name: Optional[str] = Query(None, description="사용자명으로 검색"),
        custom_design_name: Optional[str] = Query(None, description="커스텀 디자인명으로 검색"),
        portfolio_name: Optional[str] = Query(None, description="포트폴리오명으로 검색"),
        status: Optional[str] = Query(None, description="상태값으로 검색 (0~3)"),

        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    모든 진행 상태 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.

    응답 형식:
    - type: 0=custom_design, 1=portfolio
    - type_id: custom_design id 또는 portfolio id
    - type_name: custom_design의 item_name 또는 portfolio의 design_name
    - image_url: main_image_url
    - design_line, design_base1, design_base2, design_pupil: 이미지 정보
    - design_line_color, design_base1_color, design_base2_color, design_pupil_color: 색상 정보

    상태 코드:
    - 0: 대기
    - 1: 진행중
    - 2: 지연
    - 3: 배송완료
    """
    # 권한 검사 (필요시 조정)
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="진행 상태 목록을 조회할 권한이 없습니다."
        )

    # 상태값 유효성 검사
    if status and status not in ['0', '1', '2', '3']:
        raise HTTPException(
            status_code=400,
            detail="상태값은 0, 1, 2, 3 중 하나여야 합니다."
        )

    paginated_data = progress_status_crud.get_progress_status_paginated(
        db,
        page=page,
        size=size,
        user_name=user_name,
        custom_design_name=custom_design_name,
        portfolio_name=portfolio_name,
        status=status
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


@router.get("/{progress_status_id}", response_model=progress_status_schema.ProgressStatusResponse)
def get_single_progress_status(
        progress_status_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 진행 상태의 상세 정보를 조회합니다."""
    db_progress_status = progress_status_crud.get_progress_status_by_id(
        db, progress_status_id
    )
    if not db_progress_status:
        raise HTTPException(
            status_code=404,
            detail="해당 ID의 진행 상태를 찾을 수 없습니다."
        )

    return db_progress_status


@router.patch("/{progress_status_id}", response_model=progress_status_schema.ProgressStatusApiResponse)
def update_progress_status_details(
        progress_status_id: int,
        progress_status_update: progress_status_schema.ProgressStatusUpdate,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 진행 상태의 정보를 업데이트합니다."""
    # 권한 검사
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="진행 상태를 수정할 권한이 없습니다."
        )

    db_progress_status = progress_status_crud.get_progress_status_by_id(
        db, progress_status_id
    )
    if not db_progress_status:
        raise HTTPException(
            status_code=404,
            detail="수정할 진행 상태를 찾을 수 없습니다."
        )

    # 상태값 유효성 검사
    if progress_status_update.status and progress_status_update.status not in ['0', '1', '2', '3']:
        raise HTTPException(
            status_code=400,
            detail="상태값은 0, 1, 2, 3 중 하나여야 합니다."
        )

    updated_progress_status = progress_status_crud.update_progress_status(
        db,
        db_progress_status=db_progress_status,
        progress_status_update=progress_status_update
    )

    response_data = progress_status_schema.ProgressStatusResponse.model_validate(
        updated_progress_status
    )

    return progress_status_schema.ProgressStatusApiResponse(
        success=True,
        message="진행 상태가 성공적으로 업데이트되었습니다.",
        data=response_data
    )


@router.post("/sync-existing-data", response_model=progress_status_schema.StatusResponse)
def sync_existing_progress_data(
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    기존 데이터를 기반으로 progress_status를 일괄 생성합니다.
    (임시 API - 한 번만 실행)

    - status가 '3'인 모든 custom_design에 대해 progress_status 생성
    - 모든 portfolio에 대해 progress_status 생성 또는 portfolio_id 업데이트
    """
    # superadmin 권한만 실행 가능
    if current_user.permission != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 작업은 superadmin 권한이 필요합니다."
        )

    try:
        created_count = progress_status_crud.sync_existing_data(db)
        return progress_status_schema.StatusResponse(
            status="success",
            message=f"기존 데이터 동기화 완료. {created_count}개의 progress_status가 생성되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동기화 중 오류 발생: {str(e)}"
        )