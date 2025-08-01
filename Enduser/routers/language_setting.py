# Enduser/routers/language_setting.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from db import models
from core.security import get_current_user
from core.language_context import set_user_language, get_user_language

router = APIRouter(tags=["Language Settings"])

class LanguageResponse(BaseModel):
    language: str
    message: str

@router.get("/locale_kr", response_model=LanguageResponse)
def set_korean(current_user: models.AdminUser = Depends(get_current_user)):
    """사용자 언어를 한국어로 설정합니다."""
    set_user_language(current_user.username, 'ko')
    # 번역 캐시 비우기
    from services.translate_service import translate_service
    translate_service.clear_cache()
    return LanguageResponse(
        language='ko',
        message='언어가 한국어로 설정되었습니다.'
    )

@router.get("/locale_en", response_model=LanguageResponse)
def set_english(current_user: models.AdminUser = Depends(get_current_user)):
    """사용자 언어를 영어로 설정합니다."""
    set_user_language(current_user.username, 'en')
    # 번역 캐시 비우기
    from services.translate_service import translate_service
    translate_service.clear_cache()
    return LanguageResponse(
        language='en',
        message='Language has been set to English.'
    )