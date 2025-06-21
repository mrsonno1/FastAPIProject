# schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator # field_validator 임포트
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from zoneinfo import ZoneInfo # zoneinfo 임포트

# 회원가입(관리자 생성) 시 받을 데이터
class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    permission: str
    account_code: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None

# 응답으로 보낼 유저 정보 (비밀번호 제외)
class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    permission: str
    account_code: Optional[str] = None
    company_name: Optional[str] = None
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
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None