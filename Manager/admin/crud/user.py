# crud/user.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone # timezone을 임포트합니다.
from db import models
from sqlalchemy import func
from Manager.admin.schemas import user as user_schema

from typing import Optional


def get_user_by_username(db: Session, username: str):
    """아이디로 사용자 정보 조회 (삭제되지 않은 사용자만)"""
    return db.query(models.AdminUser).filter(
        models.AdminUser.username == username,
        models.AdminUser.is_deleted == False
    ).first()


def get_user_by_account_code(db: Session, account_code: str):
    """계정코드로 사용자 정보 조회 (삭제되지 않은 사용자만)"""
    # 계정코드는 NULL일 수 있으므로, 비어있지 않은 경우에만 조회합니다.
    if not account_code:
        return None
    return db.query(models.AdminUser).filter(
        models.AdminUser.account_code == account_code,
        models.AdminUser.is_deleted == False
    ).first()

def get_user_by_account_code_case_insensitive(db: Session, account_code: str):
    """계정코드로 사용자 정보 조회 - 대소문자 구분 없음 (삭제되지 않은 사용자만)"""
    # 계정코드는 NULL일 수 있으므로, 비어있지 않은 경우에만 조회합니다.
    if not account_code:
        return None
    return db.query(models.AdminUser).filter(
        func.upper(models.AdminUser.account_code) == account_code.upper(),
        models.AdminUser.is_deleted == False
    ).first()


def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 정보 조회 (삭제되지 않은 사용자만)"""
    return db.query(models.AdminUser).filter(
        models.AdminUser.email == email,
        models.AdminUser.is_deleted == False
    ).first()


def create_user(db: Session, user: user_schema.AdminUserCreate):
    """새로운 관리자 사용자 생성"""
    from core.security import get_password_hash
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


def delete_admin_user_by_id(db: Session, user_id: int) -> bool:
    """
    ID로 관리자 계정을 찾아 소프트 삭제합니다.
    :return: 삭제 성공 시 True, 해당 객체가 없을 시 False
    """
    db_user = db.query(models.AdminUser).filter(
        models.AdminUser.id == user_id,
        models.AdminUser.is_deleted == False  # 이미 삭제되지 않은 사용자만
    ).first()
    if db_user:
        db_user.is_deleted = True  # 소프트 삭제
        db.commit()
        return True
    return False


def fix_admin_user(db: Session, db_user: models.AdminUser, user_fix: user_schema.AdminUserFix):
    """
    관리자 계정의 정보를 선택적으로 업데이트합니다. (단순화된 버전)
    """
    # 1. Pydantic 모델에서 사용자가 보낸 값들만 딕셔너리로 추출합니다.
    # exclude_none=False를 사용하여 None 값도 포함시킵니다 (빈 문자열이 None으로 변환된 경우 처리)
    update_data = user_fix.model_dump(exclude_unset=True, exclude_none=False)

    from core.security import get_password_hash
    # 2. 비밀번호가 있다면, 해싱하여 딕셔너리 값을 교체합니다.
    if "new_password" in update_data and update_data["new_password"]:
        # 'new_password' 키를 DB 모델의 속성명인 'password'로 바꾸고, 값을 해싱합니다.
        update_data["hashed_password"] = get_password_hash(update_data.pop("new_password"))
    elif "new_password" in update_data:
        # new_password가 None이면 제거 (비밀번호는 None으로 설정할 수 없음)
        update_data.pop("new_password")

    # 3. 이메일이 변경되려는 경우, 중복 확인을 건너뜁니다 (중복 허용)
    # 이메일 중복 체크를 제거하여 같은 이메일을 여러 계정이 가질 수 있도록 합니다.
    
    # 4. 딕셔너리의 각 키-값 쌍에 대해 DB 모델 객체의 속성을 업데이트합니다.
    #    이제 모든 키 이름이 모델 속성 이름과 일치하므로 분기문이 필요 없습니다.
    for key, value in update_data.items():
        setattr(db_user, key, value)

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
    """사용자 PK(index)로 사용자 정보 조회 (삭제되지 않은 사용자만)"""
    return db.query(models.AdminUser).filter(
        models.AdminUser.id == user_id,
        models.AdminUser.is_deleted == False
    ).first()


def get_users_by_contact_name(db: Session, name: str):
    """
    담당자명(contact_name)으로 사용자 목록을 검색 (LIKE 검색) - 삭제되지 않은 사용자만
    """
    search_pattern = f"%{name}%"
    return db.query(models.AdminUser).filter(
        models.AdminUser.contact_name.like(search_pattern),
        models.AdminUser.is_deleted == False
    ).all()


def get_admin_users_paginated(
        db: Session,
        page: int,
        size: int,
        id: Optional[int] = None,
        permission: Optional[str] = None,
        username: Optional[str] = None,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None  # <-- 이 파라미터를 처리하는 로직 변경
):
    """
    관리자 계정 목록을 검색 조건과 함께 페이지네이션하여 가져옵니다. (삭제되지 않은 사용자만)
    """
    query = db.query(models.AdminUser).filter(models.AdminUser.is_deleted == False)

    if id is not None:
        query = query.filter(models.AdminUser.id == id)
    if permission:
        query = query.filter(models.AdminUser.permission == permission)
    if username:
        query = query.filter(models.AdminUser.username.like(f"%{username}%"))
    if company_name:
        query = query.filter(models.AdminUser.company_name.like(f"%{company_name}%"))
    if contact_name:
        query = query.filter(models.AdminUser.contact_name.like(f"%{contact_name}%"))

    # ▼▼▼▼▼ 전화번호 검색 로직 수정 ▼▼▼▼▼
    if contact_phone:
        # 1. 사용자가 입력한 검색어에서 숫자만 추출합니다.
        #    (Python에서 직접 처리)
        search_digits = ''.join(filter(str.isdigit, contact_phone))

        if search_digits:  # 숫자만 추출한 결과가 있을 경우에만 필터링
            # 2. PostgreSQL의 regexp_replace 함수를 사용하여 DB 컬럼 값에서
            #    숫자가 아닌 모든 문자('[^0-9]')를 빈 문자열('')로 바꿉니다.
            #    그 결과와 search_digits를 LIKE로 비교합니다.
            db_phone_digits = func.regexp_replace(models.AdminUser.contact_phone, r'[^0-9]', '', 'g')
            query = query.filter(db_phone_digits.like(f"%{search_digits}%"))

    total_count = query.count()
    offset = (page - 1) * size
    items = query.order_by(models.AdminUser.id.desc()).offset(offset).limit(size).all()

    return {"items": items, "total_count": total_count}