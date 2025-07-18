# core/dependencies.py
from fastapi import Depends
from db import models
from core.security import get_current_user
from core.language_context import get_user_language, set_current_language

async def get_current_language_dependency(
    current_user: models.AdminUser = Depends(get_current_user)
) -> str:
    """현재 사용자의 언어 설정을 가져와서 컨텍스트에 설정합니다."""
    language = get_user_language(current_user.username)
    set_current_language(language)
    return language