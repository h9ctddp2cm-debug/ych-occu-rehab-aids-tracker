"""
Perplexity-based price extractor.
Replaces Gemini extractor (Gemini API blocked in Hong Kong).

Uses Perplexity Sonar API via OpenAI-compatible endpoint.
"""
import os
import re
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Sonar is the cheapest model ($1/$1 per 1M tokens, $5 per 1K requests low context)
# For our use case (extracting a single integer), Sonar is more than enough.
MODEL = "sonar"
API_URL = "https://api.perplexity.ai/chat/completions"

_api_key = os.environ.get("PERPLEXITY_API_KEY")


def _truncate_html(html: str, max_chars: int = 50000) -> str:
    """Strip <script>, <style>, comments. Keep main content."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'\s+', ' ', html)
    return html[:max_chars]


TIER1_PROMPT = """You are extracting the MAIN PRODUCT price from an e-commerce product page (Hong Kong retailer, prices in HK$).

The HTML content below is the COMPLETE source of truth. Do NOT search the web. Do NOT use external knowledge. Use ONLY the HTML provided.

The page may contain:
- The main product's current price (what we want)
- The main product's original/list price (strikethrough, IGNORE this)
- Related products' prices (smaller, in sidebars or "you may also like" sections, IGNORE)
- Shipping/promo amounts e.g. "free shipping over $499" (IGNORE - this is a banner, not a price)

Return ONLY the main product's CURRENT SELLING PRICE as a single integer (no currency symbol, no commas, no decimals).
If you cannot reliably identify the main product price from the HTML, return exactly: UNKNOWN

Examples of valid responses: 2680
Examples of invalid responses: HK$2,680 / $2,680.00 / 2680.50 / "The price is 2680"

HTML content:
"""

TIER2_PROMPT = """You are extracting the LOWEST price from an e-commerce product page that sells multiple SIZE VARIANTS of the same product (Hong Kong retailer, prices in HK$).

The HTML content below is the COMPLETE source of truth. Do NOT search the web. Do NOT use external knowledge. Use ONLY the HTML provided.

This product has multiple sizes/variants at different prices. We want the cheapest variant's current selling price.

IGNORE:
- Strikethrough/original prices (we want current selling prices)
- Related products' prices
- Shipping/promo amounts e.g. "free shipping over $499"

Return ONLY the LOWEST current variant price as a single integer (no currency symbol, no commas, no decimals).
If you cannot reliably identify variant prices, return exactly: UNKNOWN

HTML content:
"""


def extract_price(html: str, url: str, tier: int = 1) -> Optional[int]:
    """
    Use Perplexity Sonar to extract main product price (Tier 1) or lowest variant price (Tier 2).
    Returns int or None.
    """
    if not _api_key:
        logger.error("PERPLEXITY_API_KEY not set — cannot extract prices")
        return None

    clean_html = _truncate_html(html)
    if not clean_html.strip():
        return None

    prompt = (TIER2_PROMPT if tier == 2 else TIER1_PROMPT) + clean_html

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 20,
        # Use low search context to minimize cost
        "web_search_options": {
            "search_context_size": "low",
        },
    }

    headers = {
        "Authorization": f"Bearer {_api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        logger.warning("Perplexity API error for %s: %s", url, e)
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.warning("Perplexity API unexpected response for %s: %s", url, e)
        return None

    if text.upper() == "UNKNOWN" or not text:
        return None

    # Parse integer
    m = re.search(r'\d+', text)
    if not m:
        logger.warning("Perplexity returned non-numeric for %s: %r", url, text[:100])
        return None

    return int(m.group(0))
