from sqlalchemy.orm import Session
from db import models
from core.security import get_password_hash, verify_password
from typing import Optional
from fastapi import HTTPException


def get_user_by_username(db: Session, username: str) -> Optional[models.AdminUser]:
    """사용자명으로 사용자 조회"""
    return db.query(models.AdminUser).filter(models.AdminUser.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.AdminUser]:
    """이메일로 사용자 조회"""
    return db.query(models.AdminUser).filter(models.AdminUser.email == email).first()


def update_user_info(db: Session, user: models.AdminUser, user_update: dict) -> models.AdminUser:
    """사용자 정보 업데이트"""
    for key, value in user_update.items():
        if key == "new_password" and value:
            # 비밀번호 변경 시 해싱
            user.hashed_password = get_password_hash(value)
        elif key != "new_password" and hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


def verify_user_password(db: Session, username: str, password: str) -> Optional[models.AdminUser]:
    """사용자 비밀번호 검증"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
