# rank/crud/rank.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import models
from datetime import date

def get_top_released_products(db: Session, limit: int = 10):
    """오늘 날짜의 조회수(daily_views)가 가장 많은 출시 제품 10개를 조회합니다."""
    today = date.today()
    return db.query(
        models.Releasedproduct.main_image_url.label('image'),
        models.Releasedproduct.design_name.label('name'),
        models.DailyView.view_count.label('view')
    ).join(
        models.DailyView,
        (models.DailyView.content_id == models.Releasedproduct.id) &
        (models.DailyView.content_type == 'released_product')
    ).filter(
        models.DailyView.view_date == today
    ).order_by(
        models.DailyView.view_count.desc()
    ).limit(limit).all()

def get_top_portfolios(db: Session, limit: int = 10):
    """오늘 날짜의 조회수(daily_views)가 가장 많은 포트폴리오 10개를 조회합니다."""
    today = date.today()
    return db.query(
        models.Portfolio.main_image_url.label('image'),
        models.Portfolio.design_name.label('name'),
        models.DailyView.view_count.label('view')
    ).join(
        models.DailyView,
        (models.DailyView.content_id == models.Portfolio.id) &
        (models.DailyView.content_type == 'portfolio')
    ).filter(
        models.DailyView.view_date == today
    ).order_by(
        models.DailyView.view_count.desc()
    ).limit(limit).all()

def get_custom_design_status_counts(db: Session):
    status_counts = db.query(
        models.CustomDesign.status,
        func.count(models.CustomDesign.id)
    ).group_by(models.CustomDesign.status).all()

    # 사용자 요청: 0=wait, 1=reject, 2=under_review, 3=complet
    # DB 컬럼 타입이 String이므로, 키를 문자열로 사용합니다.
    status_map = {
        '0': 'wait',
        '1': 'reject',
        '2': 'under_review',
        '3': 'complet'
    }

    counts = {
        'wait': 0,
        'reject': 0,
        'under_review': 0,
        'complet': 0,
    }

    for status_val, count in status_counts:
        # DB에서 가져온 status 값을 문자열로 변환하여 타입 불일치 문제를 해결합니다.
        str_status_val = str(status_val)
        if str_status_val in status_map:
            key = status_map[str_status_val]
            counts[key] = count

    total = sum(counts.values())
    counts['total'] = total
    
    return counts


def get_progress_status_counts(db: Session):
    """진행 상태별 개수를 조회합니다."""
    status_counts = db.query(
        models.Progressstatus.status,
        func.count(models.Progressstatus.id)
    ).group_by(models.Progressstatus.status).all()

    # wait=0, progress=1, delay=2, delivery_completed=3
    counts = {
        'wait': 0,
        'pregress': 0,  # 오타 그대로 유지 (기존 API 호환성)
        'delay': 0,
        'delivery_completed': 0,
    }

    for status_val, count in status_counts:
        if status_val == '0':
            counts['wait'] = count
        elif status_val == '1':
            counts['pregress'] = count
        elif status_val == '2':
            counts['delay'] = count
        elif status_val == '3':
            counts['delivery_completed'] = count

    total = sum(counts.values())
    counts['total'] = total

    return counts