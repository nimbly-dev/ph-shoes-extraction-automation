import time
import re
import requests
import json
import html
import concurrent.futures
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass
from logger import logger
from .base import BaseShoe, BaseExtractor

# Global configuration for Hoka
base_url = "https://www.hoka.com/en/ph"

# List of category endpoints to process
product_lists_url = [
    # MEN
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
    # WOMEN
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
    # KIDS
    '/kids'
]

# Extra configuration for each category
category_config = {
    # MEN
    '/mens-road': {"gender": ["male"], "age_group": "adult", "subTitle": "road"},
    '/mens-trail': {"gender": ["male"], "age_group": "adult", "subTitle": "trail"},
    '/mens-trail-hiking-shoes': {"gender": ["male"], "age_group": "adult", "subTitle": "trail-hiking"},
    '/mens-walking': {"gender": ["male"], "age_group": "adult", "subTitle": "walking"},
    '/mens-fitness': {"gender": ["male"], "age_group": "adult", "subTitle": "fitness"},
    '/mens-recovery-comfort-shoes': {"gender": ["male"], "age_group": "adult", "subTitle": "recovery-comfort"},
    '/mens-stability-shoes': {"gender": ["male"], "age_group": "adult", "subTitle": "stability"},
    '/mens-wides': {"gender": ["male"], "age_group": "adult", "subTitle": "wides"},
    '/mens-sandals': {"gender": ["male"], "age_group": "adult", "subTitle": "sandals"},
    '/mens-lifestyle': {"gender": ["male"], "age_group": "adult", "subTitle": "lifestyle"},
    # WOMEN
    '/womens-road': {"gender": ["female"], "age_group": "adult", "subTitle": "road"},
    '/womens-trail': {"gender": ["female"], "age_group": "adult", "subTitle": "trail"},
    '/womens-trail-hiking-shoes': {"gender": ["female"], "age_group": "adult", "subTitle": "trail-hiking"},
    '/womens-walking': {"gender": ["female"], "age_group": "adult", "subTitle": "walking"},
    '/womens-fitness': {"gender": ["female"], "age_group": "adult", "subTitle": "fitness"},
    '/womens-recovery-comfort-shoes': {"gender": ["female"], "age_group": "adult", "subTitle": "recovery-comfort"},
    '/womens-stability-shoes': {"gender": ["female"], "age_group": "adult", "subTitle": "stability"},
    '/womens-wides': {"gender": ["female"], "age_group": "adult", "subTitle": "wides"},
    '/womens-sandals': {"gender": ["female"], "age_group": "adult", "subTitle": "sandals"},
    '/womens-lifestyle': {"gender": ["female"], "age_group": "adult", "subTitle": "lifestyle"},
    # KIDS
    '/kids': {"gender": ["unisex"], "age_group": "youth", "subTitle": "kids"}
}

@dataclass
class HokaShoe(BaseShoe):
    pass

def fetch_page(url: str) -> str:
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/116.0.5845.97 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def extract_image(prod) -> str:
    img_tag = prod.find("img", class_="tile-image")
    if img_tag and img_tag.get("src"):
        return img_tag.get("src").strip()
    image_container = prod.find("div", class_="image-container")
    if image_container and image_container.has_attr("data-images"):
        data_images = image_container["data-images"]
        try:
            images_data = json.loads(data_images)
            for key, group in images_data.items():
                if "default" in group and "medium" in group["default"]:
                    candidate = group["default"]["medium"][0].get("url")
                    if candidate:
                        return candidate.strip()
        except Exception:
            return ""
    return ""

def parse_hoka_products(html_content: str) -> List[dict]:
    soup = BeautifulSoup(html_content, 'html.parser')
    product_elements = soup.find_all('div', class_='product', attrs={'data-pid': True})
    products = []
    for prod in product_elements:
        record = {}
        record["id"] = prod.get("data-pid")
        name_container = prod.find("div", class_="tile-product-name")
        if name_container:
            a_tag = name_container.find("a", class_="link")
            if a_tag:
                record["title"] = a_tag.get_text(strip=True)
        a_link = prod.find("a", class_="js-pdp-link")
        if a_link and a_link.has_attr("href"):
            raw_url = a_link["href"].strip()
            record["url"] = raw_url if raw_url.startswith("http") else "https://www.hoka.com" + raw_url
        record["image"] = extract_image(prod)
        sale_span = prod.find("span", class_="sales")
        if sale_span:
            sale_text = sale_span.get_text(strip=True).replace("₱", "").replace(",", "").strip()
            try:
                record["price_sale"] = float(sale_text)
            except ValueError:
                record["price_sale"] = None
        else:
            record["price_sale"] = None
        orig_span = prod.find("span", class_="original-price")
        if orig_span:
            orig_text = orig_span.get_text(strip=True).replace("₱", "").replace(",", "").strip()
            try:
                record["price_original"] = int(float(orig_text))
            except ValueError:
                record["price_original"] = None
        else:
            record["price_original"] = record.get("price_sale")
        if record.get("id") and record.get("title"):
            products.append(record)
    return products

def safe_float(val):
    try:
        return float(re.sub(r'[^\d.]', '', str(val)))
    except Exception:
        return None

class HokaExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        """
        :param category: Category endpoint (e.g., '/mens-road') or 'all' for all categories.
        :param num_pages: Number of pages per category (-1 means fetch all products in one go).
        """
        self.category = category
        self.num_pages = num_pages

    def _scrape_category(self, cat_path: str) -> List[dict]:
        # Fetch a single large page instead of paginating incrementally.
        url = f"{base_url}{cat_path}/?sz=200"
        logger.info(f"Fetching large page: {url}")
        try:
            html_content = fetch_page(url)
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return []
        products = parse_hoka_products(html_content)
        logger.info(f"Found {len(products)} product(s) for {cat_path} in one shot.")
        return products

    def extract(self) -> List[HokaShoe]:
        all_products = []
        # Determine which categories to process.
        paths = product_lists_url if self.category.lower() == "all" else [self.category]

        def process_category(path):
            logger.info(f"Processing category: {path}")
            products = self._scrape_category(path)
            # Merge extra fields from configuration.
            if path in category_config:
                extra_fields = category_config[path]
                for product in products:
                    product.update(extra_fields)
            else:
                inferred = path.lstrip("/").split("-")[-1]
                for product in products:
                    product["subTitle"] = inferred
            return products

        # Use ThreadPoolExecutor to process categories concurrently.
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_category, path): path for path in paths}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    all_products.extend(result)
                except Exception as exc:
                    logger.error(f"Category {futures[future]} generated an exception: {exc}")

        # Convert dictionaries to HokaShoe dataclass instances.
        shoes = []
        for rec in all_products:
            rec["price_sale"] = safe_float(rec.get("price_sale"))
            rec["price_original"] = safe_float(rec.get("price_original")) or rec.get("price_sale")
            try:
                shoe = HokaShoe(**rec)
                shoes.append(shoe)
            except Exception as ex:
                logger.error(f"Error creating HokaShoe: {ex}")
        return shoes
