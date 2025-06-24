# routers/admin.py
import math # 총 페이지 계산을 위해 math 라이브러리 임포트
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List # List 타입을 임포트합니다.
from typing import List, Optional
from db.database import get_db
from schemas import user as user_schema
from crud import user as user_crud
from core.security import get_current_user
from db import models

# 새로운 APIRouter 객체 생성
router = APIRouter(
    prefix="/admins",  # 이 라우터의 모든 경로는 /admins로 시작
    tags=["Admins"],   # FastAPI 문서에서 "Admins" 그룹으로 묶임
    responses={404: {"description": "Not found"}},
)

@router.get("/by-username/{username}", response_model=user_schema.AdminUserResponse)
def read_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """
    사용자 아이디(username)로 특정 관리자 정보 조회.
    인증된 사용자만 접근 가능합니다.
    """
    db_user = user_crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="해당 아이디의 사용자를 찾을 수 없습니다.")
    return db_user


@router.get("/by-contact-name/", response_model=List[user_schema.AdminUserResponse])
def read_users_by_contact_name(
        name: str = Query(..., min_length=1, description="검색할 담당자 이름"),
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    담당자 이름(contact_name)의 일부를 포함하는 모든 사용자 목록을 조회합니다.
    (예: '민수'로 검색)
    """
    # 권한 검사를 원한다면 여기에 추가할 수 있습니다.
    # if current_user.permission != 'admin':
    #     raise HTTPException(status_code=403, detail="권한이 없습니다.")

    users = user_crud.get_users_by_contact_name(db, name=name)
    if not users:
        # 검색 결과가 없는 것은 에러가 아니므로, 빈 리스트를 반환하는 것이 일반적입니다.
        # 혹은 404 에러를 발생시켜도 됩니다.
        return []

    return users


@router.get("/by-id/{user_id}", response_model=user_schema.AdminUserResponse)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(get_current_user)
):
    """
    사용자 고유 ID(PK, index)로 특정 관리자 정보 조회.
    인증된 사용자만 접근 가능합니다.
    """
    db_user = user_crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="해당 ID의 사용자를 찾을 수 없습니다.")
    return db_user


@router.get("/list", response_model=user_schema.PaginatedAdminUserResponse)
def list_all_admin_users(
        # 페이지네이션 파라미터
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),

        # ▼▼▼▼▼ 선택적 검색 파라미터 추가 ▼▼▼▼▼
        permission: Optional[str] = Query(None, description="권한으로 검색"),
        username: Optional[str] = Query(None, min_length=1, description="아이디로 검색"),
        company_name: Optional[str] = Query(None, min_length=1, description="소속사업자명으로 검색"),
        contact_name: Optional[str] = Query(None, min_length=1, description="담당자명으로 검색"),
        contact_phone: Optional[str] = Query(None, min_length=1, description="담당자연락처로 검색"),

        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    모든 관리자 계정 목록을 검색 조건과 함께 페이지네이션하여 조회합니다.
    """
    # 1단계에서 수정한 권한 검사 로직
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 작업을 수행할 권한이 없습니다."
        )

    # 수정된 CRUD 함수 호출
    paginated_data = user_crud.get_admin_users_paginated(
        db,
        page=page,
        size=size,
        permission=permission,
        username=username,
        company_name=company_name,
        contact_name=contact_name,
        contact_phone=contact_phone
    )

    items = paginated_data["items"]
    total_count = paginated_data["total_count"]

    total_pages = math.ceil(total_count / size) if total_count > 0 else 1

    # PaginatedAdminUserResponse 스키마를 사용한다고 가정합니다.
    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }