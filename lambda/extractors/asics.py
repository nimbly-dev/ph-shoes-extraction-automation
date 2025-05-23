import time
import re
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
from base.base import BaseShoe, BaseExtractor
from logger import logger
import html
import json

# Global configuration for Asics
BASE_URL = "https://www.asics.com/ph/en-ph"
# List of category endpoints to process
product_lists_url = [
    # MEN
    '/running013',
    '/sportstyle013',
    '/indoor013',
    '/volleyball013',
    '/tennis013',
    '/trailrunning013',
    '/basketball013',
    '/soccer013',
    '/basketball013',
    '/cricket013',
    '/others013',
    # WOMEN
    '/running023',
    '/sportstyle023',
    '/indoor023',
    '/volleyball023',
    '/netball023',
    '/tennis023',
    '/trailrunning023',
    '/basketball023',
    '/soccer023',
    # KIDS
    '/running033',
    '/kids-indoor-shoes',
    '/kids-tennis-shoes',
    '/casual033'
]

# Category configuration with extra details
category_config = {
    # MALE
    '/running013': {"gender": ["male"], "age_group": "adult"},
    '/sportstyle013': {"gender": ["male"], "age_group": "adult"},
    '/indoor013': {"gender": ["male"], "age_group": "adult"},
    '/volleyball013': {"gender": ["male"], "age_group": "adult"},
    '/tennis013': {"gender": ["male"], "age_group": "adult"},
    '/trailrunning013': {"gender": ["male"], "age_group": "adult"},
    '/basketball013': {"gender": ["male"], "age_group": "adult"},
    '/soccer013': {"gender": ["male"], "age_group": "adult"},
    '/cricket013': {"gender": ["male"], "age_group": "adult"},
    '/others013': {"gender": ["male"], "age_group": "adult"},
    # FEMALE
    '/running023': {"gender": ["female"], "age_group": "adult"},
    '/sportstyle023': {"gender": ["female"], "age_group": "adult"},
    '/indoor023': {"gender": ["female"], "age_group": "adult"},
    '/volleyball023': {"gender": ["female"], "age_group": "adult"},
    '/netball023': {"gender": ["female"], "age_group": "adult"},
    '/tennis023': {"gender": ["female"], "age_group": "adult"},
    '/trailrunning023': {"gender": ["female"], "age_group": "adult"},
    '/basketball023': {"gender": ["female"], "age_group": "adult"},
    '/soccer023': {"gender": ["female"], "age_group": "adult"},
    # KIDS
    '/running033': {"gender": ["unisex"], "age_group": "youth"},
    '/kids-indoor-shoes': {"gender": ["unisex"], "age_group": "youth"},
    '/kids-tennis-shoes': {"gender": ["unisex"], "age_group": "youth"},
    '/casual033': {"gender": ["unisex"], "age_group": "youth"}
}

# Page size for pagination
PAGE_SIZE = 24

@dataclass
class AsicsShoe(BaseShoe):
    # Inherit from BaseShoe; add any Asics-specific fields if needed.
    pass

class AsicsExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        """
        :param category: Category endpoint (e.g., '/running013') or 'all' for all categories.
        :param num_pages: Number of pages per category (-1 means loop until no products are found).
        """
        self.category = category
        self.num_pages = num_pages

    def _fetch_page(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text

    def _extract_products_from_html(self, html: str, category_path: str) -> List[AsicsShoe]:
        """
        Extract product details from the HTML of a category page.
        Returns a list of AsicsShoe instances.
        """
        soup = BeautifulSoup(html, 'html.parser')
        products = soup.find_all('div', class_='product-tile')
        shoes = []
        for prod in products:
            try:
                prod_id = prod.get('data-itemid')
                title_elem = prod.find('div', class_='product-name')
                title = title_elem.text.strip() if title_elem else None
                subtitle_elem = prod.select_one(".product-tile__text.product-tile__text--small.xx-small-reg")
                subtitle = subtitle_elem.text.strip() if subtitle_elem else None
                a_tag = prod.find_parent("a", class_="product-tile__link")
                raw_url = a_tag["href"].strip() if (a_tag and a_tag.has_attr("href")) else None
                prod_url = f"{raw_url.rstrip('/')}/{prod_id}.html" if (raw_url and prod_id) else None
                image = self._extract_image_from_prod(prod)
                sale_price_elem = prod.find('span', class_='price-sales')
                price_sale = sale_price_elem.text.strip() if sale_price_elem else None
                original_price_elem = prod.find('span', class_='price-original')
                if not original_price_elem:
                    original_price_elem = prod.find('span', class_='price-standard')
                price_original = original_price_elem.text.strip() if original_price_elem else price_sale

                def parse_price(p):
                    if p:
                        num = re.sub(r'[^\d.]', '', p)
                        return float(num) if num else None
                    return None

                price_sale_val = parse_price(price_sale)
                price_original_val = parse_price(price_original)
                if price_sale_val is None:
                    price_sale_val = price_original_val

                cat_details = category_config.get(category_path, {})
                record = {
                    "id": prod_id,
                    "title": title,
                    "subTitle": subtitle,
                    "url": prod_url,
                    "image": image,
                    "price_sale": price_sale_val if price_sale_val is not None else 0.0,
                    "price_original": price_original_val,
                    "gender": cat_details.get("gender", []),
                    "age_group": cat_details.get("age_group", "")
                }
                shoe = AsicsShoe(**record)
                shoes.append(shoe)
            except Exception as ex:
                logger.error(f"Error extracting product details: {ex}")
        return shoes

    def _extract_image_from_prod(self, prod) -> str:
        """
        Extract the product image URL from a product tile.
        """
        img_elem = prod.find("img", class_="product-tile__image")
        candidate = None
        if img_elem:
            candidate = img_elem.get("data-src-load-more", "").strip()
            if candidate.startswith("data:") or len(candidate) < 30:
                candidate = img_elem.get("src", "").strip()
                if candidate.startswith("data:") or len(candidate) < 30:
                    candidate = None
            if not candidate and img_elem.has_attr("data-alt-image"):
                alt_img_str = html.unescape(img_elem["data-alt-image"])
                try:
                    alt_data = json.loads(alt_img_str)
                    candidate = alt_data.get("src")
                except Exception:
                    candidate = None
        if (not candidate or len(candidate) < 30) and prod.get("data-itemid"):
            prod_id = prod.get("data-itemid")
            parts = prod_id.split("-")
            if len(parts) == 2:
                first, second = parts
                candidate = f"https://images.asics.com/is/image/asics/{first}_{second}_SR_RT_AJP?$productlist$"
        return candidate

    def _process_category(self, category_path: str) -> List[AsicsShoe]:
        """
        Process a single category by paginating through the pages.
        """
        category_url = f"{BASE_URL}{category_path}/"
        all_shoes = []
        start = 0
        while True:
            paged_url = f"{category_url}?start={start}&sz={PAGE_SIZE}"
            logger.info(f"Fetching: {paged_url}")
            try:
                html_content = self._fetch_page(paged_url)
            except Exception as e:
                logger.error(f"Error fetching page {paged_url}: {e}")
                break
            shoes = self._extract_products_from_html(html_content, category_path)
            logger.info(f"Found {len(shoes)} products on page starting at {start}")
            if not shoes:
                break
            all_shoes.extend(shoes)
            start += PAGE_SIZE
            if self.num_pages != -1 and start >= self.num_pages * PAGE_SIZE:
                break
            time.sleep(0.25)  # Consider reducing delay if rate limits allow
        return all_shoes

    def extract(self) -> List[AsicsShoe]:
        """
        Process either a specific category or all Asics categories concurrently.
        """
        all_shoes = []
        if self.category.lower() == "all":
            paths = product_lists_url
        else:
            paths = [self.category]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_path = {executor.submit(self._process_category, path): path for path in paths}
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    shoes = future.result()
                    logger.info(f"Completed processing {path}: {len(shoes)} products found.")
                    all_shoes.extend(shoes)
                except Exception as exc:
                    logger.error(f"Error processing category {path}: {exc}")
        return all_shoes
