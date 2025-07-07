# schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator # field_validator 임포트
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from zoneinfo import ZoneInfo # zoneinfo 임포트


class AdminUserFix(BaseModel):
    # 일반 정보 필드 (모두 선택사항)
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    email: Optional[EmailStr] = None

    # 비밀번호 필드 (선택사항)
    new_password: Optional[str] = None

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        """
        email 필드에 빈 문자열("")이 들어오면 None으로 변환합니다.
        """
        # 입력값이 정확히 빈 문자열일 경우에만 None으로 바꿉니다.
        if v == "":
            return None
        return v

# 회원가입(관리자 생성) 시 받을 데이터
class AdminUserCreate(BaseModel):
    username: str
    password: str
    permission: str
    account_code: str
    company_name: str
    email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        # 입력값이 빈 문자열이면 None으로 변환
        if v == "":
            return None
        return v

# 응답으로 보낼 유저 정보 (비밀번호 제외)
class AdminUserResponse(BaseModel):
    id: int
    username: str
    permission: str
    account_code: str
    company_name: str
    email: Optional[EmailStr] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: datetime
    last_login_at: datetime

    class Config:
        from_attributes = True # SQLAlchemy 모델과 매핑


class PaginatedAdminUserResponse(BaseModel):
    total_count: int
    total_pages: int
    page: int
    size: int
    items: List[AdminUserResponse]

# 기존 Token, TokenData 스키마는 변경할 필요가 없습니다.
# 로그인 시 사용할 주체(subject)를 email에서 username으로 이미 변경했기 때문입니다.
class Token(BaseModel):
    access_token: str
    refresh_token: str
    account_code: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None