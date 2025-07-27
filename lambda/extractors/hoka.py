# extract_hoka.py

import time
import requests
import json
import concurrent.futures
from typing import List, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from logger import logger
from base.base import BaseShoe, BaseExtractor

base_url = "https://www.hoka.com/en/ph"
product_lists_url = [
    '/mens-road', '/mens-trail', '/mens-trail-hiking-shoes', '/mens-walking',
    '/mens-fitness', '/mens-recovery-comfort-shoes', '/mens-stability-shoes',
    '/mens-wides', '/mens-sandals', '/mens-lifestyle',
    '/womens-road', '/womens-trail', '/womens-trail-hiking-shoes',
    '/womens-walking', '/womens-fitness', '/womens-recovery-comfort-shoes',
    '/womens-stability-shoes', '/womens-wides', '/womens-sandals',
    '/womens-lifestyle', '/kids'
]
category_config = {
    '/mens-road':                       {"gender": "male",   "age_group": "adult", "subTitle": "road"},
    # … (rest of your mapping unchanged) …
    '/kids':                            {"gender": "unisex", "age_group": "youth", "subTitle": "kids"}
}

@dataclass
class HokaShoe(BaseShoe):
    brand: str = "hoka"


def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36"
        )
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
            for grp in data.values():
                if "default" in grp and "medium" in grp["default"]:
                    url = grp["default"]["medium"][0].get("url")
                    if url:
                        return url.strip()
        except json.JSONDecodeError:
            logger.warning("Failed to decode image data JSON")
    return ""


def _parse_price(tag) -> Optional[float]:
    if not tag:
        return None
    text = tag.get_text(strip=True).replace("₱", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        logger.warning(f"Could not parse price from text: '{text}'")
        return None


def parse_hoka_products(html_content: str) -> List[dict]:
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.find_all('div', class_='product', attrs={'data-pid': True})
    results = []
    for prod in items:
        rec = {"brand": "hoka", "id": prod["data-pid"]}
        # title
        name_div = prod.find("div", class_="tile-product-name")
        if name_div and (a := name_div.find("a", class_="link")):
            rec["title"] = a.get_text(strip=True)
        # url
        link = prod.find("a", class_="js-pdp-link")
        if link and link.has_attr("href"):
            href = link["href"].strip()
            rec["url"] = href if href.startswith("http") else base_url + href
        # image
        rec["image"] = extract_image(prod)
        # prices
        sale_price = _parse_price(prod.find("span", class_="sales"))
        orig_price = _parse_price(prod.find("span", class_="original-price"))
        rec["price_sale"]     = sale_price
        rec["price_original"] = orig_price if orig_price is not None else sale_price
        # skip items with no price
        if rec["price_sale"] is None and rec["price_original"] is None:
            continue
        if rec.get("id") and rec.get("title"):
            results.append(rec)
    return results


class HokaExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category  = category
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

        # pull out the canonical config values
        cfg = category_config.get(path, {})
        for r in prods:
            # 1) assign canonical BaseShoe fields
            r["gender"]    = [cfg.get("gender")] if cfg.get("gender") else []
            r["age_group"] = cfg.get("age_group")
            r["subTitle"]  = cfg.get("subTitle")

            # 2) bundle any site-specific bits into `extra`
            extras = {"category_path": path}
            r["extra"] = json.dumps(extras, ensure_ascii=False)

        return prods

    def extract(self) -> List[HokaShoe]:
        paths   = product_lists_url if self.category.lower() == "all" else [self.category]
        all_recs = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(self._scrape_category, p): p for p in paths}
            for f in concurrent.futures.as_completed(futures):
                path = futures[f]
                try:
                    recs = f.result()
                    all_recs.extend(recs)
                except Exception as e:
                    logger.error(f"{path} error: {e}")

        return [HokaShoe(**r) for r in all_recs]
