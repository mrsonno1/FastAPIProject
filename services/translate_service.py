from deep_translator import GoogleTranslator
from typing import Optional, List
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# 번역 캐시를 별도 함수로 분리
@lru_cache(maxsize=1000)
def _cached_translate(text: str, target_lang: str, source_lang: str) -> str:
    """실제 번역을 수행하고 캐싱합니다."""
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        result = translator.translate(text)
        return result
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # 번역 실패 시 원본 반환


class TranslateService:
    def __init__(self):
        pass  # GoogleTranslator는 인스턴스별로 생성

    def translate_text(self, text: str, target_lang: str, source_lang: str = 'ko') -> str:
        """텍스트를 번역합니다. 캐싱을 사용하여 중복 번역을 방지합니다."""
        if not text or source_lang == target_lang:
            return text

        return _cached_translate(text, target_lang, source_lang)
    
    def clear_cache(self):
        """번역 캐시를 비웁니다."""
        _cached_translate.cache_clear()

    def translate_list(self, texts: List[str], target_lang: str, source_lang: str = 'ko') -> List[str]:
        """여러 텍스트를 한 번에 번역합니다."""
        if source_lang == target_lang:
            return texts

        return [self.translate_text(text, target_lang, source_lang) for text in texts]


# 싱글톤 인스턴스
translate_service = TranslateService()