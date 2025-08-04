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
    - language_setting에 따라 테이블에 저장된 국가명을 반환
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
    
    # 국가 정보를 반환
    country_data = []
    
    for country in countries:
        # 언어 설정에 따라 테이블에서 직접 읽기
        if language == 'en':
            # 영문 이름이 있으면 사용, 없으면 번역 서비스 사용
            if country.country_name_en:
                country_name = country.country_name_en
            else:
                # 영문 이름이 없으면 번역하고 DB에 저장
                translated_name = translate_service.translate_text(
                    country.country_name, 
                    target_lang='en', 
                    source_lang='ko'
                )
                # DB에 영문 이름 저장
                country.country_name_en = translated_name
                db.commit()
                country_name = translated_name
        else:
            # 한국어는 그대로 사용
            country_name = country.country_name
            
        country_data.append({
            'id': country.id,
            'country_name': country_name
        })
    
    return [CountryResponse(id=country['id'], country_name=country['country_name']) 
            for country in country_data]