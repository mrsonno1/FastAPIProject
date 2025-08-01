# routers/released_product.py
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import Optional
import math
from Manager.released_product.schemas import released_product as released_product_schema
from db import models
from db.database import get_db
from Manager.released_product.crud import released_product as released_product_CRUD
from services.storage_service import storage_service
from services.thumbnail_service import thumbnail_service
from core.security import get_current_user
from Manager.portfolio.schemas import portfolio as portfolio_schema

router = APIRouter(prefix="/released-product", tags=["released-product"])

@router.post("/", response_model=released_product_schema.ReleasedProductApiResponse,
             status_code=status.HTTP_200_OK
)
def create_new_released_product(
    design_name: str = Form(...),
    color_name: str = Form(...),
    brand_id: int = Form(...),
    color_line_color_id: Optional[str] = Form(None),
    color_base1_color_id: Optional[str] = Form(None),
    color_base2_color_id: Optional[str] = Form(None),
    color_pupil_color_id: Optional[str] = Form(None),
    graphic_diameter: Optional[str] = Form(None),
    optic_zone: Optional[str] = Form(None),
    dia: Optional[str] = Form(None),
    base_curve: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    try:
        # --- [수정] 받은 Form 데이터로 Pydantic 모델 객체를 직접 생성 ---
        released_product_data = released_product_schema.ReleasedProductCreate(
            design_name=design_name,
            color_name=color_name,
            brand_id=brand_id,
            color_line_color_id=color_line_color_id,
            color_base1_color_id=color_base1_color_id,
            color_base2_color_id=color_base2_color_id,
            color_pupil_color_id=color_pupil_color_id,
            graphic_diameter=graphic_diameter,
            optic_zone=optic_zone,
            dia=dia,
            base_curve=base_curve
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    if released_product_CRUD.get_released_product_by_design_name(db, design_name=released_product_data.design_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    # 파일 내용을 먼저 읽어서 저장
    file_content = file.file.read()
    file.file.seek(0)  # 파일 포인터를 처음으로 되돌림
    
    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="메인 이미지 업로드에 실패했습니다.")

    # 썸네일 생성
    thumbnail_url = thumbnail_service.create_and_upload_thumbnail(file_content, file.filename)

    released_product_data.main_image_url = upload_result["public_url"]
    released_product_data.thumbnail_url = thumbnail_url  # 썸네일 URL 추가

    created_released_product = released_product_CRUD.create_released_product(
        db=db,
        # --- [수정] CRUD 함수에 Pydantic 모델 객체 전달 ---
        released_product=released_product_data,
        user_id=current_user.id
    )

    response_data = released_product_schema.ReleasedProductResponse.model_validate(created_released_product)

    return released_product_schema.ReleasedProductApiResponse(
        success=True,
        message="출시 제품이 성공적으로 생성되었습니다.",
        data=response_data
    )

@router.patch("/{product_id}", response_model=released_product_schema.ReleasedProductApiResponse)
def update_released_product_details(
    product_id: int,
    design_name: str = Form(...),
    color_name: str = Form(...),
    brand_id: int = Form(...),
    color_line_color_id: Optional[str] = Form(None),
    color_base1_color_id: Optional[str] = Form(None),
    color_base2_color_id: Optional[str] = Form(None),
    color_pupil_color_id: Optional[str] = Form(None),
    graphic_diameter: Optional[str] = Form(None),
    optic_zone: Optional[str] = Form(None),
    dia: Optional[str] = Form(None),
    base_curve: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """출시 제품 정보를 업데이트합니다."""
    db_released_product = db.query(models.Releasedproduct).filter(models.Releasedproduct.id == product_id).first()
    if not db_released_product:
        raise HTTPException(status_code=404, detail="출시 제품을 찾을 수 없습니다.")

    try:
        # --- [수정] 받은 Form 데이터로 Pydantic 모델 객체를 직접 생성 ---
        released_product_update_data = released_product_schema.ReleasedProductCreate(
            design_name=design_name,
            color_name=color_name,
            brand_id=brand_id,
            color_line_color_id=color_line_color_id,
            color_base1_color_id=color_base1_color_id,
            color_base2_color_id=color_base2_color_id,
            color_pupil_color_id=color_pupil_color_id,
            graphic_diameter=graphic_diameter,
            optic_zone=optic_zone,
            dia=dia,
            base_curve=base_curve
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    # 디자인명 중복 검사 (자신을 제외하고)
    existing_product = released_product_CRUD.get_released_product_by_design_name(db, design_name=released_product_update_data.design_name)
    if existing_product and existing_product.id != product_id:
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    # 이미지 파일 처리
    if file:
        # 기존 이미지 삭제 (선택 사항, 필요에 따라 구현)
        if db_released_product.main_image_url:
            # storage_service.delete_file(db_released_product.object_name) # object_name이 필요
            pass # 현재 object_name이 없으므로 삭제 로직은 생략

        # 파일 내용을 먼저 읽어서 저장
        file_content = file.file.read()
        file.file.seek(0)  # 파일 포인터를 처음으로 되돌림
        
        upload_result = storage_service.upload_file(file)
        if not upload_result:
            raise HTTPException(status_code=500, detail="새 이미지 업로드에 실패했습니다.")
        released_product_update_data.main_image_url = upload_result["public_url"]
        
        # 썸네일 생성
        thumbnail_url = thumbnail_service.create_and_upload_thumbnail(file_content, file.filename)
        released_product_update_data.thumbnail_url = thumbnail_url  # 썸네일 URL 추가

    updated_released_product = released_product_CRUD.update_released_product(
        db=db,
        db_released_product=db_released_product,
        released_product_update=released_product_update_data
    )

    response_data = released_product_schema.ReleasedProductResponse.model_validate(updated_released_product)

    return released_product_schema.ReleasedProductApiResponse(
        success=True,
        message="출시 제품이 성공적으로 업데이트되었습니다.",
        data=response_data
    )


@router.delete("/{product_id}", response_model=portfolio_schema.StatusResponse, status_code=status.HTTP_200_OK)
def delete_single_released_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """ID로 특정 출시 제품을 삭제합니다."""
    try:
        was_deleted = released_product_CRUD.delete_released_product_by_id(db, product_id=product_id)
        if not was_deleted:
            raise HTTPException(status_code=404, detail="해당 ID의 출시 제품을 찾을 수 없습니다.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

    return portfolio_schema.StatusResponse(status="success", message="출시 제품이 성공적으로 삭제되었습니다.")


@router.get("/list", response_model=released_product_schema.ReleasedProductListResponse)
def list_all_released_products(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        design_name: Optional[str] = Query(None, description="디자인명으로 검색"),
        color_name: Optional[str] = Query(None, description="컬러명으로 검색"),
        brandname: Optional[str] = Query(None, description="브랜드명으로 검색"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'created_at desc', 'views asc')"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    모든 출시 제품 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    paginated_data = released_product_CRUD.get_released_products_paginated(
        db,
        page=page,
        size=size,
        design_name=design_name,
        color_name=color_name,
        brandname=brandname,
        orderBy=orderBy,
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

@router.get("/{design_name}", response_model=released_product_schema.ReleasedProductResponse)
def read_single_released_product(
        design_name: str,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    db_released_product = released_product_CRUD.get_released_product_by_design_name(db, design_name=design_name)
    if db_released_product is None:
        raise HTTPException(status_code=404, detail="출시 제품을 찾을 수 없습니다.")
    return db_released_product

@router.get("/info/{id}", response_model=released_product_schema.ReleasedProductDetailResponse)
def get_released_product_detail(
        id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    ID로 특정 출시 제품의 상세 정보를 조회합니다.
    디자인, 컬러, 이미지 등의 세부 정보가 포함됩니다.
    """
    # 먼저 제품이 존재하는지 확인
    product = released_product_CRUD.get_released_product_by_id(db, product_id=id)
    if not product:
        raise HTTPException(status_code=404, detail="해당 ID의 출시 제품을 찾을 수 없습니다.")

    # 상세 정보 조회
    result = released_product_CRUD.get_released_product_detail(db, product_id=id)
    if not result:
        raise HTTPException(status_code=500, detail="출시 제품 상세 정보 조회 중 오류가 발생했습니다.")

    return result