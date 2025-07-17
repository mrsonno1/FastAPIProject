from pydantic import BaseModel
from typing import Optional


# 이미지 공유 생성 요청
class ShareImageCreateRequest(BaseModel):
    item_name: str  # 디자인 이름
    category: str  # 카테고리 (커스텀디자인, 포트폴리오)


# 이미지 공유 응답
class ShareImageResponse(BaseModel):
    image_url: str  # 이미지 링크 URL


# 공유된 이미지 정보 응답
class SharedImageDetailResponse(BaseModel):
    item_name: str  # 디자인 이름
    category: str  # 카테고리
    image_url: str  # 이미지 URL


# 이메일 공유 요청
class ShareEmailRequest(BaseModel):
    recipient_email: str  # 받는이 이메일
    image_url: str  # 이미지 URL