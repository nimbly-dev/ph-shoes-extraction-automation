# extractors/nike.py

import json
import re
import time
import requests
from typing import List, Optional
from dataclasses import dataclass

import pandas as pd

from base.base import BaseShoe, BaseExtractor
from logger import logger


@dataclass
class NikeShoe(BaseShoe):
    """
    Site‐specific metadata is now in `extra` (JSON string).
    """
    brand: str = "nike"
    extra: Optional[str] = None


class NikeExtractor(BaseExtractor):
    SITE_BASE = 'https://www.nike.com/ph/w'
    API_BASE  = 'https://api.nike.com'

    # one Session for all requests
    SESSION = requests.Session()
    SESSION.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        ),
        "nike-api-caller-id": "com.nike.commerce.nikedotcom.snkrs.web"
    })

    PRODUCT_LISTS_URL = [
        '/mens-shoes-nik1zy7ok',
        '/womens-shoes-5e1x6zy7ok',
        '/older-kids-agibjzv4dh',
        '/little-kids-6dacezv4dh',
        '/baby-toddlers-kids-2j488zv4dh'
    ]
    CATEGORY_CONFIG = {
        '/mens-shoes-nik1zy7ok':         {"gender": ["male"],    "age_group": "adult"},
        '/womens-shoes-5e1x6zy7ok':       {"gender": ["female"],  "age_group": "adult"},
        '/older-kids-agibjzv4dh':         {"gender": ["unisex"],  "age_group": "youth"},
        '/little-kids-6dacezv4dh':        {"gender": ["unisex"],  "age_group": "kids"},
        '/baby-toddlers-kids-2j488zv4dh': {"gender": ["unisex"],  "age_group": "toddlers"},
    }

    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category  = category
        self.num_pages = num_pages

    def _get_products_from_groupings(self, stub: Optional[str], products: list) -> list:
        if not stub:
            return products
        resp = self.SESSION.get(self.API_BASE + stub).json()
        for grp in resp.get('productGroupings', []) or []:
            products.extend(grp.get('products') or [])
        nxt = resp.get('pages', {}).get('next')
        return self._get_products_from_groupings(nxt, products) if nxt else products

    def _extract_product_data(self, product: dict) -> dict:
        # core fields
        return {
            'id':              product.get('productCode', ''),
            'title':           product.get('copy', {}).get('title', ''),
            'subTitle':        product.get('copy', {}).get('subTitle'),
            'url':             product.get('pdpUrl', {}).get('url', ''),
            'image':           product.get('colorwayImages', {}).get('portraitURL'),
            'price_original':  product.get('prices', {}).get('initialPrice', 0.0),
            'price_sale':      product.get('prices', {}).get('currentPrice', 0.0),
        }

    def _process_category(self, path: str, cfg: dict) -> List[NikeShoe]:
        logger.info(f"Processing category: {path}")
        html = self.SESSION.get(self.SITE_BASE + path).text
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not m:
            raise Exception(f"__NEXT_DATA__ not found for {path}")
        redux = json.loads(m.group(1))

        try:
            wall = redux['props']['pageProps']['initialState']['Wall']
            stub = re.sub(r'anchor=\d+', 'anchor=0', wall['pageData']['next'])
        except KeyError:
            raise Exception(f"Lazy-load URL missing in JSON for {path}")

        raw = self._get_products_from_groupings(stub, [])
        logger.info(f"Extracted {len(raw)} items for {path}")

        shoes: List[NikeShoe] = []
        for p in raw:
            d = self._extract_product_data(p)
            # build BaseShoe fields + gender/age_group
            rec = {
                "id":             d['id'],
                "title":          d['title'],
                "subTitle":       d['subTitle'],
                "url":            d['url'],
                "image":          d['image'],
                "price_sale":     d['price_sale'],
                "price_original": d['price_original'],
                "gender":         cfg.get("gender", []),
                "age_group":      cfg.get("age_group", ""),
                "brand":          "nike",
            }
            # only colorDescription in `extra`
            cd = p.get('displayColors', {}).get('colorDescription')
            rec["extra"] = json.dumps({"colorDescription": cd}, ensure_ascii=False) if cd else None

            shoes.append(NikeShoe(**rec))

        return shoes

    def extract(self) -> List[NikeShoe]:
        all_shoes: List[NikeShoe] = []
        if self.category.lower() == "all":
            for path, cfg in self.CATEGORY_CONFIG.items():
                all_shoes.extend(self._process_category(path, cfg))
        else:
            p = self.category if self.category.startswith("/") else f"/{self.category}"
            cfg = self.CATEGORY_CONFIG.get(p)
            if not cfg:
                raise ValueError(f"Unsupported category: {self.category}")
            all_shoes = self._process_category(p, cfg)

        return all_shoes
