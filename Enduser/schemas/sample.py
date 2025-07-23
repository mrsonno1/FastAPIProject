from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


# 디자인 컴포넌트 정보
class DesignComponent(BaseModel):
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    image_name: Optional[str] = None
    RGB_id: Optional[str] = None
    RGB_color: Optional[str] = None
    RGB_name: Optional[str] = None
    size: Optional[int] = 100
    opacity: Optional[int] = 100


# 샘플 목록 아이템
class SampleListItem(BaseModel):
    id: int  # progressstatus id
    item_name: str  # 디자인 이름
    main_image_url: Optional[str] = None  # 메인 이미지 URL
    category: str  # 카테고리 (커스텀디자인, 포트폴리오)
    design_line: Optional[DesignComponent] = None
    design_base1: Optional[DesignComponent] = None
    design_base2: Optional[DesignComponent] = None
    design_pupil: Optional[DesignComponent] = None
    graphic_diameter: Optional[str] = None
    optic_zone: Optional[str] = None
    created_at: datetime  # 요청일
    estimated_ship_date: Optional[date] = None  # 발송 예정일
    status: str  # 진행 현황
    shipped_date: Optional[datetime] = None  # 발송일
    request_note: Optional[str] = None  # 요청사항
    account_code: Optional[str] = None  # account_code 추가

    class Config:
        from_attributes = True


# 샘플 목록 응답
class PaginatedSampleResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[SampleListItem]


# 샘플 상세 정보 응답
class SampleDetailResponse(BaseModel):
    recipient_name: Optional[str] = None  # 받는이
    recipient_phone: Optional[str] = None  # 연락처
    recipient_address: Optional[str] = None  # 주소
    tracking_number: Optional[str] = None  # 송장번호
    request_note: Optional[str] = None  # 요청사항


# Progress Status 생성 요청 (Form 데이터용)
class SampleCreateRequest(BaseModel):
    client_name: str  # 받는사람
    number: str  # 연락처
    address: str  # 주소
    request_date: Optional[datetime] = None  # 요청일 (없으면 현재시간)


# 샘플 요청 결과
class SampleResultResponse(BaseModel):
    result: str  # 결과 메시지


# 일괄 샘플 요청 결과
class BulkSampleResultResponse(BaseModel):
    result: str  # 결과 메시지
    success_count: int  # 성공한 개수
    failed_count: int  # 실패한 개수
    failed_items: List[str] = []  # 실패한 아이템 목록