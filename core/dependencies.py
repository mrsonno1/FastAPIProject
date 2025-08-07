# core/dependencies.py
from fastapi import Depends
from db import models
from core.security import get_current_user
from core.language_context import get_user_language, set_current_language, set_user_language

def get_current_language_dependency(
    current_user: models.AdminUser = Depends(get_current_user)
) -> str:
    """현재 사용자의 언어 설정을 가져와서 컨텍스트에 설정합니다."""
    # 데이터베이스에서 언어 설정 읽기 (우선)
    if hasattr(current_user, 'language_preference') and current_user.language_preference:
        language = current_user.language_preference
        # 메모리 캐시에도 저장
        set_user_language(current_user.username, language)
    else:
        # DB에 필드가 없거나 값이 없으면 메모리에서 확인, 없으면 기본값
        language = get_user_language(current_user.username)
    
    set_current_language(language)
    return language