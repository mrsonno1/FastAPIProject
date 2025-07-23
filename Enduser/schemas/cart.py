from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 장바구니 카운트 응답
class CartCountResponse(BaseModel):
    count: int  # 장바구니에 담긴 상품 개수


# 장바구니 아이템
class CartItem(BaseModel):
    item_name: str  # 디자인 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    account_code: str  # account_code 추가
    category: str  # 카테고리 (커스텀디자인, 포트폴리오)

    class Config:
        from_attributes = True


# 장바구니 목록 응답
class CartListResponse(BaseModel):
    items: List[CartItem]


# 장바구니 추가 요청
class CartAddRequest(BaseModel):
    item_name: str  # 디자인 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    category: str  # 카테고리 (커스텀디자인, 포트폴리오)


# 장바구니 삭제 요청
class CartDeleteRequest(BaseModel):
    category: str  # 카테고리 (커스텀디자인, 포트폴리오)


# Progress Status 생성 요청
class CartToProgressRequest(BaseModel):
    client_name: str  # 받는사람
    number: str  # 연락처
    address: str  # 주소
    request_date: Optional[datetime] = None  # 요청일 (없으면 현재시간)