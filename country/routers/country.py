# routers/country.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from country.schemas import country as country_schema
from country.crud import country as country_crud
from db import models
from brand.schemas.brand import RankUpdateBulk as BrandRankUpdateBulk

from portfolio.schemas import portfolio as portfolio_schema

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.post("/", response_model=country_schema.CountryResponse, status_code=status.HTTP_201_CREATED)
def create_new_country(country: country_schema.CountryCreate, db: Session = Depends(get_db)):
    if country_crud.get_country_by_name(db, country_name=country.country_name):
        raise HTTPException(status_code=409, detail="이미 사용 중인 국가 이름입니다.")
    return country_crud.create_country(db=db, country=country)


@router.get("/listall", response_model=List[country_schema.CountryResponse])
def get_all_countries(db: Session = Depends(get_db)):
    """모든 국가를 순위 순으로 조회합니다."""
    return country_crud.get_all_countries_ordered(db)


@router.delete("/{country_id}", response_model=portfolio_schema.StatusResponse, status_code=status.HTTP_200_OK)
def delete_single_country(
        country_id: int,
        db: Session = Depends(get_db)
):
    """ID로 특정 국가 데이터를 삭제합니다."""
    try:
        country_crud.delete_country_by_id(db, country_id=country_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

    return portfolio_schema.StatusResponse(status="success", message="국가가 성공적으로 삭제되었습니다.")

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


@router.patch("/rank/bulk", status_code=status.HTTP_204_NO_CONTENT)
def update_ranks_in_bulk(
    rank_update: BrandRankUpdateBulk,
    db: Session = Depends(get_db)
):
    """
    전체 국가 순서 목록을 한 번에 업데이트합니다.
    """
    country_crud.update_country_ranks_bulk(db, ranks=rank_update.ranks)
    return