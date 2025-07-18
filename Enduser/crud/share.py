from sqlalchemy.dialects.postgresql import Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from db import models
from typing import Optional, Union
import uuid
import hashlib
from services.storage_service import storage_service
from fastapi import UploadFile


def generate_unique_image_id(user_id: str, item_name: str, category: str) -> str:
    """고유한 이미지 ID 생성"""
    # 사용자ID, 아이템명, 카테고리를 조합하여 해시 생성
    combined_string = f"{user_id}_{item_name}_{category}"
    hash_object = hashlib.md5(combined_string.encode())
    return hash_object.hexdigest()[:12]  # 12자리만 사용


def create_or_get_shared_image(
        db: Session,
        user_id: str,
        item_name: str,
        category: str,
        image_file: Union[UploadFile, dict]  # UploadFile 또는 dict (base64 데이터)
) -> Optional[str]:
    """공유 이미지 생성 또는 기존 이미지 URL 반환"""

    # 기존 공유 이미지가 있는지 확인
    existing_share = db.query(models.Share).filter(
        and_(
            models.Share.user_id == user_id,
            models.Share.item_name == item_name,
            models.Share.category == category
        )
    ).first()

    if existing_share:
        return existing_share.image_url

    # 이미지 업로드
    if isinstance(image_file, UploadFile):
        # 기존 파일 업로드 방식
        upload_result = storage_service.upload_file(image_file)
    else:
        # Base64 업로드 방식 (dict 형태로 전달됨)
        upload_result = storage_service.upload_base64_file(
            file_data=image_file['data'],
            filename=image_file['filename'],
            content_type=image_file['content_type']
        )

    if not upload_result:
        return None

    # 고유 ID 생성
    image_id = generate_unique_image_id(user_id, item_name, category)

    # 중복 체크 (극히 드물지만 해시 충돌 가능성)
    while db.query(models.Share).filter(models.Share.image_id == image_id).first():
        image_id = str(uuid.uuid4())[:12]

    # Share 레코드 생성
    new_share = models.Share(
        image_id=image_id,
        user_id=user_id,
        item_name=item_name,
        category=category,
        image_url=upload_result["public_url"],
        object_name=upload_result["object_name"]
    )

    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return new_share.image_url


def get_shared_image_detail(db: Session, image_id: str) -> Optional[models.Share]:
    """공유된 이미지 정보 조회"""

    return db.query(models.Share).filter(
        models.Share.image_id == image_id
    ).first()


def send_share_email(
        recipient_email: str,
        image_url: str,
        image_id: str
) -> bool:
    """이미지 공유 이메일 전송"""

    from Enduser.Email import send_email_endpoint
    from pydantic import BaseModel, EmailStr

    class EmailSchema(BaseModel):
        to_email: EmailStr
        subject: str
        body: str

    # 공유 링크 생성
    share_link = f"https://yourdomain.com/share/{image_id}"

    email_data = EmailSchema(
        to_email=recipient_email,
        subject="LensGrapick 디자인 공유",
        body=f"""
안녕하세요,

LensGrapick에서 디자인을 공유해드립니다.

이미지 링크: {image_url}
공유 페이지: {share_link}

감사합니다.
LensGrapick 팀
        """
    )

    try:
        # Email 모듈의 send_email_endpoint 함수 호출
        result = send_email_endpoint(email_data)
        return True
    except Exception as e:
        print(f"이메일 전송 실패: {e}")
        return False