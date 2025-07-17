from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from db import models
from datetime import datetime, timedelta
from typing import Dict, Any


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
        content_name: str
) -> int:
    """컨텐츠에 유저 입장"""

    # 만료된 유저 정리
    clean_expired_users(db)

    # 이미 입장한 기록이 있는지 확인
    existing = db.query(models.RealtimeUser).filter(
        and_(
            models.RealtimeUser.user_id == user_id,
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_name == content_name
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
            content_name=content_name
        )
        db.add(new_entry)

    db.commit()

    # 현재 유저수 반환
    return get_realtime_users_count(db, content_type, content_name)


def leave_content(
        db: Session,
        user_id: str,
        content_type: str,
        content_name: str
) -> int:
    """컨텐츠에서 유저 퇴장"""

    # 만료된 유저 정리
    clean_expired_users(db)

    # 유저 기록 삭제
    db.query(models.RealtimeUser).filter(
        and_(
            models.RealtimeUser.user_id == user_id,
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_name == content_name
        )
    ).delete()

    db.commit()

    # 현재 유저수 반환
    return get_realtime_users_count(db, content_type, content_name)


def get_realtime_users_count(
        db: Session,
        content_type: str,
        content_name: str
) -> int:
    """현재 실시간 유저수 조회"""

    # 만료된 유저 정리
    clean_expired_users(db)

    # 현재 유저수 카운트
    count = db.query(func.count(models.RealtimeUser.id)).filter(
        and_(
            models.RealtimeUser.content_type == content_type,
            models.RealtimeUser.content_name == content_name
        )
    ).scalar()

    return count or 0