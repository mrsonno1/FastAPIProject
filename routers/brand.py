# routers/brand.py
from typing import List, Optional
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas import brand as brand_schema
from crud import brand as brand_crud
from db import models
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query, Response
from services.storage_service import storage_service # S3/MinIO 서비스 임포트
from schemas.brand import PaginatedBrandResponse
import math

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.post("/", response_model=brand_schema.BrandResponse, status_code=status.HTTP_201_CREATED)
def create_new_brand(
        # 이제 Form 데이터와 File 데이터를 함께 받습니다.
        brand_name: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """새로운 브랜드를 등록합니다. 이름과 이미지 파일을 함께 전송받습니다."""
    if brand_crud.get_brand_by_name(db, brand_name=brand_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 브랜드 이름입니다.")

    # 1. S3(MinIO)에 이미지 업로드
    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")

    # 2. CRUD 함수를 호출하여 DB에 저장
    return brand_crud.create_brand(
        db=db,
        brand_name=brand_name,
        brand_image_url=upload_result["public_url"],
        object_name = upload_result["object_name"]
    )

@router.get("/", response_model=List[brand_schema.BrandResponse])
def get_all_countries(db: Session = Depends(get_db)):
    """모든 국가를 순위 순으로 조회합니다."""
    return brand_schema.get_all_brands_ordered(db)




@router.get("/list", response_model=PaginatedBrandResponse)
def list_all_brands(
        page: int = Query(1, ge=1),
        size: int = Query(999, ge=1, le=1000),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'rank asc')"),
        searchText: Optional[str] = Query(None, description="통합 검색어"),
        db: Session = Depends(get_db)
):
    """모든 브랜드를 검색 및 정렬 조건과 함께 페이지네이션하여 조회합니다."""
    # 페이지네이션 기능이 포함된 CRUD 함수를 호출해야 합니다.
    paginated_data = brand_crud.get_brands_paginated(
        db, page=page, size=size, orderBy=orderBy, searchText=searchText
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


@router.put("/{brand_id}", response_model=brand_schema.BrandResponse)
def update_brand_details(
        brand_id: int,
        brand_name: str = Form(...),
        # 파일은 선택사항(Optional)으로 받습니다.
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db)
):
    """브랜드의 이름이나 이미지를 수정합니다."""
    db_brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if not db_brand:
        raise HTTPException(status_code=404, detail="브랜드를 찾을 수 없습니다.")

    # 이름 중복 검사
    existing_brand = brand_crud.get_brand_by_name(db, brand_name=brand_name)
    if existing_brand and existing_brand.id != brand_id:
        raise HTTPException(status_code=409, detail="이미 사용 중인 브랜드 이름입니다.")

    new_image_url = db_brand.brand_image_url  # 기본값은 기존 URL
    new_object_name = db_brand.object_name

    if file:  # 만약 새로운 파일이 함께 전송되었다면
        # 1. 기존 S3 파일 삭제
        if db_brand.object_name:  # object_name이 DB에 저장되어 있어야 함
            storage_service.delete_file(db_brand.object_name)

        # 2. 새 파일 업로드
        upload_result = storage_service.upload_file(file)
        if not upload_result:
            raise HTTPException(status_code=500, detail="새 이미지 업로드에 실패했습니다.")

        new_image_url = upload_result["public_url"]
        new_object_name = upload_result["object_name"]
        # TODO: 새로운 object_name도 DB에 저장해야 함

    # CRUD 함수를 호출하여 DB 업데이트
    return brand_crud.update_brand_info(
        db,
        db_brand=db_brand,
        brand_name=brand_name,
        brand_image_url=new_image_url,
        object_name=new_object_name
    )

@router.patch("/rank/bulk", status_code=status.HTTP_204_NO_CONTENT)
def update_ranks_in_bulk(
    rank_update: brand_schema.RankUpdateBulk,
    db: Session = Depends(get_db)
):
    """
    전체 브랜드 순서 목록을 한 번에 업데이트합니다.
    """
    brand_crud.update_brand_ranks_bulk(db, ranks=rank_update.ranks)
    return