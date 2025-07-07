# routers/released_product.py
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
import math
from released_product.schemas import released_product as released_product_schema
from db import models
from db.database import get_db
from released_product.crud import released_product as released_product_CRUD
from services.storage_service import storage_service
from core.security import get_current_user

router = APIRouter(prefix="/released-product", tags=["released-product"])

@router.post("/", response_model=released_product_schema.ReleasedProductApiResponse,
             status_code=status.HTTP_200_OK
)
def create_new_released_product(
    released_product_str: str = Form(..., alias="released_product"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):

    try:
        released_product_dict = json.loads(released_product_str)
        released_product_data = released_product_schema.ReleasedProductCreate(**released_product_dict)

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="전송된 'released_product' 데이터의 JSON 형식이 잘못되었습니다.")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"데이터 유효성 검사 실패: {e}")

    if released_product_CRUD.get_released_product_by_design_name(db, design_name=released_product_data.design_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 디자인명입니다.")

    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="메인 이미지 업로드에 실패했습니다.")

    released_product_data.main_image_url = upload_result["public_url"]

    created_released_product = released_product_CRUD.create_released_product(
        db=db,
        released_product=released_product_data,
        user_id=current_user.id
    )

    response_data = released_product_schema.ReleasedProductResponse.model_validate(created_released_product)

    return released_product_schema.ReleasedProductApiResponse(
        success=True,
        message="출시 제품이 성공적으로 생성되었습니다.",
        data=response_data
    )

@router.get("/list", response_model=released_product_schema.PaginatedReleasedProductResponse)
def list_all_released_products(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        design_name: Optional[str] = Query(None, description="디자인명으로 검색"),
        color_name: Optional[str] = Query(None, description="컬러명으로 검색"),
        db: Session = Depends(get_db)
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
        db: Session = Depends(get_db)
):
    db_released_product = released_product_CRUD.get_released_product_by_design_name(db, design_name=design_name)
    if db_released_product is None:
        raise HTTPException(status_code=404, detail="출시 제품을 찾을 수 없습니다.")
    return db_released_product
