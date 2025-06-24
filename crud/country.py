# crud/country.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from db import models
from schemas import country as country_schema

def get_country_by_name(db: Session, country_name: str):
    return db.query(models.Country).filter(models.Country.country_name == country_name).first()

def get_all_countries_ordered(db: Session):
    return db.query(models.Country).order_by(models.Country.rank).all()

def create_country(db: Session, country: country_schema.CountryCreate):
    """새로운 국가를 가장 낮은 순위로 생성합니다."""
    max_rank = db.query(func.max(models.Country.rank)).scalar() or 0
    db_country = models.Country(
        country_name=country.country_name,
        rank=max_rank + 1
    )
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

def update_country_info(db: Session, db_country: models.Country, country_update: country_schema.CountryUpdate):
    """국가 이름을 수정합니다."""
    db_country.country_name = country_update.country_name
    db.commit()
    db.refresh(db_country)
    return db_country

def update_country_rank(db: Session, country_id: int, action: str):
    """국가의 순위를 변경합니다."""
    target_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not target_country:
        return None

    all_countries = get_all_countries_ordered(db)
    if len(all_countries) <= 1:
        return all_countries

    if action == "up":
        current_index = all_countries.index(target_country)
        if current_index > 0:
            prev_country = all_countries[current_index - 1]
            target_country.rank, prev_country.rank = prev_country.rank, target_country.rank
    elif action == "down":
        current_index = all_countries.index(target_country)
        if current_index < len(all_countries) - 1:
            next_country = all_countries[current_index + 1]
            target_country.rank, next_country.rank = next_country.rank, target_country.rank
    elif action == "top":
        db.query(models.Country).filter(models.Country.id != country_id).update({models.Country.rank: models.Country.rank + 1})
        target_country.rank = 1
    elif action == "bottom":
        max_rank = all_countries[-1].rank
        db.query(models.Country).filter(
            models.Country.id != country_id,
            models.Country.rank > target_country.rank
        ).update({models.Country.rank: models.Country.rank - 1})
        target_country.rank = max_rank

    db.commit()
    return get_all_countries_ordered(db)