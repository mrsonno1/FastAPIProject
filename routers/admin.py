# routers/admin.py
import math # 총 페이지 계산을 위해 math 라이브러리 임포트

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from typing import List, Optional
from db.database import get_db
from schemas import user as user_schema
from crud import user as user_crud
from core.security import get_current_user, verify_password
from db import models


# 새로운 APIRouter 객체 생성
router = APIRouter(
    prefix="/admins",  # 이 라우터의 모든 경로는 /admins로 시작
    tags=["Admins"],   # FastAPI 문서에서 "Admins" 그룹으로 묶임
    responses={404: {"description": "Not found"}},
)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    (superadmin 전용) ID로 특정 관리자 계정을 삭제합니다.
    자기 자신은 삭제할 수 없습니다.
    """
    # 1. 관리자 권한 확인
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자를 삭제할 권한이 없습니다."
        )

    # 2. 자기 자신 삭제 시도 방지
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신의 계정은 삭제할 수 없습니다."
        )

    # 3. 삭제할 대상 사용자 조회
    user_to_delete = user_crud.get_user_by_id(db, user_id=user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="삭제할 사용자를 찾을 수 없습니다.")

    # (선택사항) 삭제 대상이 superadmin인 경우 방지
    if user_to_delete.permission == 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="superadmin 계정은 삭제할 수 없습니다."
        )

    # 4. CRUD 함수 호출하여 삭제
    was_deleted = user_crud.delete_admin_user_by_id(db, user_id=user_id)

    # 이 부분은 이론적으로 위에서 이미 확인했으므로 도달하기 어렵지만, 안전장치로 둡니다.
    if not was_deleted:
        raise HTTPException(status_code=404, detail="삭제 중 오류가 발생했습니다.")

    # 5. 성공 시 204 응답
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/fix/{username}", response_model=user_schema.AdminUserResponse)
def fix_user_info_by_username(  # 함수 이름도 변경
        username: str,  # 경로 변수를 user_id: int 에서 username: str 로 변경
        user_fix: user_schema.AdminUserFix,
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user)
):
    """
    (관리자 전용) 아이디(username)로 특정 관리자 계정의 정보를 수정합니다.
    """
    # 1. 권한 검사
    if current_user.permission not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 정보를 수정할 권한이 없습니다."
        )

    # 2. 수정할 대상 사용자 조회 (ID 대신 username으로 조회)
    user_to_update = user_crud.get_user_by_username(db, username=username)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="수정할 사용자를 찾을 수 없습니다.")



    # 4. CRUD 함수 호출하여 업데이트
    return user_crud.fix_admin_user(db, db_user=user_to_update, user_fix=user_fix)


@router.get("/list", response_model=user_schema.PaginatedAdminUserResponse)
def list_all_admin_users(
        # 페이지네이션 파라미터
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),

        # ▼▼▼▼▼ 선택적 검색 파라미터 추가 ▼▼▼▼▼
        id: Optional[str] = Query(None, description="아이디로 검색"),
        permission: Optional[str] = Query(None, description="권한으로 검색"),
        username: Optional[str] = Query(None, min_length=1, description="이름으 검색"),
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
        id=id,  # <-- 추가
        permission=permission,
        username=username,
        company_name=company_name,
        contact_name=contact_name,
        contact_phone=contact_phone
    )

    items = paginated_data["items"]
    total_count = paginated_data["total_count"]

    total_pages = math.ceil(total_count / size) if total_count > 0 else 1


    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }