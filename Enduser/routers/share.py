from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import share as share_schema
from Enduser.schemas import base64_upload as base64_schema  # 추가
from Enduser.crud import share as share_crud
from services.storage_service import storage_service

router = APIRouter(tags=["Share"])


# 기존 Form/File 업로드 방식 (하위 호환성 유지)
@router.post("/share/images", response_model=share_schema.ShareImageResponse)
def create_shared_image(
        item_name: str = Form(..., description="디자인 이름"),
        category: str = Form(..., description="카테고리 (커스텀디자인, 포트폴리오)"),
        image_data: UploadFile = File(..., description="이미지 파일"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """디자인 이미지 등록 및 링크 조회 - File 업로드 방식"""

    # 카테고리 검증
    if category not in ['커스텀디자인', '포트폴리오']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다."
        )

    # 해당 아이템이 실제로 존재하는지 확인
    if category == '커스텀디자인':
        design = db.query(models.CustomDesign).filter(
            models.CustomDesign.item_name == item_name,
            models.CustomDesign.user_id == current_user.username
        ).first()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 커스텀디자인을 찾을 수 없습니다."
            )
    else:
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.design_name == item_name,
            models.Portfolio.is_deleted == False
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 포트폴리오를 찾을 수 없습니다."
            )

    # 공유 이미지 생성 또는 기존 URL 반환
    image_url = share_crud.create_or_get_shared_image(
        db=db,
        user_id=current_user.username,
        item_name=item_name,
        category=category,
        image_file=image_data
    )

    if not image_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 업로드에 실패했습니다."
        )

    return share_schema.ShareImageResponse(image_url=image_url)


# 새로운 Base64 업로드 방식
@router.post("/share/images/base64", response_model=share_schema.ShareImageResponse)
def create_shared_image_base64(
        share_data: base64_schema.ShareImageCreateWithBase64,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """디자인 이미지 등록 및 링크 조회 - Base64 업로드 방식 (Unity용)"""

    # 해당 아이템이 실제로 존재하는지 확인
    if share_data.category == '커스텀디자인':
        design = db.query(models.CustomDesign).filter(
            models.CustomDesign.item_name == share_data.item_name,
            models.CustomDesign.user_id == current_user.username
        ).first()

        if not design:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 커스텀디자인을 찾을 수 없습니다."
            )
    else:
        portfolio = db.query(models.Portfolio).filter(
            models.Portfolio.design_name == share_data.item_name,
            models.Portfolio.is_deleted == False
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 포트폴리오를 찾을 수 없습니다."
            )

    # 기존 공유 이미지가 있는지 확인
    existing_share = db.query(models.Share).filter(
        models.Share.user_id == current_user.username,
        models.Share.item_name == share_data.item_name,
        models.Share.category == share_data.category
    ).first()

    if existing_share:
        return share_schema.ShareImageResponse(image_url=existing_share.image_url)

    # Base64 이미지 업로드
    try:
        # Base64 데이터를 바이트로 변환
        image_bytes = share_data.image_data.to_bytes()

        # Storage Service를 통해 업로드
        upload_result = storage_service.upload_base64_file(
            file_data=image_bytes,
            filename=share_data.image_data.filename,
            content_type=share_data.image_data.content_type
        )

        if not upload_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이미지 업로드에 실패했습니다."
            )

        # 고유 ID 생성
        image_id = share_crud.generate_unique_image_id(
            current_user.username,
            share_data.item_name,
            share_data.category
        )

        # 중복 체크
        import uuid
        while db.query(models.Share).filter(models.Share.image_id == image_id).first():
            image_id = str(uuid.uuid4())[:12]

        # Share 레코드 생성
        new_share = models.Share(
            image_id=image_id,
            user_id=current_user.username,
            item_name=share_data.item_name,
            category=share_data.category,
            image_url=upload_result["public_url"],
            object_name=upload_result["object_name"]
        )

        db.add(new_share)
        db.commit()
        db.refresh(new_share)

        return share_schema.ShareImageResponse(image_url=new_share.image_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이미지 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/share/images/{image_id}", response_model=share_schema.SharedImageDetailResponse)
def get_shared_image(
        image_id: str,
        db: Session = Depends(get_db)
):
    """공유된 디자인 이미지 조회 (인증 불필요)"""

    shared_image = share_crud.get_shared_image_detail(
        db=db,
        image_id=image_id
    )

    if not shared_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공유된 이미지를 찾을 수 없습니다."
        )

    return share_schema.SharedImageDetailResponse(
        item_name=shared_image.item_name,
        category=shared_image.category,
        image_url=shared_image.image_url
    )


@router.post("/share/email/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def share_image_by_email(
        image_id: str,
        email_data: share_schema.ShareEmailRequest,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """디자인 이미지 링크 이메일로 공유"""

    # 공유된 이미지 확인
    shared_image = share_crud.get_shared_image_detail(
        db=db,
        image_id=image_id
    )

    if not shared_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공유된 이미지를 찾을 수 없습니다."
        )

    # 이메일 전송
    success = share_crud.send_share_email(
        recipient_email=email_data.recipient_email,
        image_url=email_data.image_url,
        image_id=image_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이메일 전송에 실패했습니다."
        )

    return