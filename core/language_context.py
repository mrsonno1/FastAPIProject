# core/language_context.py
from contextvars import ContextVar
from typing import Dict
import threading
_user_languages: Dict[str, str] = {}
_language_lock = threading.Lock()

# 현재 요청의 사용자별 언어 설정
_current_user_lang: ContextVar[str] = ContextVar('current_user_lang', default='ko')

def set_user_language(username: str, language: str) -> None:
    """사용자의 언어 설정을 저장합니다."""
    with _language_lock:
        _user_languages[username] = language

def get_user_language(username: str) -> str:
    """사용자의 언어 설정을 가져옵니다."""
    with _language_lock:
        return _user_languages.get(username, 'ko')

def set_current_language(language: str) -> None:
    """현재 요청의 언어를 설정합니다."""
    _current_user_lang.set(language)

def get_current_language() -> str:
    """현재 요청의 언어를 반환합니다."""
    return _current_user_lang.get()