# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.database import get_db
from Manager.admin.schemas import user as user_schema
from Manager.admin.crud import user as user_crud
from core.security import create_access_token, create_refresh_token, get_current_user, verify_password
from db import models
from pydantic import BaseModel # BaseModel 임포트
from jose import JWTError, jwt
from core.config import settings
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

    # 대소문자 구분 없이 검사 (upper로 통일)
    account_code_upper = account_code.strip().upper()
    user = user_crud.get_user_by_account_code_case_insensitive(db, account_code=account_code_upper)
    return {"exists": user is not None}

@router.post("/register", response_model=user_schema.AdminUserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user: user_schema.AdminUserCreate, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """관리자 계정 생성 API - admin/superadmin 권한을 가진 사용자만 생성 가능"""
    
    # 현재 로그인한 사용자의 권한 확인
    if current_user.permission not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="계정 생성 권한이 없습니다. admin 또는 superadmin 권한이 필요합니다."
        )

    # 아이디 중복 검사
    db_user_by_name = user_crud.get_user_by_username(db, username=user.username)
    if db_user_by_name:
        raise HTTPException(status_code=400, detail="이미 등록된 아이디입니다.")
    
    # 계정코드 중복 검사 (대소문자 구분 없이)
    if user.account_code:
        existing_user = user_crud.get_user_by_account_code_case_insensitive(db, account_code=user.account_code)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 계정 코드입니다.")

    # 이메일 중복 검사 제거 - 중복 이메일 허용
    # 이메일은 더 이상 unique하지 않으므로 중복 체크를 하지 않습니다.

    # create_user 함수를 try-except로 감싸서 데이터베이스 오류를 처리합니다.
    try:
        # Pydantic 모델을 딕셔너리로 변환 후 계정코드를 대문자로 변경
        user_data = user.model_dump()
        if user_data.get('account_code'):
            user_data['account_code'] = user_data['account_code'].upper()
        
        # 수정된 데이터로 새로운 Pydantic 모델 생성
        modified_user = user_schema.AdminUserCreate(**user_data)
        new_user = user_crud.create_user(db=db, user=modified_user)
        return new_user
    except IntegrityError as e:
        # 데이터베이스의 UNIQUE 제약 조건 위반 시 실행됩니다.
        db.rollback()  # 트랜잭션을 롤백하여 세션을 깨끗한 상태로 만듭니다.
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # 에러 메시지를 분석하여 적절한 오류 메시지 반환
        if 'account_code' in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail="이미 등록된 계정 코드입니다."
            )
        elif 'username' in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail="이미 등록된 아이디입니다."
            )
        else:
            # 예상치 못한 IntegrityError
            raise HTTPException(
                status_code=409,
                detail=f"데이터 중복 오류: {error_msg}"
            )
    except Exception as e:
        # 그 외 예기치 못한 오류 처리
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"계정 생성 중 예기치 못한 오류가 발생했습니다: {e}"
        )


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


@router.get("/me", response_model=user_schema.AdminUserResponse)
def read_users_me(current_user: models.AdminUser = Depends(get_current_user)):
    """현재 로그인된 사용자 정보 확인 API (토큰 필요)"""
    return current_user


@router.post("/refresh", response_model=user_schema.Token)
def refresh_token(
        refresh_token: str = Header(..., description="Refresh Token"),
        db: Session = Depends(get_db)
):
    """
    Refresh Token을 사용하여 새로운 Access Token과 Refresh Token을 발급받습니다.
    (Refresh Token Rotation 적용)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Refresh Token 검증 (만료, 서명 등)
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 2. DB에서 사용자 정보 확인
    user = user_crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    # 3. 새로운 Access Token 생성
    new_access_token = create_access_token(data={"sub": user.username})

    # 4. (보안 강화) 새로운 Refresh Token도 함께 생성 (Refresh Token Rotation)
    new_refresh_token = create_refresh_token(data={"sub": user.username})

    # Token 스키마에 맞게 응답 반환
    return user_schema.Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )