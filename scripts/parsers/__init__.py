"""
Single OpenRouter-based extractor for all domains.
History:
- Originally Gemini → blocked in Hong Kong (2026-06)
- Perplexity → requires $5 prepay credit card (no Alipay)
- Now OpenRouter → free tier, supports Alipay if upgrade needed
"""
from .openrouter_extract import extract_price as _or_extract


def get_parser(domain: str):
    """Returns a unified parser callable for any domain."""
    return _UnifiedParser()


class _UnifiedParser:
    def extract_price(self, html: str, url: str) -> int | None:
        return _or_extract(html, url, tier=1)

    def extract_min_price(self, html: str, url: str) -> int | None:
        return _or_extract(html, url, tier=2)
