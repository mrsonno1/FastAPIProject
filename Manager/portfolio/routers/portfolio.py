from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from Manager.portfolio.schemas import portfolio as portfolio_schema
from Manager.portfolio.crud import portfolio as portfolio_CRUD
from db import models
from db.database import get_db
from core.security import get_current_user
import math
from services.storage_service import storage_service
from services.thumbnail_service import thumbnail_service
# 새로운 형식의 포트폴리오 관련 API


router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.post("/", response_model=portfolio_schema.PortfolioApiResponse,
             status_code=status.HTTP_200_OK
)
def create_new_portfolio(
    design_name: str = Form(...),
    color_name: str = Form(...),
    exposed_countries: str = Form(""),  # 기본값 빈 문자열
    is_fixed_axis: str = Form("N"),  # 기본값 'N'
    design_line_image_id: Optional[str] = Form(None),
    design_line_color_id: Optional[str] = Form(None),
    design_base1_image_id: Optional[str] = Form(None),
    design_base1_color_id: Optional[str] = Form(None),
    design_base2_image_id: Optional[str] = Form(None),
    design_base2_color_id: Optional[str] = Form(None),
    design_pupil_image_id: Optional[str] = Form(None),
    design_pupil_color_id: Optional[str] = Form(None),
    graphic_diameter: Optional[str] = Form(None),
    optic_zone: Optional[str] = Form(None),
    dia: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """
    새로운 포트폴리오를 생성합니다.
    exposed_countries는 콤마로 구분된 국가 ID 문자열입니다 (예: "1,2,3,4")
    is_fixed_axis는 'Y' 또는 'N'입니다.
    """

    try:
        # --- [수정] 받은 Form 데이터로 Pydantic 모델 객체를 직접 생성 ---
        portfolio_data = portfolio_schema.PortfolioCreate(
            design_name=design_name,
            color_name=color_name,
            exposed_countries=exposed_countries,
            is_fixed_axis=is_fixed_axis,
            design_line_image_id=design_line_image_id,
            design_line_color_id=design_line_color_id,
            design_base1_image_id=design_base1_image_id,
            design_base1_color_id=design_base1_color_id,
            design_base2_image_id=design_base2_image_id,
            design_base2_color_id=design_base2_color_id,
            design_pupil_image_id=design_pupil_image_id,
            design_pupil_color_id=design_pupil_color_id,
            graphic_diameter=graphic_diameter,
            optic_zone=optic_zone,
            dia=dia
        )
    except Exception as e:  # Pydantic 유효성 검사 실패 시
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    if portfolio_CRUD.get_portfolio_by_design_name(db, design_name=portfolio_data.design_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    # 이미지 업로드
    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="메인 이미지 업로드에 실패했습니다.")

    # 썸네일 생성
    file.file.seek(0)  # 파일 포인터 리셋
    file_content = file.file.read()
    thumbnail_url = thumbnail_service.create_and_upload_thumbnail(file_content, file.filename)

    # 이미지 업로드 url 적용
    portfolio_data.main_image_url = upload_result["public_url"]
    portfolio_data.thumbnail_url = thumbnail_url  # 썸네일 URL 추가

    # 데이터베이스 적용
    created_portfolio = portfolio_CRUD.create_portfolio(
        db=db,
        portfolio=portfolio_data,
        user_id=current_user.id
    )

    # 응답 모델로 변환
    response_data = portfolio_schema.PortfolioResponse.model_validate(created_portfolio)

    # 반환값 생성
    return portfolio_schema.PortfolioApiResponse(
        success=True,
        message="포트폴리오가 성공적으로 생성되었습니다.",
        data=response_data
    )

@router.delete("/{portfolio_id}", response_model=portfolio_schema.StatusResponse, status_code=status.HTTP_200_OK)
def delete_single_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 포트폴리오를 삭제합니다."""
    try:
        was_deleted = portfolio_CRUD.delete_portfolio_by_id(db, portfolio_id=portfolio_id)
        if not was_deleted:
            raise HTTPException(status_code=404, detail="해당 ID의 포트폴리오를 찾을 수 없습니다.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

    return portfolio_schema.StatusResponse(status="success", message="포트폴리오가 성공적으로 삭제되었습니다.")


@router.get("/list", response_model=portfolio_schema.PaginatedPortfolioListResponse)
def list_all_portfolios(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        design_name: Optional[str] = Query(None, description="디자인명으로 검색"),
        color_name: Optional[str] = Query(None, description="컬러명으로 검색"),
        exposed_countries: Optional[List[str]] = Query(None, description="노출 국가 ID로 검색"),
        is_fixed_axis: Optional[str] = Query(None, description="고정 축 여부로 검색 (Y/N)"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'created_at desc', 'views asc')"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    모든 포트폴리오 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    # is_fixed_axis 검증
    if is_fixed_axis and is_fixed_axis not in ['Y', 'N']:
        raise HTTPException(status_code=400, detail="is_fixed_axis는 'Y' 또는 'N'이어야 합니다")

    paginated_data = portfolio_CRUD.get_portfolios_paginated(
        db,
        page=page,
        size=size,
        design_name=design_name,
        color_name=color_name,
        exposed_countries=exposed_countries,
        is_fixed_axis=is_fixed_axis,
        orderBy=orderBy
    )

    items = paginated_data["items"]
    total_count = paginated_data["total_count"]

    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/info/{portfolio_id}", response_model=portfolio_schema.PortfolioDetailApiResponse)
def get_portfolio_detail(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
    ):

    """
    단일 포트폴리오 상세 정보를 조회합니다.<br>
    ID로 특정 포트폴리오를 찾아 상세 정보를 반환합니다.
    """

    detail_data  = portfolio_CRUD.get_portfolio_detail(db, portfolio_id, is_admin=True)
    if not detail_data :
        raise HTTPException(status_code=404, detail="해당 ID의 포트폴리오를 찾을 수 없습니다.")

    # Pydantic 모델을 사용하여 데이터 유효성 검사 및 변환
    validated_data = portfolio_schema.PortfolioDetailData.model_validate(detail_data)

    return portfolio_schema.PortfolioDetailApiResponse(data=validated_data)


@router.get("/{design_name}", response_model=portfolio_schema.PortfolioResponse)
def read_single_portfolio(
        design_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    db_portfolio = portfolio_CRUD.get_portfolio_by_design_name(db, design_name=design_name)
    if db_portfolio is None:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    return db_portfolio

@router.patch("/axis/{portfolio_id}", response_model=portfolio_schema.PortfolioApiResponse)
def toggle_fixed_axis(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """포트폴리오의 is_fixed_axis 값을 토글합니다 (Y→N, N→Y)."""

    # 1. 포트폴리오 조회
    db_portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

    # 2. is_fixed_axis 값 토글 (Y→N, N→Y)
    current_value = db_portfolio.is_fixed_axis
    new_value = "N" if current_value == "Y" else "Y"

    # 3. 값 업데이트
    db_portfolio.is_fixed_axis = new_value
    db.commit()
    db.refresh(db_portfolio)

    # 4. 응답 생성
    response_data = portfolio_schema.PortfolioResponse.model_validate(db_portfolio)

    return portfolio_schema.PortfolioApiResponse(
        success=True,
        message=f"포트폴리오 축고정 상태가 '{current_value}'에서 '{new_value}'로 변경되었습니다.",
        data=response_data
    )



@router.patch("/{portfolio_id}", response_model=portfolio_schema.PortfolioApiResponse)
def update_portfolio_details(
    portfolio_id: int,
    # 필수 필드
    design_name: str = Form(...),
    color_name: str = Form(...),
    # 선택적 폼 필드
    exposed_countries: str = Form(""),
    is_fixed_axis: str = Form("N"),
    design_line_image_id: Optional[str] = Form(None),
    design_line_color_id: Optional[str] = Form(None),
    design_base1_image_id: Optional[str] = Form(None),
    design_base1_color_id: Optional[str] = Form(None),
    design_base2_image_id: Optional[str] = Form(None),
    design_base2_color_id: Optional[str] = Form(None),
    design_pupil_image_id: Optional[str] = Form(None),
    design_pupil_color_id: Optional[str] = Form(None),
    graphic_diameter: Optional[str] = Form(None),
    optic_zone: Optional[str] = Form(None),
    dia: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """포트폴리오 정보를 업데이트합니다."""
    db_portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")

    try:
        # --- [수정] 받은 Form 데이터로 Pydantic 모델 객체를 직접 생성 ---
        # 수정 시에는 모든 필드가 제공되지 않을 수 있으므로,
        # 기본 스키마를 사용하여 유효성 검사를 진행합니다.
        portfolio_update_data = portfolio_schema.PortfolioCreate(
            design_name=design_name,
            color_name=color_name,
            exposed_countries=exposed_countries,
            is_fixed_axis=is_fixed_axis,
            design_line_image_id=design_line_image_id,
            design_line_color_id=design_line_color_id,
            design_base1_image_id=design_base1_image_id,
            design_base1_color_id=design_base1_color_id,
            design_base2_image_id=design_base2_image_id,
            design_base2_color_id=design_base2_color_id,
            design_pupil_image_id=design_pupil_image_id,
            design_pupil_color_id=design_pupil_color_id,
            graphic_diameter=graphic_diameter,
            optic_zone=optic_zone,
            dia=dia
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    # 디자인명 중복 검사 (자신을 제외하고)
    existing_portfolio = portfolio_CRUD.get_portfolio_by_design_name(db, design_name=portfolio_update_data.design_name)
    if existing_portfolio and existing_portfolio.id != portfolio_id:
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    # 이미지 파일 처리
    if file:
        # 기존 이미지 삭제 (선택 사항, 필요에 따라 구현)
        if db_portfolio.main_image_url:
            # storage_service.delete_file(db_portfolio.object_name) # object_name이 필요
            pass # 현재 object_name이 없으므로 삭제 로직은 생략

        upload_result = storage_service.upload_file(file)
        if not upload_result:
            raise HTTPException(status_code=500, detail="새 이미지 업로드에 실패했습니다.")
        portfolio_update_data.main_image_url = upload_result["public_url"]
        
        # 썸네일 생성
        file.file.seek(0)  # 파일 포인터 리셋
        file_content = file.file.read()
        thumbnail_url = thumbnail_service.create_and_upload_thumbnail(file_content, file.filename)
        portfolio_update_data.thumbnail_url = thumbnail_url  # 썸네일 URL 추가

    updated_portfolio = portfolio_CRUD.update_portfolio(
        db=db,
        db_portfolio=db_portfolio,
        portfolio_update=portfolio_update_data
    )

    response_data = portfolio_schema.PortfolioResponse.model_validate(updated_portfolio)

    return portfolio_schema.PortfolioApiResponse(
        success=True,
        message="포트폴리오가 성공적으로 업데이트되었습니다.",
        data=response_data
    )

