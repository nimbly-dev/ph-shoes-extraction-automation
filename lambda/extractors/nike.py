# extractors/nike.py

import json
import re
import time
import requests
from typing import List, Optional
from dataclasses import dataclass
from logger import logger
from base.base import BaseShoe, BaseExtractor

@dataclass
class NikeShoe(BaseShoe):
    """
    All site-specific metadata is now in `extra` (JSON string).
    """
    brand: str = "nike"
    extra: Optional[str] = None


class NikeExtractor(BaseExtractor):
    BASE_URL = 'https://api.nike.com'
    SITE_BASE = 'https://www.nike.com/ph/w'
    API_BASE = 'https://api.nike.com'

    SESSION = requests.Session()
    SESSION.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "nike-api-caller-id": "com.nike.commerce.nikedotcom.snkrs.web"
    })

    PRODUCT_LISTS_URL = [
        '/mens-shoes-nik1zy7ok',
        '/womens-shoes-5e1x6zy7ok',
        '/older-kids-agibjzv4dh',
        '/little-kids-6dacezv4dh',
        '/baby-toddlers-kids-2j488zv4dh'
    ]

    # Note: gender as a list for consistency
    CATEGORY_CONFIG = {
        '/mens-shoes-nik1zy7ok':        {"gender": ["male"],   "age_group": "adult"},
        '/womens-shoes-5e1x6zy7ok':      {"gender": ["female"], "age_group": "adult"},
        '/older-kids-agibjzv4dh':        {"gender": ["unisex"], "age_group": "youth"},
        '/little-kids-6dacezv4dh':       {"gender": ["unisex"], "age_group": "kids"},
        '/baby-toddlers-kids-2j488zv4dh':{"gender": ["unisex"], "age_group": "toddlers"},
    }

    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category  = category
        self.num_pages = num_pages

    def _get_products_from_groupings(self, stub: str, products: list) -> list:
        resp = self.SESSION.get(f"{self.API_BASE}{stub}").json()
        for grp in resp.get('productGroupings', []):
            products.extend(grp.get('products') or [])
        nxt = resp.get('pages', {}).get('next')
        if nxt:
            return self._get_products_from_groupings(nxt, products)
        return products

    def _extract_product_data(self, product: dict) -> dict:
        # pull out site-specific fields
        return {
            'id':               product.get('productCode', ''),
            'title':            product.get('copy', {}).get('title', ''),
            'subTitle':         product.get('copy', {}).get('subTitle'),
            'url':              product.get('pdpUrl', {}).get('url'),
            'image':            product.get('colorwayImages', {}).get('portraitURL'),
            'price_original':   product.get('prices', {}).get('initialPrice'),
            'price_sale':       product.get('prices', {}).get('currentPrice'),
            'colordescription': product.get('displayColors', {}).get('colorDescription'),
            'out_of_stock':     any("OUT_OF_STOCK" in a for a in (product.get('featuredAttributes') or [])),
            'best_seller':      any("BEST_SELLER"  in a for a in (product.get('featuredAttributes') or [])),
        }

    def _process_category(self, path: str, config: dict) -> List[NikeShoe]:
        logger.info(f"→ Processing {path}")
        start_t = time.time()
        html = self.SESSION.get(f"{self.SITE_BASE}{path}").text

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not m:
            raise Exception(f"No __NEXT_DATA__ for {path}")

        redux = json.loads(m.group(1))
        state = redux['props']['pageProps']['initialState']
        wall  = (state if isinstance(state, dict) else json.loads(state)) \
                .get('Wall', {}) \
                .get('pageData', {})
        nxt = wall.get('next')
        if not nxt:
            raise Exception(f"No next URL in initialState for {path}")

        # normalize to anchor=0
        stub     = re.sub(r'anchor=\d+', 'anchor=0', nxt)
        products = self._get_products_from_groupings(stub, [])
        logger.info(f"Extracted {len(products)} items for {path}")

        shoes: List[NikeShoe] = []
        for p in products:
            d = self._extract_product_data(p)
            # build canonical record
            rec = {
                "id":             d['id'],
                "title":          d['title'],
                "subTitle":       d['subTitle'],
                "url":            d['url'],
                "image":          d['image'],
                "price_sale":     d['price_sale'] or 0.0,
                "price_original": d['price_original'] or 0.0,
                "gender":         config.get("gender", []),
                "age_group":      config.get("age_group", ""),
                "brand":          "nike",
            }
            # bundle site-specific bits into extra
            extras = {
                "colorDescription": d.get("colordescription"),
                "outOfStock":       d.get("out_of_stock"),
                "bestSeller":       d.get("best_seller"),
            }
            # drop any falsy values so JSON is minimal
            extras = {k: v for k, v in extras.items() if v not in (None, "", False)}
            rec["extra"] = json.dumps(extras, ensure_ascii=False) if extras else None

            shoes.append(NikeShoe(**rec))

        logger.info(f"→ Done {path} in {(time.time()-start_t):.1f}s")
        return shoes

    def extract(self) -> List[NikeShoe]:
        all_shoes: List[NikeShoe] = []

        if self.category.lower() == "all":
            for cat in self.PRODUCT_LISTS_URL:
                cfg = self.CATEGORY_CONFIG.get(cat, {})
                all_shoes.extend(self._process_category(cat, cfg))
        else:
            cat = self.category if self.category.startswith("/") else f"/{self.category}"
            cfg = self.CATEGORY_CONFIG.get(cat)
            if not cfg:
                raise ValueError(f"Unsupported category: {self.category}")
            all_shoes = self._process_category(cat, cfg)

        return all_shoes
