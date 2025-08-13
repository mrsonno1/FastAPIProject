from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Manager.admin.schemas import user as user_schema
from Manager.admin.crud import user as user_crud
from db.database import get_db
from db import models
from core.security import get_current_user, create_access_token, verify_token, verify_password, create_refresh_token
from Manager.admin.schemas import user as user_schema # 기존 Token 스키마 재사용
from Enduser.schemas import login as login_schema
from Enduser.crud import login as login_crud

# 새로운 APIRouter 객체 생성
router = APIRouter(
    prefix="/login",  # 이 라우터의 모든 경로는 /login 으로 시작
    tags=["Authentication"],   # FastAPI 문서에서 "Authentication" 그룹으로 묶임
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=user_schema.Token, summary="일반 사용자/관리자 로그인")
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

    # 로그인 성공 시, 마지막 접속 시간 업데이트
    user_crud.update_last_login(db, username=user.username)
    
    # 로그인 시 언어 설정을 항상 한국어('ko')로 초기화
    user.language_preference = 'ko'
    db.commit()

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # 언어 설정은 항상 'ko'로 반환
    language_preference = 'ko'

    return user_schema.Token(
        access_token=access_token,
        refresh_token=refresh_token,
        account_code=user.account_code,
        language_preference=language_preference
    )


@router.get("/me", response_model=login_schema.UserMeResponse)
def get_my_info(
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """내 정보 조회"""
    return login_schema.UserMeResponse(
        username=current_user.username,
        permission=current_user.permission,
        company_name=current_user.company_name or "",
        email=current_user.email or "",
        contact_name=current_user.contact_name or "",
        contact_phone=current_user.contact_phone or ""
    )


@router.post("/refresh", response_model=login_schema.TokenRefreshResponse)
def refresh_token(
        refresh_token: str = Header(..., alias="refresh-token"),
        db: Session = Depends(get_db)
):
    """사용자 토큰 갱신"""
    try:
        # 리프레시 토큰 검증
        payload = verify_token(refresh_token)
        username = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # 사용자 조회
        user = login_crud.get_user_by_username(db, username=username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # 새 토큰 생성
        new_access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token(data={"sub": user.username})

        return login_schema.TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.put("/me", response_model=login_schema.UserUpdateResponse)
def update_my_info(
        user_update: login_schema.UserUpdateRequest,
        current_user: models.AdminUser = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """내 정보 수정"""

    # 이메일 중복 검사 제거 - 중복 이메일 허용
    # 이메일은 더 이상 unique하지 않으므로 중복 체크를 하지 않습니다.

    # 업데이트할 데이터 준비 - 빈 문자열("")은 None으로 변환되어 전달됨
    # model_dump를 사용하여 설정된 필드만 가져옴 (exclude_unset=True)
    update_data = user_update.model_dump(exclude_unset=True, exclude_none=False)
    
    # new_password가 None인 경우 제거 (비밀번호는 None으로 설정할 수 없음)
    if "new_password" in update_data and update_data["new_password"] is None:
        update_data.pop("new_password")

    # 사용자 정보 업데이트
    updated_user = login_crud.update_user_info(db, current_user, update_data)

    return login_schema.UserUpdateResponse(
        username=updated_user.username,
        permission=updated_user.permission,
        company_name=updated_user.company_name or "",
        email=updated_user.email or "",
        contact_name=updated_user.contact_name or "",
        contact_phone=updated_user.contact_phone or ""
    )
