# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import user as user_schema
from crud import user as user_crud
from core.security import create_access_token, create_refresh_token, get_current_user, verify_password
from db import models
from pydantic import BaseModel # BaseModel 임포트

router = APIRouter(prefix="/auth", tags=["Auth"])


# 중복 검사 응답을 위한 Pydantic 모델
class DuplicationCheckResponse(BaseModel):
    exists: bool


@router.get("/check/username", response_model=DuplicationCheckResponse, tags=["Validation"])
def check_username_duplicate(username: str, db: Session = Depends(get_db)):
    """
    아이디(username)가 이미 존재하는지 실시간으로 확인합니다.
    - 존재하면 {"exists": true}
    - 존재하지 않으면 {"exists": false}
    """
    user = user_crud.get_user_by_username(db, username=username)
    return {"exists": user is not None}


@router.get("/check/account-code", response_model=DuplicationCheckResponse, tags=["Validation"])
def check_account_code_duplicate(account_code: str, db: Session = Depends(get_db)):
    """
    계정코드가 이미 존재하는지 실시간으로 확인합니다.
    - 존재하면 {"exists": true}
    - 존재하지 않으면 {"exists": false}
    """
    # 계정코드는 비어있을 수 있으므로, 값이 있는 경우에만 검사합니다.
    if not account_code.strip():
        return {"exists": False}

    user = user_crud.get_user_by_account_code(db, account_code=account_code)
    return {"exists": user is not None}

@router.post("/register", response_model=user_schema.AdminUserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: user_schema.AdminUserCreate, db: Session = Depends(get_db)):
    """관리자 계정 생성 API"""
    db_user_by_name = user_crud.get_user_by_username(db, username=user.username)
    if db_user_by_name:
        raise HTTPException(status_code=400, detail="이미 등록된 아이디입니다.")

    db_user_by_email = user_crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    return user_crud.create_user(db=db, user=user)


@router.post("/login", response_model=user_schema.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):

    """로그인 API, Access/Refresh 토큰 발급 및 접속시간 갱신"""
    user = user_crud.get_user_by_username(db, username=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 로그인 성공 시, 마지막 접속 시간 업데이트
    user_crud.update_last_login(db, username=user.username)

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=user_schema.AdminUserResponse)
def read_users_me(current_user: models.AdminUser = Depends(get_current_user)):
    """현재 로그인된 사용자 정보 확인 API (토큰 필요)"""
    return current_user