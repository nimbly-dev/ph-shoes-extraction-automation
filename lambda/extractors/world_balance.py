# extractors/world_balance.py

import json
import random
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
from dataclasses import dataclass
from logger import logger
from base.base import BaseShoe, BaseExtractor

BASE_URL       = 'https://worldbalance.com.ph'
COLLECTION_PATH = '/collections'

# List of collection paths to scrape
product_lists_url = [
    '/performance',
    '/lifestyle-m',
    '/athleisure-m',
    '/classic-men-shoes',
    '/slipper-m',
    '/performance-l',
    '/lifestyle-l',
    '/classic-women-shoes',
    '/slippers-l',
    '/performance-kids',
    '/lifestyle-kids',
    '/classic-children-shoes',
    '/slippers-kids',
    '/pe',
    '/athleisure-kids'
]

# Per‐path metadata
category_config = {
    '/performance':            {"gender": ["male"],   "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-m':            {"gender": ["male"],   "age_group": "adult", "subtitle": "lifestyle"},
    '/athleisure-m':           {"gender": ["male"],   "age_group": "adult", "subtitle": "athleisure"},
    '/classic-men-shoes':      {"gender": ["male"],   "age_group": "adult", "subtitle": "classic-shoes"},
    '/slipper-m':              {"gender": ["male"],   "age_group": "adult", "subtitle": "slipper"},
    '/performance-l':          {"gender": ["female"], "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-l':            {"gender": ["female"], "age_group": "adult", "subtitle": "lifestyle"},
    '/classic-women-shoes':    {"gender": ["female"], "age_group": "adult", "subtitle": "classic-shoes"},
    '/slippers-l':             {"gender": ["female"], "age_group": "adult", "subtitle": "slipper"},
    '/performance-kids':       {"gender": ["unisex"], "age_group": "youth", "subtitle": "performance"},
    '/lifestyle-kids':         {"gender": ["unisex"], "age_group": "youth", "subtitle": "lifestyle"},
    '/classic-children-shoes': {"gender": ["unisex"], "age_group": "youth", "subtitle": "classic-shoes"},
    '/slippers-kids':          {"gender": ["unisex"], "age_group": "youth", "subtitle": "slipper"},
    '/pe':                     {"gender": ["unisex"], "age_group": "youth", "subtitle": "pe"},
    '/athleisure-kids':        {"gender": ["unisex"], "age_group": "youth", "subtitle": "athleisure"},
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

@dataclass
class WorldBalanceShoe(BaseShoe):
    brand: str = "worldbalance"
    extra: Optional[str] = None


def parse_price(raw: str) -> Tuple[float, float]:
    nums = [m.replace(',', '') for m in re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', raw)]
    if len(nums) >= 2:
        # the first is original, second is sale
        return float(nums[1]), float(nums[0])
    if nums:
        v = float(nums[0])
        return v, v
    return 0.0, 0.0


class WorldBalanceExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category  = category
        self.num_pages = num_pages

    def _extract_products_from_html(self, html: str, path: str) -> List[WorldBalanceShoe]:
        soup  = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.grid__item[data-product-id]')
        shoes: List[WorldBalanceShoe] = []
        cfg = category_config.get(path, {})

        for c in cards:
            try:
                pid   = c['data-product-id'].strip()
                link  = c.select_one('a.grid-product__link')
                name  = c.select_one('div.grid-product__title')
                price = c.select_one('div.grid-product__price')
                img   = c.select_one('img.grid-product__image')

                title = name.get_text(strip=True) if name else ''
                href  = link['href'] if link and link.has_attr('href') else ''
                url   = href if href.startswith('http') else BASE_URL + href

                img_url = ''
                if img and img.has_attr('src'):
                    img_url = img['src']
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = BASE_URL + img_url

                raw = price.get_text(separator=' ', strip=True) if price else ''
                sale, orig = parse_price(raw)

                rec = {
                    "id":             pid,
                    "title":          title,
                    "subTitle":       cfg.get("subtitle", ""),
                    "url":            url,
                    "image":          img_url,
                    "price_sale":     sale,
                    "price_original": orig,
                    "gender":         cfg.get("gender", []),
                    "age_group":      cfg.get("age_group", ""),
                    "brand":          "worldbalance",
                }
                # bundle extras
                extras = {"category_path": path}
                rec["extra"] = json.dumps(extras, ensure_ascii=False)
                shoes.append(WorldBalanceShoe(**rec))
            except Exception as e:
                logger.error(f"Error parsing card in {path}: {e}")
        return shoes

    def _get_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, 'html.parser')
        nums = [int(a.get_text()) for a in soup.select('div.pagination a') if a.get_text().isdigit()]
        return max(nums) if nums else 1

    def extract(self) -> List[WorldBalanceShoe]:
        all_shoes: List[WorldBalanceShoe] = []
        paths = product_lists_url if self.category.lower() == "all" else [self.category]

        for p in paths:
            first_url = f"{BASE_URL}{COLLECTION_PATH}{p}"
            logger.info(f"→ Fetching {first_url}")
            resp = requests.get(first_url, headers=HEADERS)
            if resp.status_code != 200:
                logger.error(f"{p} fetch failed: {resp.status_code}")
                continue

            total_pages = self._get_total_pages(resp.text)
            logger.info(f"{p} has {total_pages} page(s)")

            for i in range(1, total_pages + 1):
                page_url = f"{first_url}?page={i}"
                logger.info(f"  · page {i}")
                r2 = requests.get(page_url, headers=HEADERS)
                if r2.status_code != 200:
                    logger.error(f"Page {i} failed: {r2.status_code}")
                    break

                batch = self._extract_products_from_html(r2.text, p)
                if not batch:
                    logger.info("No items; stopping pages loop.")
                    break

                all_shoes.extend(batch)
                if 0 <= self.num_pages == i:
                    break

                time.sleep(random.uniform(1, 2))

        return all_shoes
