# routers/country.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from schemas import country as country_schema
from crud import country as country_crud
from db import models
from schemas.brand import RankUpdateBulk as BrandRankUpdateBulk

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.post("/", response_model=country_schema.CountryResponse, status_code=status.HTTP_201_CREATED)
def create_new_country(country: country_schema.CountryCreate, db: Session = Depends(get_db)):
    if country_crud.get_country_by_name(db, country_name=country.country_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 국가 이름입니다.")
    return country_crud.create_country(db=db, country=country)


@router.get("/", response_model=List[country_schema.CountryResponse])
def get_all_countries(db: Session = Depends(get_db)):
    """모든 국가를 순위 순으로 조회합니다."""
    return country_crud.get_all_countries_ordered(db)


@router.put("/{country_id}", response_model=country_schema.CountryResponse)
def update_country_details(
        country_id: int,
        country_update: country_schema.CountryUpdate,
        db: Session = Depends(get_db)
):
    """국가 이름을 수정합니다."""
    db_country = db.query(models.Country).filter(models.Country.id == country_id).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="국가를 찾을 수 없습니다.")

    existing_country = country_crud.get_country_by_name(db, country_name=country_update.country_name)
    if existing_country and existing_country.id != country_id:
        raise HTTPException(status_code=409, detail="이미 사용 중인 국가 이름입니다.")

    return country_crud.update_country_info(db, db_country=db_country, country_update=country_update)


@router.patch("/rank/{country_id}", response_model=List[country_schema.CountryResponse])
def update_rank(
        country_id: int,
        rank_update: country_schema.RankUpdate,
        db: Session = Depends(get_db)
):
    """국가의 순위를 변경합니다. (up, down, top, bottom)"""
    updated_countries = country_crud.update_country_rank(db, country_id=country_id, action=rank_update.action)
    if updated_countries is None:
        raise HTTPException(status_code=404, detail="국가를 찾을 수 없습니다.")
    return updated_countries


@router.put("/rank/bulk", status_code=status.HTTP_204_NO_CONTENT)
def update_ranks_in_bulk(
    # 스키마 이름을 명확히 하기 위해 BrandRankUpdateBulk 사용
    rank_update: BrandRankUpdateBulk,
    db: Session = Depends(get_db)
):
    """
    전체 국가 순서 목록을 한 번에 업데이트합니다.
    """
    country_crud.update_country_ranks_bulk(db, ranks=rank_update.ranks)
    return # 성공 시 204 응답