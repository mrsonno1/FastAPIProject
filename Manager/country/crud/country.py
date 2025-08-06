# crud/country.py
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from db import models
from Manager.country.schemas import country as country_schema
from typing import List
from fastapi import HTTPException


def get_country_by_name(db: Session, country_name: str):
    return db.query(models.Country).filter(models.Country.country_name == country_name).first()

def get_country_by_id(db: Session, country_id: int):
    return db.query(models.Country).filter(models.Country.id == country_id).first()


def get_all_countries_ordered(db: Session):
    try:
        # rank가 NULL인 경우를 처리하기 위해 COALESCE 사용
        countries = db.query(models.Country).order_by(
            func.coalesce(models.Country.rank, 999999),  # NULL인 경우 큰 숫자로 정렬
            models.Country.id
        ).all()
        return countries
    except Exception as e:
        print(f"ERROR in get_all_countries_ordered: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

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


def delete_country_by_id(db: Session, country_id: int) -> models.Country:
    """국가 ID로 국가를 삭제합니다. 종속성 검사를 포함합니다."""

    # 종속성 검사: portfolio 테이블의 exposed_countries 필드에서 사용 여부 확인
    portfolios = db.query(models.Portfolio).filter(
        models.Portfolio.exposed_countries.isnot(None)
    ).all()

    for portfolio in portfolios:
        if portfolio.exposed_countries:
            country_ids = [id.strip() for id in portfolio.exposed_countries.split(',')]
            if str(country_id) in country_ids:
                raise HTTPException(
                    status_code=400,
                    detail="이 국가는 포트폴리오의 노출 국가로 설정되어 있으므로 삭제할 수 없습니다."
                )

    # 종속성이 없으면 삭제 진행
    country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="국가를 찾을 수 없습니다.")

    db.delete(country)
    db.commit()
    return country


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


def update_country_ranks_bulk(db: Session, ranks: List[country_schema.RankItem]):
    """
    여러 국가의 순위를 한 번에 업데이트합니다.
    """
    if not ranks:
        return # 업데이트할 내용이 없으면 아무것도 하지 않음

    db.query(models.Country).update(
        {
            models.Country.rank: case(
                # 전달받은 ranks 리스트로 case 문을 동적으로 생성
                {item.id: item.rank for item in ranks},
                value=models.Country.id
            )
        },
        synchronize_session=False
    )
    db.commit()