
from pydantic import BaseModel, EmailStr
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
    email: Optional[EmailStr] = None
    new_password: Optional[str] = None

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
