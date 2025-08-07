
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class UserMeResponse(BaseModel):
    """내 정보 조회 응답 스키마"""
    username: str
    permission: str
    company_name: str
    email: str
    contact_name: str
    contact_phone: str

    class Config:
        from_attributes = True

class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답 스키마"""
    access_token: str
    refresh_token: str

class UserUpdateRequest(BaseModel):
    """내 정보 수정 요청 스키마"""
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None  # EmailStr 대신 str 사용
    new_password: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """이메일 유효성 검사 - 빈 문자열은 None으로 처리"""
        if v == "":
            return None
        if v is not None:
            # 이메일 형식 검증
            from email_validator import validate_email, EmailNotValidError
            try:
                validate_email(v)
            except EmailNotValidError:
                raise ValueError("유효한 이메일 주소를 입력해주세요.")
        return v

class UserUpdateResponse(BaseModel):
    """내 정보 수정 응답 스키마"""
    username: str
    permission: str
    company_name: str
    email: str
    contact_name: str
    contact_phone: str

    class Config:
        from_attributes = True
