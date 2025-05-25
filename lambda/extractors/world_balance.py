import json
import random
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
from dataclasses import dataclass
from logger import logger
from base.base import BaseShoe, BaseExtractor

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

category_config = {
    '/performance':            {"gender": "male",   "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-m':            {"gender": "male",   "age_group": "adult", "subtitle": "lifestyle"},
    '/athleisure-m':           {"gender": "male",   "age_group": "adult", "subtitle": "athleisure"},
    '/classic-men-shoes':      {"gender": "male",   "age_group": "adult", "subtitle": "classic-shoes"},
    '/slipper-m':              {"gender": "male",   "age_group": "adult", "subtitle": "slipper"},
    '/performance-l':          {"gender": "female", "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-l':            {"gender": "female", "age_group": "adult", "subtitle": "lifestyle"},
    '/classic-women-shoes':    {"gender": "female", "age_group": "adult", "subtitle": "classic-shoes"},
    '/slippers-l':             {"gender": "female", "age_group": "adult", "subtitle": "slipper"},
    '/performance-kids':       {"gender": "unisex","age_group": "youth", "subtitle": "performance"},
    '/lifestyle-kids':         {"gender": "unisex","age_group": "youth", "subtitle": "lifestyle"},
    '/classic-children-shoes': {"gender": "unisex","age_group": "youth", "subtitle": "classic-shoes"},
    '/slippers-kids':          {"gender": "unisex","age_group": "youth", "subtitle": "slipper"},
    '/pe':                     {"gender": "unisex","age_group": "youth", "subtitle": "pe"},
    '/athleisure-kids':        {"gender": "unisex","age_group": "youth", "subtitle": "athleisure"},
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

@dataclass
class WorldBalanceShoe(BaseShoe):
    pass

def parse_price(raw: str) -> Tuple[float, float]:
    nums = [m.replace(',', '') for m in re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', raw)]
    if len(nums) >= 2:
        return float(nums[1]), float(nums[0])
    if nums:
        v = float(nums[0])
        return v, v
    return 0.0, 0.0

class WorldBalanceExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category = category
        self.num_pages = num_pages

    def _extract_products_from_html(self, html: str, path: str) -> List[WorldBalanceShoe]:
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div.grid__item[data-product-id]')
        shoes: List[WorldBalanceShoe] = []

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

                img_url = img['src'] if (img and img.has_attr('src')) else ''
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = BASE_URL + img_url

                raw = price.get_text(separator=' ', strip=True) if price else ''
                sale, orig = parse_price(raw)

                cfg = category_config.get(path, {})
                shoes.append(WorldBalanceShoe(
                    id=pid,
                    title=title,
                    subTitle=cfg.get("subtitle",""),
                    url=url,
                    image=img_url,
                    price_sale=sale,
                    price_original=orig,
                    gender=cfg.get("gender",""),
                    age_group=cfg.get("age_group","")
                ))
            except Exception as e:
                logger.error(f"Error on {path}: {e}")

        return shoes

    def _get_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, 'html.parser')
        nums = [int(a.get_text()) for a in soup.select('div.pagination a') if a.get_text().isdigit()]
        return max(nums) if nums else 1

    def extract(self) -> List[WorldBalanceShoe]:
        all_shoes: List[WorldBalanceShoe] = []
        paths = product_lists_url if self.category.lower()=="all" else [self.category]

        for p in paths:
            first = f"{BASE_URL}{COLLECTION_PATH}{p}"
            logger.info(f"→ Fetching {first}")
            r = requests.get(first, headers=headers)
            if r.status_code != 200:
                logger.error(f"{p} fetch failed: {r.status_code}")
                continue

            pages = self._get_total_pages(r.text)
            logger.info(f"{p} has {pages} page(s)")

            for i in range(1, pages+1):
                url = f"{BASE_URL}{COLLECTION_PATH}{p}?page={i}"
                logger.info(f"  · page {i}")
                resp = requests.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Page {i} failed: {resp.status_code}")
                    break

                shoes = self._extract_products_from_html(resp.text, p)
                if not shoes:
                    logger.info("No items; stopping pages loop.")
                    break

                all_shoes.extend(shoes)
                if 0 <= self.num_pages == i:
                    break
                time.sleep(random.uniform(1,2))

        return all_shoes
