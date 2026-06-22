"""
Single Perplexity-based extractor for all domains.
(Was Gemini — switched 2026-06-22 because Gemini API is blocked in Hong Kong.)
"""
from .perplexity_extract import extract_price as _pplx_extract


def get_parser(domain: str):
    """Returns a unified parser callable for any domain."""
    return _UnifiedParser()


class _UnifiedParser:
    def extract_price(self, html: str, url: str) -> int | None:
        return _pplx_extract(html, url, tier=1)

    def extract_min_price(self, html: str, url: str) -> int | None:
        return _pplx_extract(html, url, tier=2)
