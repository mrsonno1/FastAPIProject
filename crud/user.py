# crud/user.py
from sqlalchemy.orm import Session
from datetime import datetime
from datetime import datetime, timezone # timezone을 임포트합니다.
from zoneinfo import ZoneInfo # zoneinfo 임포트
from db import models
from schemas import user as user_schema
from core.security import get_password_hash

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


def get_users_paginated(db: Session, page: int, size: int):
    """
    모든 관리자 계정 목록을 페이지네이션하여 가져옵니다.
    """
    # 1. 건너뛸 항목 수를 계산합니다. (페이지 1이면 0개, 페이지 2이면 size만큼 건너뜀)
    offset = (page - 1) * size

    # 2. 전체 항목 수를 계산하기 위한 쿼리
    total_count = db.query(models.AdminUser).count()

    # 3. 실제 페이지에 해당하는 데이터만 가져오는 쿼리 (offset과 limit 사용)
    items = db.query(models.AdminUser).offset(offset).limit(size).all()

    # 4. 데이터 목록과 전체 개수를 딕셔너리로 반환
    return {"items": items, "total_count": total_count}