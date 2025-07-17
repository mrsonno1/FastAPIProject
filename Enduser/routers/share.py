from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db import models
from core.security import get_current_user
from Enduser.schemas import share as share_schema
from Enduser.crud import share as share_crud

router = APIRouter(tags=["Share"])


@router.post("/share/images", response_model=share_schema.ShareImageResponse)
def create_shared_image(
        item_name: str = Form(..., description="디자인 이름"),
        category: str = Form(..., description="카테고리 (커스텀디자인, 포트폴리오)"),
        image_data: UploadFile = File(..., description="이미지 파일"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """디자인 이미지 등록 및 링크 조회"""

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