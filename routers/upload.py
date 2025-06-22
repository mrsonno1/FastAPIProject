# routers/upload.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session

from db.database import get_db
# 수정/검색을 위한 스키마 및 CRUD 함수 임포트
from schemas.image import ImageResponse
from crud import image as image_crud  # image_crud로 임포트
from services.minio_service import minio_service
from db import models

router = APIRouter(prefix="/images", tags=["Images"])  # prefix를 /images로 변경하는 것이 더 명확


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

    upload_result = minio_service.upload_file(file)
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


@router.get("/search/{category}/{display_name}", response_model=ImageResponse)
def search_image_by_display_name(category: str, display_name: str, db: Session = Depends(get_db)):
    """
    종류(category)와 표시 이름(display_name)으로 이미지를 검색합니다.
    """
    db_image = image_crud.get_image_by_display_name(db, category=category, display_name=display_name)
    if db_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 이름의 이미지를 찾을 수 없습니다."
        )
    return db_image


@router.put("/update-info/{image_id}", response_model=ImageResponse)
def update_image_info(
        image_id: int,
        new_display_name: str = Form(..., min_length=1),
        db: Session = Depends(get_db)
):
    db_image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not db_image:
        raise HTTPException(...)

    # 수정하려는 새 이름이 "같은 카테고리 내에서" 이미 사용 중인지 확인
    existing_image = image_crud.get_image_by_display_name(
        db,
        category=db_image.category,  # <-- 기존 이미지의 카테고리를 사용
        display_name=new_display_name
    )
    if existing_image and existing_image.id != image_id:
        raise HTTPException(status_code=409, detail="해당 종류에 이미 사용 중인 표시 이름입니다.")

    db_image.display_name = new_display_name
    db.commit()
    db.refresh(db_image)
    return db_image


@router.put("/update-file/{image_id}", response_model=ImageResponse)
def update_image_file(
        image_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    이미지 파일 자체를 교체하고, 기존의 원본 파일은 삭제합니다.
    """
    db_image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    # 1. 삭제할 기존 파일의 object_name을 변수에 저장해 둡니다.
    old_object_name = db_image.object_name

    # 2. 새로운 파일을 먼저 업로드합니다.
    upload_result = minio_service.upload_file(file)
    if not upload_result:
        raise HTTPException(status_code=500, detail="새 파일 업로드에 실패했습니다.")

    # ▼▼▼▼▼ 이 부분이 핵심입니다 ▼▼▼▼▼
    # 3. 새 파일 업로드가 성공하면, 기존 파일을 MinIO에서 삭제합니다.
    if old_object_name:  # 기존 파일 이름이 DB에 있는 경우에만 삭제 시도
        minio_service.delete_file(old_object_name)
    # ▲▲▲▲▲ 여기까지 ▲▲▲▲▲

    # 4. DB 정보를 새로운 파일 정보로 업데이트합니다.
    #    (이전 답변에서 이 로직을 CRUD 함수로 분리했었다면 해당 함수를 호출)
    db_image.object_name = upload_result["object_name"]
    db_image.public_url = upload_result["public_url"]
    db.commit()
    db.refresh(db_image)

    return db_image