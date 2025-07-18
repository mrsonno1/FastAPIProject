from googletrans import Googletrans
from typing import Optional, List
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class TranslateService:
    def __init__(self):
        self.translator = Googletrans()

    @lru_cache(maxsize=1000)
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'ko') -> str:
        """텍스트를 번역합니다. 캐싱을 사용하여 중복 번역을 방지합니다."""
        if not text or source_lang == target_lang:
            return text

        try:
            result = self.translator.translate(text, dest=target_lang, src=source_lang)
            return result.text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # 번역 실패 시 원본 반환

    def translate_list(self, texts: List[str], target_lang: str, source_lang: str = 'ko') -> List[str]:
        """여러 텍스트를 한 번에 번역합니다."""
        if source_lang == target_lang:
            return texts

        return [self.translate_text(text, target_lang, source_lang) for text in texts]


# 싱글톤 인스턴스
translate_service = TranslateService()