"""
Single Groq-based extractor for all domains.
History:
- Originally Gemini -> blocked in Hong Kong (2026-06)
- Perplexity -> requires $5 prepay credit card (no Alipay)
- OpenRouter -> free tier only 50 req/day (hits 429 with 58 products)
- Now Groq -> free 1000 req/day on llama-3.3-70b, fast & HK-friendly
"""
from .groq_extract import extract_price as _groq_extract


def get_parser(domain: str):
    """Returns a unified parser callable for any domain."""
    return _UnifiedParser()


class _UnifiedParser:
    def extract_price(self, html: str, url: str) -> int | None:
        return _groq_extract(html, url, tier=1)

    def extract_min_price(self, html: str, url: str) -> int | None:
        return _groq_extract(html, url, tier=2)
