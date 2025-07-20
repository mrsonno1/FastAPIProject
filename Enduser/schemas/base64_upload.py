# Enduser/schemas/base64_upload.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import base64
import re


class Base64File(BaseModel):
    """Base64로 인코딩된 파일 데이터"""
    filename: str = Field(..., description="파일명 (예: image.png)")
    content_type: str = Field(..., description="파일 MIME 타입 (예: image/png)")
    data: str = Field(..., description="Base64로 인코딩된 파일 데이터")

    @field_validator('data')
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Base64 데이터 유효성 검사"""
        # data:image/png;base64, 형식의 prefix 제거
        if v.startswith('data:'):
            v = v.split(',')[1] if ',' in v else v

        # Base64 유효성 검사
        try:
            # 패딩 추가 (필요한 경우)
            missing_padding = len(v) % 4
            if missing_padding:
                v += '=' * (4 - missing_padding)

            # 디코딩 테스트
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("유효하지 않은 Base64 데이터입니다.")

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """이미지 MIME 타입만 허용"""
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if v not in allowed_types:
            raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_types)}")
        return v

    def to_bytes(self) -> bytes:
        """Base64 데이터를 바이트로 변환"""
        return base64.b64decode(self.data)


class CustomDesignCreateWithBase64(BaseModel):
    """Base64 이미지를 포함한 커스텀 디자인 생성 요청"""
    # item_name과 color_name 제거 - 자동 생성됨
    design_line_image_id: Optional[str] = Field(None, description="라인 이미지 ID")
    design_line_color_id: Optional[str] = Field(None, description="라인 색상 ID")
    line_transparency: Optional[str] = Field("100", description="라인 투명도")
    line_size: Optional[str] = Field("100", description="라인 크기")
    design_base1_image_id: Optional[str] = Field(None, description="바탕1 이미지 ID")
    design_base1_color_id: Optional[str] = Field(None, description="바탕1 색상 ID")
    base1_transparency: Optional[str] = Field("100", description="바탕1 투명도")
    base1_size: Optional[str] = Field("100", description="바탕1 크기")
    design_base2_image_id: Optional[str] = Field(None, description="바탕2 이미지 ID")
    design_base2_color_id: Optional[str] = Field(None, description="바탕2 색상 ID")
    base2_transparency: Optional[str] = Field("100", description="바탕2 투명도")
    base2_size: Optional[str] = Field("100", description="바탕2 크기")
    design_pupil_image_id: Optional[str] = Field(None, description="동공 이미지 ID")
    design_pupil_color_id: Optional[str] = Field(None, description="동공 색상 ID")
    pupil_transparency: Optional[str] = Field("100", description="동공 투명도")
    pupil_size: Optional[str] = Field("100", description="동공 크기")
    graphic_diameter: Optional[str] = Field(None, description="그래픽 직경")
    optic_zone: Optional[str] = Field(None, description="옵틱 존")
    request_message: Optional[str] = Field(None, description="요청 메시지")
    main_image: Optional[Base64File] = Field(None, description="메인 이미지 (Base64)")


class ShareImageCreateWithBase64(BaseModel):
    """Base64 이미지를 포함한 공유 이미지 생성 요청"""
    item_name: str = Field(..., description="디자인 이름")
    category: str = Field(..., description="카테고리 (커스텀디자인, 포트폴리오)")
    image_data: Base64File = Field(..., description="이미지 데이터 (Base64)")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in ['커스텀디자인', '포트폴리오']:
            raise ValueError("카테고리는 '커스텀디자인' 또는 '포트폴리오'여야 합니다.")
        return v