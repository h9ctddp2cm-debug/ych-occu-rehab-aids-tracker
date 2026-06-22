#!/usr/bin/env python3
"""One-off recheck for products that failed in the 2026-06-22 main run.

Rules per user (2026-06-22):
  1. Phone-only products (price_display contains 致電/查詢/contact/phone)
     -> change price_display to "參考價錢" + do NOT update last_checked
  2. Variant-price products (price_display has " - " or " / " or 多尺寸)
     -> fetch a single representative model price + update last_checked
  3. 521/timeout/CAPTCHA fetch fail -> retry then either:
       - succeed -> update price + last_checked
       - still fail -> leave last_checked = 6/15
  4. 404 / page removed -> delete from products.json entirely

Usage:
  DASHSCOPE_API_KEY=... python3 scripts/recheck_fails.py
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_JSON = ROOT / "products.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_checker import (
    _make_session,
    fetch_html,
    _detect_stock_status,
    _validate_price,
    _today_hkt,
    TIER2_IDS,
)
from parsers import get_parser

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("recheck")

# Products that were not updated in the 6/22 main run
FAIL_IDS = {
    "w3", "w5", "w6", "w9",
    "cm2", "cm4", "cm5",
    "br2", "r3",
    "sc1", "sc3", "sc4", "sc8",
    "tr1", "tr4", "tr5",
    "rc3", "sa3",
    "rmp1", "rmp4",
    "bed1", "bed2",
    "mat3",
    "hr1", "hr3", "hr5", "hr6",
}

PHONE_KEYWORDS = ["致電", "查詢", "contact", "phone", "請電", "請致電"]


def is_phone_only(p: dict) -> bool:
    pd = (p.get("price_display") or "").lower()
    return any(kw.lower() in pd for kw in PHONE_KEYWORDS)


def main():
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    today = _today_hkt()
    data = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    session = _make_session()

    stats = {
        "phone_only_marked": 0,
        "fetched_ok": 0,
        "still_failed": 0,
        "deleted_404": 0,
        "oos_detected": 0,
    }

    new_data = []
    for p in data:
        pid = p.get("id")
        if pid not in FAIL_IDS:
            new_data.append(p)
            continue

        url = p.get("product_url", "")
        name = p.get("product_name", "")[:30]

        # --- Rule 1: phone-only -> just relabel ---
        if is_phone_only(p):
            log.info("[%s] PHONE-ONLY: %s -> set 參考價錢", pid, name)
            p["price_display"] = "HK$ — 參考價錢，請致電查詢"
            p["price_note"] = "參考價錢"
            # do NOT touch last_checked
            stats["phone_only_marked"] += 1
            new_data.append(p)
            continue

        # --- Try fetch ---
        log.info("[%s] FETCHING: %s | %s", pid, name, url)
        try:
            r = session.get(url, timeout=25, allow_redirects=True)
        except Exception as e:
            log.warning("[%s] fetch exception: %s", pid, e)
            stats["still_failed"] += 1
            new_data.append(p)
            continue

        # --- Rule 4: 404 -> delete ---
        if r.status_code == 404:
            log.warning("[%s] 404 PAGE REMOVED -> deleting", pid)
            stats["deleted_404"] += 1
            # do not append
            continue

        if r.status_code != 200 or len(r.text) < 3000:
            # CAPTCHA pages from gethealth are ~7700 bytes — try detect
            if "CAPTCHA" in r.text or "请解决" in r.text:
                log.warning("[%s] CAPTCHA bot wall -> still failed", pid)
            else:
                log.warning("[%s] HTTP %s size=%d -> still failed", pid, r.status_code, len(r.text))
            stats["still_failed"] += 1
            new_data.append(p)
            continue

        html = r.text

        # --- Stock check ---
        if _detect_stock_status(html) == "out_of_stock":
            log.info("[%s] OOS detected", pid)
            p["stock_status"] = "out_of_stock"
            p["last_checked"] = today
            stats["oos_detected"] += 1
            new_data.append(p)
            continue

        # --- Extract price via AI ---
        domain = urlparse(url).hostname or ""
        is_tier2 = pid in TIER2_IDS
        parser = get_parser(domain)
        product_name = p.get("product_name", "") or ""
        model_hint = p.get("model", "") or ""
        hint = f"{product_name} {model_hint}".strip()

        try:
            if is_tier2:
                new_price = parser.extract_min_price(html, url, product_hint=hint)
            else:
                new_price = parser.extract_price(html, url, product_hint=hint)
        except Exception as e:
            log.warning("[%s] parser exception: %s", pid, e)
            stats["still_failed"] += 1
            new_data.append(p)
            continue

        new_price = _validate_price(new_price)
        if not new_price:
            log.warning("[%s] AI returned no usable price", pid)
            stats["still_failed"] += 1
            new_data.append(p)
            continue

        # --- Sanity check ---
        old_price = p.get("price_min")
        # For variant products keep min anchor; for Tier 1 update both.
        if is_tier2:
            log.info("[%s] TIER2 price_min: %s -> %s", pid, old_price, new_price)
            p["price_min"] = new_price
        else:
            log.info("[%s] price_min/max: %s -> %s", pid, old_price, new_price)
            p["price_min"] = new_price
            p["price_max"] = new_price
            # Rebuild price_display for simple Tier 1
            p["price_display"] = f"HK${new_price:,}"

        p["last_checked"] = today
        # Clear stock_status if previously set (recheck OK = in_stock)
        if p.get("stock_status") and p["stock_status"] != "in_stock":
            p["stock_status"] = "in_stock"

        stats["fetched_ok"] += 1
        time.sleep(2)  # rate limit
        new_data.append(p)

    PRODUCTS_JSON.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("=== DONE ===")
    log.info("phone_only_marked: %d", stats["phone_only_marked"])
    log.info("fetched_ok        : %d", stats["fetched_ok"])
    log.info("oos_detected      : %d", stats["oos_detected"])
    log.info("still_failed      : %d", stats["still_failed"])
    log.info("deleted_404       : %d", stats["deleted_404"])
    log.info("Total products    : %d -> %d", len(data), len(new_data))


if __name__ == "__main__":
    main()
