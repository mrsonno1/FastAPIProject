# rank/crud/rank.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import models

def get_top_released_products(db: Session, limit: int = 10):
    return db.query(
        models.Releasedproduct.main_image_url.label('image'),
        models.Releasedproduct.design_name.label('name'),
        models.Releasedproduct.views.label('view')
    ).order_by(models.Releasedproduct.views.desc()).limit(limit).all()

def get_top_portfolios(db: Session, limit: int = 10):
    return db.query(
        models.Portfolio.main_image_url.label('image'),
        models.Portfolio.design_name.label('name'),
        models.Portfolio.views.label('view')
    ).order_by(models.Portfolio.views.desc()).limit(limit).all()

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
