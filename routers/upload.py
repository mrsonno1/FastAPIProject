# routers/upload.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import math
from db.database import get_db
# 수정/검색을 위한 스키마 및 CRUD 함수 임포트
from schemas.image import ImageResponse, PaginatedImageResponse
from crud import image as image_crud  # image_crud로 임포트
from services.storage_service import storage_service
from db import models
from schemas.color import NameCheckResponse

router = APIRouter(prefix="/images", tags=["Images"])  # prefix를 /images로 변경하는 것이 더 명확


@router.get("/list", response_model=PaginatedImageResponse)
def list_all_images(
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
        category: Optional[str] = Query(None, description="이미지 종류(category)로 필터링"),
        orderBy: Optional[str] = Query(None, description="정렬 기준 (예: 'rank asc', 'id desc')"),
        searchText: Optional[str] = Query(None, description="통합 검색어"),
        db: Session = Depends(get_db)
        # 인증이 필요하다면 , current_user: models.AdminUser = Depends(get_current_user) 추가
):
    """
    이미지 목록을 페이지네이션하여 조회합니다.
    'category' 파라미터로 특정 종류의 이미지만 필터링할 수 있습니다.
    """
    paginated_data = image_crud.get_images_paginated(
        db, page=page, size=size, category=category,
        orderBy=orderBy, searchText=searchText  # <-- CRUD 함수에 전달
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

# 기존 업로드 API (prefix 변경에 따라 경로도 변경됨)
@router.post("/upload", response_model=ImageResponse)
def upload_image(
        file: UploadFile = File(...),
        category: str = Form(...),  # <-- category를 Form 데이터로 받음
        display_name: str = Form(...),
        db: Session = Depends(get_db)
):
    """
    이미지 파일, 종류(category), 표시 이름을 함께 받아 업로드합니다.
    """
    # 업로드 전 중복 검사 (이제 category도 함께 전달)
    if image_crud.get_image_by_display_name(db, category=category, display_name=display_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{category}' 종류에 해당 표시 이름이 이미 존재합니다."
        )

    upload_result = storage_service.upload_file(file)
    if not upload_result:
        raise HTTPException(...)

    image_data = {
        "category": category,  # <-- DB에 저장할 데이터에 category 추가
        "display_name": display_name,
        "object_name": upload_result["object_name"],
        "public_url": upload_result["public_url"]
    }

    new_image = models.Image(**image_data)

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image


@router.get("/search", response_model=ImageResponse)
def search_image_by_display_name(
    # 경로 변수 대신 쿼리 파라미터로 받습니다.
    category: str = Query(..., description="검색할 이미지의 종류"),
    display_name: str = Query(..., description="검색할 이미지의 정확한 표시 이름"),
    db: Session = Depends(get_db)
):
    """
    종류(category)와 표시 이름(display_name)으로 이미지를 검색합니다.
    (한글 이름 검색을 위해 쿼리 파라미터 사용)
    """
    db_image = image_crud.get_image_by_display_name(
        db, category=category, display_name=display_name
    )
    if db_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 이름의 이미지를 찾을 수 없습니다."
        )
    return db_image

@router.get("/check/display-name", response_model=NameCheckResponse, tags=["Images", "Validation"])
def check_display_name_duplicate(
    category: str = Query(..., description="중복을 확인할 이미지 종류"),
    display_name: str = Query(..., description="중복을 확인할 표시 이름"),
    db: Session = Depends(get_db)
):
    """
    특정 카테고리 내에서 display_name이 이미 존재하는지 확인합니다.
    - 존재하면 {"exists": true}
    - 존재하지 않으면 {"exists": false}
    """
    image = image_crud.get_image_by_display_name(
        db, category=category, display_name=display_name
    )
    return {"exists": image is not None}

@router.put("/fix/{image_id}", response_model=ImageResponse)
def update_image_details(
        image_id: int,
        # 폼 데이터로 이름과 파일을 받습니다.
        display_name: str = Form(..., min_length=1),
        file: Optional[UploadFile] = File(None),  # 파일은 선택사항
        db: Session = Depends(get_db)
):
    """
    ID로 특정 이미지의 정보를 수정합니다.
    - 이름은 항상 전송해야 합니다.
    - 파일을 함께 보내면 이미지 파일도 교체됩니다.
    """
    # 1. 수정할 이미지 조회
    db_image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="수정할 이미지를 찾을 수 없습니다.")

    # 2. 이름 중복 검사 (수정하려는 이름이 다른 이미지에 사용 중인지)
    existing_image = image_crud.get_image_by_display_name(
        db,
        category=db_image.category,  # 기존 이미지와 같은 카테고리 내에서
        display_name=display_name
    )
    if existing_image and existing_image.id != image_id:
        raise HTTPException(status_code=409, detail="해당 종류에 이미 사용 중인 표시 이름입니다.")

    # 3. 파일 처리 로직
    new_object_name = None
    new_public_url = None

    if file:  # 만약 새로운 파일이 함께 전송되었다면
        # 3-1. 기존 파일 삭제
        if db_image.object_name:
            storage_service.delete_file(db_image.object_name)

        # 3-2. 새 파일 업로드
        upload_result = storage_service.upload_file(file)
        if not upload_result:
            raise HTTPException(status_code=500, detail="새 이미지 업로드에 실패했습니다.")

        # 3-3. 새 파일 정보를 변수에 할당
        new_object_name = upload_result["object_name"]
        new_public_url = upload_result["public_url"]

    # 4. CRUD 함수를 호출하여 DB 업데이트
    return image_crud.update_image(
        db=db,
        db_image=db_image,
        display_name=display_name,
        new_object_name=new_object_name,
        new_public_url=new_public_url
    )