from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from db import models
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union


def clean_expired_users(db: Session):
    """1분 이상 경과한 유저 기록 삭제"""
    expire_time = datetime.now() - timedelta(minutes=1)

    deleted = db.query(models.RealtimeUser).filter(
        models.RealtimeUser.entered_at < expire_time
    ).delete()

    if deleted > 0:
        db.commit()


def enter_content(
        db: Session,
        user_id: str,
        content_type: str,
        content_name: str = None,
        content_id: int = None
) -> int:
    """컨텐츠에 유저 입장 (ID 기반)"""

    # 만료된 유저 정리
    clean_expired_users(db)
    
    # content_name으로 호출된 경우 ID 찾기
    if content_id is None and content_name is not None:
        if content_type == 'released_product':
            product = db.query(models.Releasedproduct).filter(
                models.Releasedproduct.design_name == content_name
            ).first()
            if product:
                content_id = product.id
                content_name = product.design_name
            else:
                return 0
        elif content_type == 'portfolio':
            portfolio = db.query(models.Portfolio).filter(
                models.Portfolio.design_name == content_name,
                models.Portfolio.is_deleted == False
            ).first()
            if portfolio:
                content_id = portfolio.id
                content_name = portfolio.design_name
            else:
                return 0
    
    # content_id로 호출된 경우 name 조회 (참고용)
    elif content_id is not None and content_name is None:
        if content_type == 'released_product':
            product = db.query(models.Releasedproduct).filter(
                models.Releasedproduct.id == content_id
            ).first()
            if product:
                content_name = product.design_name
            else:
                return 0
        elif content_type == 'portfolio':
            portfolio = db.query(models.Portfolio).filter(
                models.Portfolio.id == content_id,
                models.Portfolio.is_deleted == False
            ).first()
            if portfolio:
                content_name = portfolio.design_name
            else:
                return 0
    
    if content_id is None:
        return 0  # content_id가 없으면 처리 불가

    # 이미 입장한 기록이 있는지 확인 (ID 기반)
    existing = db.query(models.RealtimeUser).filter(
        and_(
            models.RealtimeUser.user_id == user_id,
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_id == content_id
        )
    ).first()

    if existing:
        # 이미 있으면 시간만 업데이트
        existing.entered_at = datetime.now()
    else:
        # 새로 추가
        new_entry = models.RealtimeUser(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            content_name=content_name  # 참고용
        )
        db.add(new_entry)

    db.commit()

    # 현재 유저수 반환
    return get_realtime_users_count(db, content_type, content_name, content_id)


def leave_content(
        db: Session,
        user_id: str,
        content_type: str,
        content_name: str = None,
        content_id: int = None
) -> int:
    """컨텐츠에서 유저 퇴장 (ID 기반)"""

    # 만료된 유저 정리
    clean_expired_users(db)
    
    # content_name으로 호출된 경우 ID 찾기
    if content_id is None and content_name is not None:
        if content_type == 'released_product':
            product = db.query(models.Releasedproduct).filter(
                models.Releasedproduct.design_name == content_name
            ).first()
            if product:
                content_id = product.id
            else:
                return 0
        elif content_type == 'portfolio':
            portfolio = db.query(models.Portfolio).filter(
                models.Portfolio.design_name == content_name,
                models.Portfolio.is_deleted == False
            ).first()
            if portfolio:
                content_id = portfolio.id
            else:
                return 0
    
    if content_id is None:
        return 0  # content_id가 없으면 처리 불가

    # 유저 기록 삭제 (ID 기반)
    db.query(models.RealtimeUser).filter(
        and_(
            models.RealtimeUser.user_id == user_id,
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_id == content_id
        )
    ).delete()

    db.commit()

    # 현재 유저수 반환
    return get_realtime_users_count(db, content_type, content_name, content_id)


def get_realtime_users_count(
        db: Session,
        content_type: str,
        content_name: str = None,
        content_id: int = None
) -> int:
    """현재 실시간 유저수 조회 (ID 기반)"""

    # 만료된 유저 정리
    clean_expired_users(db)
    
    # content_name으로 호출된 경우 ID 찾기
    if content_id is None and content_name is not None:
        if content_type == 'released_product':
            product = db.query(models.Releasedproduct).filter(
                models.Releasedproduct.design_name == content_name
            ).first()
            if product:
                content_id = product.id
            else:
                return 0
        elif content_type == 'portfolio':
            portfolio = db.query(models.Portfolio).filter(
                models.Portfolio.design_name == content_name,
                models.Portfolio.is_deleted == False
            ).first()
            if portfolio:
                content_id = portfolio.id
            else:
                return 0
    
    if content_id is None:
        return 0  # content_id가 없으면 처리 불가

    # 현재 유저수 카운트 (ID 기반)
    count = db.query(func.count(models.RealtimeUser.id)).filter(
        and_(
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_id == content_id
        )
    ).scalar()

    return count or 0