"""
Single Qwen-based extractor for all domains.
History:
- Originally Gemini -> blocked in Hong Kong (2026-06)
- Perplexity -> requires $5 prepay credit card (no Alipay)
- OpenRouter -> free tier only 50 req/day
- Groq -> blocked in Hong Kong (Forbidden)
- Cerebras -> blocked in Hong Kong (Cloudflare)
- Now Qwen (Alibaba) -> HK-friendly, 1M tokens/model free 90 days
"""
from .qwen_extract import extract_price as _qwen_extract


def get_parser(domain: str):
    """Returns a unified parser callable for any domain."""
    return _UnifiedParser()


class _UnifiedParser:
    def extract_price(self, html: str, url: str, product_hint: str = "") -> int | None:
        return _qwen_extract(html, url, tier=1, product_hint=product_hint)

    def extract_min_price(self, html: str, url: str, product_hint: str = "") -> int | None:
        return _qwen_extract(html, url, tier=2, product_hint=product_hint)
