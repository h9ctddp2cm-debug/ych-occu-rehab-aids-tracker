import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import date
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

today = str(date.today())

TARGET_PRODUCTS = [
    {"id": "w3",  "model": "ALP-DS1807PF-T05",      "name": "Alpha® T05 自助式輪椅",       "source": "rehabexpress", "source_name": "復康速遞", "category": "wheelchair", "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=ALP-DS1807PF-T05"},
    {"id": "sc3", "model": "FS-798L",                "name": "靠背沐浴椅/沖涼椅",           "source": "rehabexpress", "source_name": "復康速遞", "category": "shower",    "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=FS-798L"},
    {"id": "sc4", "model": "ST-D1004",               "name": "日式旋轉沐浴椅",             "source": "rehabexpress", "source_name": "復康速遞", "category": "shower",    "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=ST-D1004"},
    {"id": "cm3", "model": "H-61-G-D-PW3",          "name": "不銹鋼沐浴便廁椅",           "source": "rehabexpress", "source_name": "復康速遞", "category": "toilet",    "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=H-61-G-D-PW3"},
    {"id": "br1", "model": "NOT-P42434",             "name": "免安裝扶手床欄(可伸長)",     "source": "rehabexpress", "source_name": "復康速遞", "category": "bedrail",   "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=NOT-P42434"},
    {"id": "r2",  "model": "WOH-TRRUB-RUB-1525-2",  "name": "WONSH®膠斜台",              "source": "rehabexpress", "source_name": "復康速遞", "category": "ramp",      "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=WONSH"},
    {"id": "m2",  "model": "RX-AM40A",               "name": "ROSSMAX條狀氣墊床褥",       "source": "rehabexpress", "source_name": "復康速遞", "category": "mattress",  "search_url": "https://www.rehabexpress.com.hk/catalogsearch/result/?q=RX-AM40A"},
    {"id": "w4",  "model": "VA3000",                 "name": "日式鋁合金輪椅",             "source": "easy66",       "source_name": "Easy66",  "category": "wheelchair", "search_url": "https://www.easy66.com.hk/en/search?q=VA3000"},
    {"id": "cm4", "model": "CS307A",                 "name": "四輪沐浴便椅(活動扶手)",     "source": "easy66",       "source_name": "Easy66",  "category": "toilet",    "search_url": "https://www.easy66.com.hk/en/search?q=CS307A"},
    {"id": "cm6", "model": "CA1360",                 "name": "摺合式沐浴便椅",             "source": "easy66",       "source_name": "Easy66",  "category": "toilet",    "search_url": "https://www.easy66.com.hk/en/search?q=CA1360"},
    {"id": "r3",  "model": "WA200",                  "name": "摺疊式輪椅斜板",             "source": "easy66",       "source_name": "Easy66",  "category": "ramp",      "search_url": "https://www.easy66.com.hk/en/search?q=WA200"},
]

def scrape_rehabexpress(product):
    try:
        r = requests.get(product["search_url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        item = soup.select_one(".product-item-info") or soup.select_one(".item.product")
        if not item:
            return None
        price_tag = item.select_one(".price")
        price_text = price_tag.get_text(strip=True) if price_tag else "請查詢"
        nums = re.findall(r"[\d]+", price_text.replace(",", ""))
        price_num = float(nums[0]) if nums else 0
        img_tag = item.select_one("img.product-image-photo") or item.select_one("img")
        image_url = ""
        if img_tag:
            image_url = img_tag.get("data-src") or img_tag.get("src") or ""
            if image_url.startswith("/"):
                image_url = "https://www.rehabexpress.com.hk" + image_url
            if "blank.png" in image_url or "placeholder" in image_url:
                image_url = ""
        link_tag = item.select_one("a.product-item-link") or item.select_one("a")
        product_url = link_tag["href"] if link_tag and link_tag.get("href") else ""
        return {"price_num": price_num, "price_display": price_text, "image_url": image_url, "product_url": product_url}
    except Exception as e:
        print(f"  [rehabexpress] Error: {e}")
        return None

def scrape_easy66(product):
    try:
        r = requests.get(product["search_url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        item = (soup.select_one(".product-item") or
                soup.select_one(".grid-product__content") or
                soup.select_one("li.grid__item"))
        if not item:
            return None
        price_tag = item.select_one(".product-price__price") or item.select_one(".price") or item.select_one(".money")
        price_text = price_tag.get_text(strip=True) if price_tag else "請查詢"
        nums = re.findall(r"[\d]+", price_text.replace(",", ""))
        price_num = float(nums[0]) if nums else 0
        img_tag = item.select_one("img")
        image_url = ""
        if img_tag:
            image_url = img_tag.get("data-src") or img_tag.get("src") or ""
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            if image_url.startswith("/"):
                image_url = "https://www.easy66.com.hk" + image_url
        link_tag = item.select_one("a")
        product_url = ""
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            product_url = href if href.startswith("http") else "https://www.easy66.com.hk" + href
        return {"price_num": price_num, "price_display": price_text, "image_url": image_url, "product_url": product_url}
    except Exception as e:
        print(f"  [easy66] Error: {e}")
        return None

def run_crawler():
    results = []
    for p in TARGET_PRODUCTS:
        print(f"Scraping: {p['name']} ({p['model']})...")
        data = scrape_rehabexpress(p) if p["source"] == "rehabexpress" else scrape_easy66(p)
        record = {
            "id": p["id"],
            "source": p["source"],
            "source_name": p["source_name"],
            "category": p["category"],
            "product_name": p["name"],
            "model": p["model"],
            "price_min": data["price_num"] if data else 0,
            "price_max": data["price_num"] if data else 0,
            "price_display": data["price_display"] if data else "請查詢",
            "image_url": data["image_url"] if data else "",
            "product_url": data["product_url"] if data else "",
            "updated_date": today,
            "last_checked": today,
        }
        results.append(record)
        print(f"  {'✅' if data else '⚠️'} {record['price_display']} | img: {'✓' if record['image_url'] else '✗'}")

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} products to products.json")

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            for r in results:
                supabase.table("products").upsert(r, on_conflict="id").execute()
            print("✅ Supabase updated")
        except Exception as e:
            print(f"⚠️ Supabase error: {e}")

if __name__ == "__main__":
    run_crawler()
