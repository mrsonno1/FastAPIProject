# Enduser/routers/language_setting.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db import models
from db.database import get_db
from core.security import get_current_user
from core.language_context import set_user_language, get_user_language
import logging

router = APIRouter(tags=["Language Settings"])
logger = logging.getLogger(__name__)

class LanguageResponse(BaseModel):
    language: str
    message: str

@router.get("/locale_kr", response_model=LanguageResponse)
def set_korean(
    current_user: models.AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 언어를 한국어로 설정합니다."""
    # 데이터베이스에 언어 설정 저장
    current_user.language_preference = 'ko'
    db.commit()
    
    # 메모리 캐시에도 저장 (세션 동안 빠른 접근)
    set_user_language(current_user.username, 'ko')
    
    # 번역 캐시 비우기
    from services.translate_service import translate_service
    translate_service.clear_cache()
    
    logger.info(f"Language set to Korean for user: {current_user.username}")
    
    return LanguageResponse(
        language='ko',
        message='언어가 한국어로 설정되었습니다.'
    )

@router.get("/locale_en", response_model=LanguageResponse)
def set_english(
    current_user: models.AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 언어를 영어로 설정합니다."""
    # 데이터베이스에 언어 설정 저장
    current_user.language_preference = 'en'
    db.commit()
    
    # 메모리 캐시에도 저장 (세션 동안 빠른 접근)
    set_user_language(current_user.username, 'en')
    
    # 번역 캐시 비우기
    from services.translate_service import translate_service
    translate_service.clear_cache()
    
    logger.info(f"Language set to English for user: {current_user.username}")
    
    return LanguageResponse(
        language='en',
        message='Language has been set to English.'
    )

@router.get("/current_locale", response_model=LanguageResponse)
def get_current_language(
    current_user: models.AdminUser = Depends(get_current_user)
):
    """현재 설정된 언어를 확인합니다."""
    # 데이터베이스에서 언어 설정 읽기
    language = current_user.language_preference if hasattr(current_user, 'language_preference') else 'ko'
    
    message = '현재 언어는 한국어입니다.' if language == 'ko' else 'Current language is English.'
    
    return LanguageResponse(
        language=language,
        message=message
    )