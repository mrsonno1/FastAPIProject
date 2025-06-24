# crud/user.py
from sqlalchemy.orm import Session
from datetime import datetime
from datetime import datetime, timezone # timezone을 임포트합니다.
from zoneinfo import ZoneInfo # zoneinfo 임포트
from db import models
from schemas import user as user_schema
from core.security import get_password_hash
from typing import Optional


def get_user_by_username(db: Session, username: str):
    """아이디로 사용자 정보 조회"""
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

def get_user_by_account_code(db: Session, account_code: str):
    """계정코드로 사용자 정보 조회"""
    # 계정코드는 NULL일 수 있으므로, 비어있지 않은 경우에만 조회합니다.
    if not account_code:
        return None
    return db.query(models.AdminUser).filter(models.AdminUser.account_code == account_code).first()

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 정보 조회"""
    return db.query(models.AdminUser).filter(models.AdminUser.email == email).first()

def create_user(db: Session, user: user_schema.AdminUserCreate):
    """새로운 관리자 사용자 생성"""
    hashed_password = get_password_hash(user.password)
    db_user = models.AdminUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password, # 모델의 변수명 사용
        account_code=user.account_code,
        permission=user.permission,
        company_name=user.company_name,
        contact_name=user.contact_name,
        contact_phone=user.contact_phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user



def update_last_login(db: Session, username: str):
    """ 마지막 접속 시간 업데이트 (안정적인 UTC 기반 방식으로 최종 수정)"""
    utc_now = datetime.now(timezone.utc)
    db.query(models.AdminUser).filter(models.AdminUser.username == username).update(
        {models.AdminUser.last_login_at: utc_now},  # UTC 시간 그대로 저장
        synchronize_session=False
    )
    db.commit()

def get_user_by_id(db: Session, user_id: int):
    """사용자 PK(index)로 사용자 정보 조회"""
    return db.query(models.AdminUser).filter(models.AdminUser.id == user_id).first()

def get_users_by_contact_name(db: Session, name: str):
    """
    담당자명(contact_name)으로 사용자 목록을 검색 (LIKE 검색)
    """
    search_pattern = f"%{name}%"
    return db.query(models.AdminUser).filter(models.AdminUser.contact_name.like(search_pattern)).all()



def get_admin_users_paginated(
    db: Session,
    page: int,
    size: int,
    permission: Optional[str] = None,
    username: Optional[str] = None,
    company_name: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_phone: Optional[str] = None
):
    """
    관리자 계정 목록을 검색 조건과 함께 페이지네이션하여 가져옵니다.
    """
    # 1. 기본 쿼리를 시작합니다.
    query = db.query(models.AdminUser)

    # 2. 검색 조건이 제공되면, 동적으로 filter를 추가합니다.
    if permission:
        query = query.filter(models.AdminUser.permission == permission)
    if username:
        # 부분 일치 검색 (LIKE)
        query = query.filter(models.AdminUser.username.like(f"%{username}%"))
    if company_name:
        query = query.filter(models.AdminUser.company_name.like(f"%{company_name}%"))
    if contact_name:
        query = query.filter(models.AdminUser.contact_name.like(f"%{contact_name}%"))
    if contact_phone:
        query = query.filter(models.AdminUser.contact_phone.like(f"%{contact_phone}%"))

    # 3. 필터가 적용된 쿼리에서 전체 항목 수를 계산합니다.
    total_count = query.count()

    # 4. 순서 정렬 및 페이지네이션을 적용하여 실제 데이터를 가져옵니다.
    offset = (page - 1) * size
    items = query.order_by(models.AdminUser.id.desc()).offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}