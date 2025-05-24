import json
import random
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
from dataclasses import dataclass
from base.base import BaseShoe, BaseExtractor
from logger import logger

BASE_URL = 'https://worldbalance.com.ph'
COLLECTION_PATH = '/collections'

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

# Category configuration
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

# Request headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

@dataclass
class WorldBalanceShoe(BaseShoe):
    pass

def parse_price(raw: str) -> Tuple[float, float]:
    """
    Given a string like "Regular price ₱1,999.00 Sale price ₱1,500.00",
    return (sale_price, original_price) = (1500.00, 1999.00).
    """
    # find all numbers with exactly two decimals
    matches = re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', raw)
    nums = [m.replace(',', '') for m in matches]
    if len(nums) >= 2:
        original = float(nums[0])
        sale     = float(nums[1])
        return sale, original
    if len(nums) == 1:
        v = float(nums[0])
        return v, v
    return 0.0, 0.0

class WorldBalanceExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category = category
        self.num_pages = num_pages

    def _extract_products_from_html(self, html: str, category_path: str) -> List[WorldBalanceShoe]:
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.grid__item[data-product-id]')
        if not cards:
            logger.warning(f"No product cards found in {category_path}")
            return []

        shoes: List[WorldBalanceShoe] = []
        for card in cards:
            try:
                pid      = card['data-product-id'].strip()
                link     = card.select_one('a.grid-product__link')
                name_el  = card.select_one('div.grid-product__title')
                price_el = card.select_one('div.grid-product__price')
                img_el   = card.select_one('img.grid-product__image')

                name = name_el.get_text(strip=True) if name_el else ''
                href = link['href'] if (link and link.has_attr('href')) else ''
                url  = href if href.startswith('http') else BASE_URL + href

                img_url = ''
                if img_el and img_el.has_attr('src'):
                    img_url = img_el['src']
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = BASE_URL + img_url

                raw_price = price_el.get_text(separator=' ', strip=True) if price_el else ''
                sale_price, original_price = parse_price(raw_price)

                details = category_config.get(category_path, {})
                shoes.append(WorldBalanceShoe(
                    id=pid,
                    title=name,
                    subTitle=details.get("subtitle", ""),
                    url=url,
                    image=img_url,
                    price_sale=sale_price,
                    price_original=original_price,
                    gender=details.get("gender", []),
                    age_group=details.get("age_group", "")
                ))
            except Exception as ex:
                logger.error(f"Error extracting card in {category_path}: {ex}")

        return shoes

    def _get_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, 'html.parser')
        pages = [int(a.get_text()) for a in soup.select('div.pagination a') if a.get_text().isdigit()]
        return max(pages) if pages else 1

    def extract(self) -> List[WorldBalanceShoe]:
        all_shoes: List[WorldBalanceShoe] = []
        paths = product_lists_url if self.category.lower() == "all" else [self.category]

        for path in paths:
            first_url = f"{BASE_URL}{COLLECTION_PATH}{path}"
            logger.info(f"→ Fetching {first_url}")
            resp = requests.get(first_url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch {first_url}: {resp.status_code}")
                continue

            total = self._get_total_pages(resp.text)
            logger.info(f"{path} has {total} page(s)")

            for page in range(1, total + 1):
                url = f"{BASE_URL}{COLLECTION_PATH}{path}?page={page}"
                logger.info(f"  · page {page}: {url}")
                r = requests.get(url, headers=headers)
                if r.status_code != 200:
                    logger.error(f"Failed to fetch {url}: {r.status_code}")
                    break

                shoes = self._extract_products_from_html(r.text, path)
                if not shoes:
                    logger.info(f"No items on page {page}; stopping.")
                    break

                all_shoes.extend(shoes)
                if 0 <= self.num_pages == page:
                    break
                time.sleep(random.uniform(1, 2))

        return all_shoes
