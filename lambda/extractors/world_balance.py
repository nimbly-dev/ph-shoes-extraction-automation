import json
import random
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
from base.base import BaseShoe, BaseExtractor
from logger import logger

# Global configuration for World Balance
BASE_URL = 'https://worldbalance.com.ph/collections'

# List of category endpoints to process
product_lists_url = [
    '/performance',
    '/lifestyle-m',
    '/athleisure-m',
    '/classic-men-shoes',
    '/slipper-m',
    # WOMEN
    '/performance-l',
    '/lifestyle-l',
    '/classic-women-shoes',
    '/slippers-l',
    # KIDS
    '/performance-kids',
    '/lifestyle-kids',
    '/classic-children-shoes',
    '/slippers-kids',
    '/pe',
    '/athleisure-kids'
]

# Category configuration (includes extra details like subtitle)
category_config = {
    # MALE
    '/performance': {"gender": ["male"], "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-m': {"gender": ["male"], "age_group": "adult", "subtitle": "lifestyle"},
    '/athleisure-m': {"gender": ["male"], "age_group": "adult", "subtitle": "athleisure"},
    '/classic-men-shoes': {"gender": ["male"], "age_group": "adult", "subtitle": "classic-shoes"},
    '/slipper-m': {"gender": ["male"], "age_group": "adult", "subtitle": "slipper"},
    # FEMALE
    '/performance-l': {"gender": ["female"], "age_group": "adult", "subtitle": "performance"},
    '/lifestyle-l': {"gender": ["female"], "age_group": "adult", "subtitle": "lifestyle"},
    '/classic-women-shoes': {"gender": ["female"], "age_group": "adult", "subtitle": "classic-shoes"},
    '/slippers-l': {"gender": ["female"], "age_group": "adult", "subtitle": "slipper"},
    # KIDS
    '/performance-kids': {"gender": ["unisex"], "age_group": "youth", "subtitle": "performance"},
    '/lifestyle-kids': {"gender": ["unisex"], "age_group": "youth", "subtitle": "lifestyle"},
    '/classic-children-shoes': {"gender": ["unisex"], "age_group": "youth", "subtitle": "classic-shoes"},
    '/slippers-kids': {"gender": ["unisex"], "age_group": "youth", "subtitle": "slipper"},
    '/pe': {"gender": ["unisex"], "age_group": "youth", "subtitle": "pe"},
    '/athleisure-kids': {"gender": ["unisex"], "age_group": "youth", "subtitle": "athleisure"}
}

# Request headers for World Balance
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Define the WorldBalanceShoe dataclass.
@dataclass
class WorldBalanceShoe(BaseShoe):
    pass  # inherits fields from BaseShoe; we'll pass subtitle, gender, etc., into it

class WorldBalanceExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        """
        :param category: Category endpoint (e.g., '/performance') or 'all'.
        :param num_pages: Max pages per category (-1 = no limit).
        """
        self.category = category
        self.num_pages = num_pages

    def _extract_products_from_html(self, html: str, category_path: str) -> List[WorldBalanceShoe]:
        soup = BeautifulSoup(html, 'html.parser')
        shoes = []
        cards = soup.select('div.product-layout.product-item')
        logger.info(f"Found {len(cards)} cards in {category_path}")

        for card in cards:
            try:
                # 1) product_id from quickview JSON
                pid = None
                btn = card.select_one('button.quickview')
                if btn and (info := btn.get('data-productinfo')):
                    pid = str(json.loads(info)['id'])

                # 2) name & URL from the caption link
                a = card.select_one('h4.product-name a')
                name = a.get_text(strip=True) if a else ''
                href = a['href'] if a and a.has_attr('href') else ''
                url = href if href.startswith('http') else BASE_URL.split('/collections')[0] + href

                # 3) image URL: active slide first, then fallback
                img = (
                    card.select_one('.carousel-inner .item.active img') or
                    card.select_one('.images-container img')
                )
                img_url = ''
                if img:
                    img_url = img.get('data-src') or img.get('src') or ''
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = BASE_URL.split('/collections')[0] + img_url

                # 4) price extraction
                def clean(x): return float(re.sub(r'[^\d.]', '', x)) if x else None
                old_el = card.select_one('p.old-price span.price')
                new_el = card.select_one('p.regular-price span.price')
                if old_el and old_el.get_text(strip=True):
                    po = clean(old_el.text)
                    ps = clean(new_el.text) if new_el else po
                else:
                    po = clean(new_el.text if new_el else '')
                    ps = po

                # 5) merge category metadata
                details = category_config.get(category_path, {})
                data = {
                    "id": pid,
                    "title": name,
                    "subTitle": details.get("subtitle", ""),
                    "url": url,
                    "image": img_url,
                    "price_sale": ps if ps is not None else 0.0,
                    "price_original": po,
                    "gender": details.get("gender", []),
                    "age_group": details.get("age_group", "")
                }

                shoes.append(WorldBalanceShoe(**data))

            except Exception as ex:
                logger.error(f"Error extracting product details: {ex}")

        return shoes

    def _get_total_pages(self, html: str) -> int:
        soup = BeautifulSoup(html, 'html.parser')
        nums = [int(a.text) for a in soup.select('ul.pagination li a') if a.text.isdigit()]
        return max(nums) if nums else 1

    def extract(self) -> List[WorldBalanceShoe]:
        """
        Loop through either one category or all categories, paginate via ?page=N,
        and return a flat list of WorldBalanceShoe.
        """
        all_shoes: List[WorldBalanceShoe] = []
        paths = product_lists_url if self.category.lower() == "all" else [self.category]

        for path in paths:
            first_url = BASE_URL + path
            logger.info(f"Fetching first page: {first_url}")
            resp = requests.get(first_url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch {first_url}: {resp.status_code}")
                continue

            total_pages = self._get_total_pages(resp.text)
            logger.info(f"Total pages for {path}: {total_pages}")

            for page in range(1, total_pages + 1):
                page_url = f"{BASE_URL}{path}?page={page}"
                logger.info(f"Fetching page {page}: {page_url}")
                r = requests.get(page_url, headers=headers)
                if r.status_code != 200:
                    logger.error(f"Failed to fetch {page_url}: {r.status_code}")
                    break

                shoes = self._extract_products_from_html(r.text, path)
                if not shoes:
                    logger.info(f"No products on page {page} for {path}; stopping pagination.")
                    break

                all_shoes.extend(shoes)

                # stop early if user set num_pages
                if 0 <= self.num_pages == page:
                    break

                # polite crawl delay
                delay = random.uniform(1, 2)
                logger.info(f"Sleeping for {delay:.2f}s before next page...")
                time.sleep(delay)

        return all_shoes
