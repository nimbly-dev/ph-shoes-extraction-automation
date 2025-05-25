import time
import re
import requests
import json
import concurrent.futures
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
from logger import logger
from base.base import BaseShoe, BaseExtractor

base_url = "https://www.hoka.com/en/ph"

product_lists_url = [
    '/mens-road',
    '/mens-trail',
    '/mens-trail-hiking-shoes',
    '/mens-walking',
    '/mens-fitness',
    '/mens-recovery-comfort-shoes',
    '/mens-stability-shoes',
    '/mens-wides',
    '/mens-sandals',
    '/mens-lifestyle',
    '/womens-road',
    '/womens-trail',
    '/womens-trail-hiking-shoes',
    '/womens-walking',
    '/womens-fitness',
    '/womens-recovery-comfort-shoes',
    '/womens-stability-shoes',
    '/womens-wides',
    '/womens-sandals',
    '/womens-lifestyle',
    '/kids'
]

category_config = {
    '/mens-road':                       {"gender": "male",   "age_group": "adult", "subTitle": "road"},
    '/mens-trail':                      {"gender": "male",   "age_group": "adult", "subTitle": "trail"},
    '/mens-trail-hiking-shoes':         {"gender": "male",   "age_group": "adult", "subTitle": "trail-hiking"},
    '/mens-walking':                    {"gender": "male",   "age_group": "adult", "subTitle": "walking"},
    '/mens-fitness':                    {"gender": "male",   "age_group": "adult", "subTitle": "fitness"},
    '/mens-recovery-comfort-shoes':     {"gender": "male",   "age_group": "adult", "subTitle": "recovery-comfort"},
    '/mens-stability-shoes':            {"gender": "male",   "age_group": "adult", "subTitle": "stability"},
    '/mens-wides':                      {"gender": "male",   "age_group": "adult", "subTitle": "wides"},
    '/mens-sandals':                    {"gender": "male",   "age_group": "adult", "subTitle": "sandals"},
    '/mens-lifestyle':                  {"gender": "male",   "age_group": "adult", "subTitle": "lifestyle"},
    '/womens-road':                     {"gender": "female", "age_group": "adult", "subTitle": "road"},
    '/womens-trail':                    {"gender": "female", "age_group": "adult", "subTitle": "trail"},
    '/womens-trail-hiking-shoes':       {"gender": "female", "age_group": "adult", "subTitle": "trail-hiking"},
    '/womens-walking':                  {"gender": "female", "age_group": "adult", "subTitle": "walking"},
    '/womens-fitness':                  {"gender": "female", "age_group": "adult", "subTitle": "fitness"},
    '/womens-recovery-comfort-shoes':   {"gender": "female", "age_group": "adult", "subTitle": "recovery-comfort"},
    '/womens-stability-shoes':          {"gender": "female", "age_group": "adult", "subTitle": "stability"},
    '/womens-wides':                    {"gender": "female", "age_group": "adult", "subTitle": "wides"},
    '/womens-sandals':                  {"gender": "female", "age_group": "adult", "subTitle": "sandals"},
    '/womens-lifestyle':                {"gender": "female", "age_group": "adult", "subTitle": "lifestyle"},
    '/kids':                            {"gender": "unisex", "age_group": "youth", "subTitle": "kids"}
}

@dataclass
class HokaShoe(BaseShoe):
    pass

def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/116.0.5845.97 Safari/537.36")
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text

def extract_image(prod) -> str:
    img = prod.find("img", class_="tile-image")
    if img and img.get("src"):
        return img["src"].strip()
    container = prod.find("div", class_="image-container")
    if container and container.has_attr("data-images"):
        try:
            data = json.loads(container["data-images"])
            for _, grp in data.items():
                if "default" in grp and "medium" in grp["default"]:
                    url = grp["default"]["medium"][0].get("url")
                    if url:
                        return url.strip()
        except:
            return ""
    return ""

def parse_hoka_products(html_content: str) -> List[dict]:
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.find_all('div', class_='product', attrs={'data-pid': True})
    results = []
    for prod in items:
        rec = {}
        rec["id"] = prod["data-pid"]
        name = prod.find("div", class_="tile-product-name")
        if name and (a := name.find("a", class_="link")):
            rec["title"] = a.get_text(strip=True)
        link = prod.find("a", class_="js-pdp-link")
        if link and link.has_attr("href"):
            href = link["href"].strip()
            rec["url"] = href if href.startswith("http") else base_url + href
        rec["image"] = extract_image(prod)
        sale = prod.find("span", class_="sales")
        rec["price_sale"] = float(sale.get_text(strip=True).replace("₱","").replace(",","")) if sale else None
        orig = prod.find("span", class_="original-price")
        if orig:
            txt = orig.get_text(strip=True).replace("₱","").replace(",","")
            rec["price_original"] = int(float(txt)) if txt else None
        else:
            rec["price_original"] = rec.get("price_sale")
        if rec.get("id") and rec.get("title"):
            results.append(rec)
    return results

def safe_float(val):
    try:
        return float(re.sub(r'[^\d.]','',str(val)))
    except:
        return None

class HokaExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category = category
        self.num_pages = num_pages

    def _scrape_category(self, path: str) -> List[dict]:
        url = f"{base_url}{path}/?sz=200"
        logger.info(f"Fetching: {url}")
        try:
            html = fetch_page(url)
        except Exception as e:
            logger.error(f"Fetch error for {url}: {e}")
            return []
        prods = parse_hoka_products(html)
        logger.info(f"Found {len(prods)} items for {path}")
        return prods

    def extract(self) -> List[HokaShoe]:
        paths = product_lists_url if self.category.lower()=="all" else [self.category]
        all_recs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(self._scrape_category, p): p for p in paths}
            for f in concurrent.futures.as_completed(futures):
                path = futures[f]
                try:
                    recs = f.result()
                    extra = category_config.get(path, {})
                    for r in recs:
                        r.update(extra)
                    all_recs.extend(recs)
                except Exception as e:
                    logger.error(f"{path} error: {e}")

        shoes: List[HokaShoe] = []
        for rec in all_recs:
            rec["price_sale"] = safe_float(rec.get("price_sale"))
            rec["price_original"] = safe_float(rec.get("price_original")) or rec.get("price_sale")
            try:
                shoes.append(HokaShoe(**rec))
            except Exception as e:
                logger.error(f"Shoe init error: {e}")
        return shoes
