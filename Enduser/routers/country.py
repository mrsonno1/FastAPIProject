# Enduser/routers/country.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db import models
from core.security import get_current_user
from core.dependencies import get_current_language_dependency
from services.translate_service import translate_service
from pydantic import BaseModel

router = APIRouter(tags=["Country"])


class CountryResponse(BaseModel):
    id: int
    country_name: str

    class Config:
        from_attributes = True


@router.get("/countries/sorted", response_model=List[CountryResponse])
def get_sorted_countries(
        db: Session = Depends(get_db),
        current_user: models.AdminUser = Depends(get_current_user),
        language: str = Depends(get_current_language_dependency)
):
    """
    포트폴리오에 노출된 국가들을 rank 순으로 정렬하여 반환합니다.
    
    - portfolios 테이블의 exposed_countries 필드에 있는 국가 ID들만 추출
    - language_setting에 따라 국가명을 번역
    - rank 필드 순으로 정렬
    """
    
    # 모든 포트폴리오에서 exposed_countries 수집
    portfolios = db.query(models.Portfolio).filter(
        models.Portfolio.exposed_countries.isnot(None),
        models.Portfolio.is_deleted == False
    ).all()
    
    # 중복 제거를 위한 set
    exposed_country_ids = set()
    
    for portfolio in portfolios:
        if portfolio.exposed_countries:
            # exposed_countries는 "1,2,3" 형태로 저장되어 있음
            country_ids = [id.strip() for id in portfolio.exposed_countries.split(',')]
            exposed_country_ids.update(country_ids)
    
    # 노출된 국가가 없는 경우
    if not exposed_country_ids:
        return []
    
    # 해당 ID의 국가들을 rank 순으로 조회
    countries = db.query(models.Country).filter(
        models.Country.id.in_([int(id) for id in exposed_country_ids])
    ).order_by(models.Country.rank).all()
    
    # 국가 정보를 (id, 원본명, 번역명) 형태로 저장
    country_data = []
    
    for country in countries:
        # 언어 설정에 따른 번역
        if language == 'en':
            # 한국어 -> 영어 번역
            translated_name = translate_service.translate_text(
                country.country_name, 
                target_lang='en', 
                source_lang='ko'
            )
        else:
            # 한국어는 번역하지 않음
            translated_name = country.country_name
            
        country_data.append({
            'id': country.id,
            'country_name': translated_name
        })
    
    # rank 순으로 이미 정렬되어 있으므로 별도 정렬 불필요
    # country_data를 그대로 반환
    return [CountryResponse(id=country['id'], country_name=country['country_name']) 
            for country in country_data]