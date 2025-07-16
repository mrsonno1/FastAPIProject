from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Manager.admin.schemas import user as user_schema
from Manager.admin.crud import user as user_crud
from db.database import get_db
from core.security import create_access_token, authenticate_user, verify_password, create_refresh_token
from Manager.admin.schemas import user as user_schema # 기존 Token 스키마 재사용

# 새로운 APIRouter 객체 생성
router = APIRouter(
    prefix="/login",  # 이 라우터의 모든 경로는 /login 으로 시작
    tags=["Authentication"],   # FastAPI 문서에서 "Authentication" 그룹으로 묶임
    responses={404: {"description": "Not found"}},
)

@router.post("/token", response_model=user_schema.Token, summary="일반 사용자/관리자 로그인")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    """로그인 API, Access/Refresh 토큰 발급 및 접속시간 갱신"""
    user = user_crud.get_user_by_username(db, username=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.permission not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인 권한이 없습니다."
        )

    # 로그인 성공 시, 마지막 접속 시간 업데이트
    user_crud.update_last_login(db, username=user.username)

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return user_schema.Token(
        access_token=access_token,
        refresh_token=refresh_token,
        account_code=user.account_code
    )