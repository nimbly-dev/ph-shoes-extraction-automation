# extractors/nike.py

import json
import re
import requests
import pandas as pd
from typing import List, Optional, Dict
from dataclasses import dataclass

from base.base import BaseShoe, BaseExtractor
from logger import logger

SITE_BASE = "https://www.nike.com/ph"
API_BASE  = "https://api.nike.com"

# -----------------------------------------------------------------------------
# Back-compat constants expected by tests
# -----------------------------------------------------------------------------
# Old-style listing paths (what tests iterate over)
PRODUCT_LISTS_URL = [
    "/mens-shoes-nik1zy7ok",
    "/womens-shoes-5e1x6zy7ok",
    "/older-kids-agibjzv4dh",
    "/little-kids-6dacezv4dh",
    "/baby-toddlers-kids-2j488zv4dh",
]

# Map old listing paths → our internal category keys
PATH_TO_CATEGORY = {
    "/mens-shoes-nik1zy7ok":            "men-shoes",
    "/womens-shoes-5e1x6zy7ok":         "women-shoes",
    "/older-kids-agibjzv4dh":           "older-kids-shoes",
    "/little-kids-6dacezv4dh":          "little-kids-shoes",
    "/baby-toddlers-kids-2j488zv4dh":   "baby-toddlers-shoes",
}

# -----------------------------------------------------------------------------
# Category → metadata (human-friendly keys we’ll also store as 'category')
# -----------------------------------------------------------------------------
CATEGORY_CONFIG = {
    "men-shoes":           {"gender": ["male"],   "age_group": "adult"},
    "women-shoes":         {"gender": ["female"], "age_group": "adult"},
    "older-kids-shoes":    {"gender": ["unisex"], "age_group": "youth"},
    "little-kids-shoes":   {"gender": ["unisex"], "age_group": "kids"},
    "baby-toddlers-shoes": {"gender": ["unisex"], "age_group": "toddlers"},
}

# Pre-resolved size-filter listing URLs per category on nike.com/ph
SIZE_URLS: Dict[str, Dict[str, str]] = {
    "men-shoes": {
        "3 US": "/w/mens-shoes-1v44nznik1zy7ok", "3.5 US": "/w/mens-shoes-1hsnhznik1zy7ok",
        "4 US": "/w/mens-shoes-4bkcbznik1zy7ok", "4.5 US": "/w/mens-shoes-8xhrhznik1zy7ok",
        "5 US": "/w/mens-shoes-nik1zv660zy7ok",  "5.5 US": "/w/mens-shoes-8slorznik1zy7ok",
        "6 US": "/w/mens-shoes-5sx0aznik1zy7ok", "6.5 US": "/w/mens-shoes-9ms5qznik1zy7ok",
        "7 US": "/w/mens-shoes-8nb9wznik1zy7ok", "7.5 US": "/w/mens-shoes-40x25znik1zy7ok",
        "8 US": "/w/mens-shoes-8ucbuznik1zy7ok", "8.5 US": "/w/mens-shoes-nik1zqrpuzy7ok",
        "9 US": "/w/mens-shoes-nik1zstp2zy7ok",  "9.5 US": "/w/mens-shoes-38l5kznik1zy7ok",
        "10 US": "/w/mens-shoes-2eqihznik1zy7ok","10.5 US": "/w/mens-shoes-4heq9znik1zy7ok",
        "11 US": "/w/mens-shoes-79n0gznik1zy7ok","11.5 US": "/w/mens-shoes-hrcoznik1zy7ok",
        "12 US": "/w/mens-shoes-1m67gznik1zy7ok","12.5 US": "/w/mens-shoes-apms5znik1zy7ok",
        "13 US": "/w/mens-shoes-9hh0lznik1zy7ok","13.5 US": "/w/mens-shoes-3phogznik1zy7ok",
        "14 US": "/w/mens-shoes-6xge1znik1zy7ok","15 US": "/w/mens-shoes-6m79uznik1zy7ok",
        "16 US": "/w/mens-shoes-1je5yznik1zy7ok","17 US": "/w/mens-shoes-48901znik1zy7ok",
        "18 US": "/w/mens-shoes-5pxh3znik1zy7ok",
    },
    "women-shoes": {
        "4.5 US": "/w/womens-shoes-5e1x6z7sfsyzy7ok", "5 US": "/w/womens-shoes-5e1x6zb2h62zy7ok",
        "5.5 US": "/w/womens-shoes-5e1x6zy7okzyt35",  "6 US": "/w/womens-shoes-4i7w1z5e1x6zy7ok",
        "6.5 US": "/w/womens-shoes-5e1x6z77ghyzy7ok", "7 US": "/w/womens-shoes-5e1x6zvyaizy7ok",
        "7.5 US": "/w/womens-shoes-5e1x6z6p31wzy7ok", "8 US": "/w/womens-shoes-5e1x6zom6bzy7ok",
        "8.5 US": "/w/womens-shoes-1cssqz5e1x6zy7ok", "9 US": "/w/womens-shoes-5e1x6z7p17azy7ok",
        "9.5 US": "/w/womens-shoes-200vmz5e1x6zy7ok", "10 US": "/w/womens-shoes-5e1x6z7xrj1zy7ok",
        "10.5 US": "/w/womens-shoes-56vxcz5e1x6zy7ok","11 US": "/w/womens-shoes-5bmh1z5e1x6zy7ok",
        "11.5 US": "/w/womens-shoes-3ms32z5e1x6zy7ok","12 US": "/w/womens-shoes-5e1x6z5jjvbzy7ok",
        "12.5 US": "/w/womens-shoes-5e1x6z6ch1jzy7ok","13 US": "/w/womens-shoes-5e1x6zb1xcizy7ok",
        "13.5 US": "/w/womens-shoes-5e1x6zgq8xzy7ok","14 US": "/w/womens-shoes-5e1x6z88difzy7ok",
        "14.5 US": "/w/womens-shoes-5e1x6z5rl2czy7ok","15 US": "/w/womens-shoes-5e1x6z9pl4gzy7ok",
        "15.5 US": "/w/womens-shoes-5e1x6z72tdlzy7ok","16.5 US": "/w/womens-shoes-4les7z5e1x6zy7ok",
    },
    "older-kids-shoes": {
        "11 C": "/w/older-kids-shoes-1ang5zagibjzv4dhzy7ok", "12 C": "/w/older-kids-shoes-2sv6bzagibjzv4dhzy7ok",
        "13 C": "/w/older-kids-shoes-3bgsfzagibjzv4dhzy7ok", "1 Y": "/w/older-kids-shoes-51udizagibjzv4dhzy7ok",
        "1.5 Y": "/w/older-kids-shoes-3quq7zagibjzv4dhzy7ok", "2 Y": "/w/older-kids-shoes-a9ncqzagibjzv4dhzy7ok",
        "2.5 Y": "/w/older-kids-shoes-6hvv3zagibjzv4dhzy7ok", "3 Y": "/w/older-kids-shoes-75n0izagibjzv4dhzy7ok",
        "3.5 Y": "/w/older-kids-shoes-681nlzagibjzv4dhzy7ok", "4 Y": "/w/older-kids-shoes-a86mozagibjzv4dhzy7ok",
        "4.5 Y": "/w/older-kids-shoes-8f8l9zagibjzv4dhzy7ok", "5 Y": "/w/older-kids-shoes-21f2mzagibjzv4dhzy7ok",
        "5.5 Y": "/w/older-kids-shoes-5vs8dzagibjzv4dhzy7ok", "6 Y": "/w/older-kids-shoes-6518wzagibjzv4dhzy7ok",
        "6.5 Y": "/w/older-kids-shoes-70asdzagibjzv4dhzy7ok", "7 Y": "/w/older-kids-shoes-8efwtzagibjzv4dhzy7ok",
    },
    "little-kids-shoes": {
        "8 C": "/w/little-kids-shoes-6dacez8ri95zv4dhzy7ok", "9 C": "/w/little-kids-shoes-6dacez8r17kzv4dhzy7ok",
        "10 C": "/w/little-kids-shoes-4f4haz6dacezv4dhzy7ok","10.5 C": "/w/little-kids-shoes-6dacez8eap3zv4dhzy7ok",
        "11 C": "/w/little-kids-shoes-1ang5z6dacezv4dhzy7ok","11.5 C": "/w/little-kids-shoes-1o9cuz6dacezv4dhzy7ok",
        "12 C": "/w/little-kids-shoes-2sv6bz6dacezv4dhzy7ok","12.5 C": "/w/little-kids-shoes-3gquuz6dacezv4dhzy7ok",
        "13 C": "/w/little-kids-shoes-3bgsfz6dacezv4dhzy7ok","13.5 C": "/w/little-kids-shoes-26bdlz6dacezv4dhzy7ok",
        "1 Y": "/w/little-kids-shoes-51udiz6dacezv4dhzy7ok","1.5 Y": "/w/little-kids-shoes-3quq7z6dacezv4dhzy7ok",
        "2 Y": "/w/little-kids-shoes-6daceza9ncqzv4dhzy7ok","2.5 Y": "/w/little-kids-shoes-6dacez6hvv3zv4dhzy7ok",
        "3 Y": "/w/little-kids-shoes-6dacez75n0izagibjzv4dhzy7ok",
    },
    "baby-toddlers-shoes": {
        "2 C": "/w/baby-toddlers-kids-shoes-2j488za7hnezv4dhzy7ok", "3 C": "/w/baby-toddlers-kids-shoes-2j488z5mg8fzv4dhzy7ok",
        "4 C": "/w/baby-toddlers-kids-shoes-2j488z32xf6zv4dhzy7ok", "5 C": "/w/baby-toddlers-kids-shoes-204f8z2j488zv4dhzy7ok",
        "6 C": "/w/baby-toddlers-kids-shoes-2j488z8b77nzv4dhzy7ok", "7 C": "/w/baby-toddlers-kids-shoes-2ggmfz2j488zv4dhzy7ok",
        "8 C": "/w/baby-toddlers-kids-shoes-2j488z8ri95zv4dhzy7ok","9 C": "/w/baby-toddlers-kids-shoes-2j488z8r17kzv4dhzy7ok",
        "10 C": "/w/baby-toddlers-kids-shoes-2j488z4f4hazv4dhzy7ok",
    },
}

@dataclass
class NikeShoe(BaseShoe):
    brand: str = "nike"
    extra: Optional[str] = None


class NikeExtractor(BaseExtractor):
    # expose for tests
    PRODUCT_LISTS_URL = PRODUCT_LISTS_URL

    SESSION = requests.Session()
    SESSION.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        ),
        "nike-api-caller-id": "com.nike.commerce.nikedotcom.snkrs.web"
    })

    def __init__(self, category: str = "all", num_pages: int = -1):
        # Accept:
        #  - "all"
        #  - new keys like "men-shoes"
        #  - back-compat listing paths like "/mens-shoes-nik1zy7ok"
        cat = (category or "all").lower()
        if cat.startswith("/"):
            cat = PATH_TO_CATEGORY.get(cat, cat)
        self.category  = cat
        self.num_pages = num_pages  # unused

    def _get_stub(self, path: str) -> str:
        html = self.SESSION.get(f"{SITE_BASE}{path}", timeout=30).text
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not m:
            raise RuntimeError(f"No __NEXT_DATA__ for {path}")
        redux = json.loads(m.group(1))
        try:
            stub = redux["props"]["pageProps"]["initialState"]["Wall"]["pageData"]["next"]
        except KeyError:
            raise RuntimeError(f"Missing Wall.pageData.next in JSON for {path}")
        stub = re.sub(r"anchor=\d+", "anchor=0", stub)
        return stub.replace("count=24", "count=100")

    def _fetch_products(self, stub: str) -> List[dict]:
        url = stub if stub.startswith("http") else API_BASE + stub
        resp = self.SESSION.get(url, timeout=30)
        if resp.headers.get("Content-Type","").startswith("text/html"):
            logger.warning(f"Blocked (HTML) from {url}")
            return []
        data = resp.json()
        products = []
        for grp in data.get("productGroupings", []) or []:
            products.extend(grp.get("products", []) or [])
        return products

    def extract(self) -> List[NikeShoe]:
        cats = list(CATEGORY_CONFIG) if self.category == "all" else [self.category]
        raw: List[dict] = []

        for cat in cats:
            cfg = CATEGORY_CONFIG.get(cat)
            if not cfg:
                raise ValueError(f"Unsupported category: {cat}")
            for size_lbl, path in SIZE_URLS[cat].items():
                logger.info(f"[Nike] {cat} | size={size_lbl}")
                try:
                    stub = self._get_stub(path)
                    items = self._fetch_products(stub)
                except Exception as e:
                    logger.warning(f"[Nike] stub/items error for {path}: {e}")
                    continue

                for p in items:
                    rec = {
                        "id":             p.get("productCode",""),
                        "title":          p.get("copy",{}).get("title",""),
                        "subTitle":       p.get("copy",{}).get("subTitle"),
                        "url":            p.get("pdpUrl",{}).get("url",""),
                        "image":          p.get("colorwayImages",{}).get("portraitURL",""),
                        "price_sale":     p.get("prices",{}).get("currentPrice",0.0),
                        "price_original": p.get("prices",{}).get("initialPrice",0.0),
                        "gender":         cfg["gender"],
                        "age_group":      cfg["age_group"],
                        "brand":          "nike",
                    }
                    extra_obj = {"category": cat, "sizes": [size_lbl]}
                    cd = p.get("displayColors",{}).get("colorDescription")
                    if cd: extra_obj["colorDescription"] = cd
                    feats = set(p.get("featuredAttributes") or [])
                    if feats:
                        extra_obj["best_seller"]  = ("BEST_SELLER" in feats)
                        extra_obj["out_of_stock"] = ("OUT_OF_STOCK" in feats)
                    rec["extra"] = json.dumps(extra_obj, ensure_ascii=False)
                    raw.append(rec)

        if not raw:
            return []

        # merge by id, union sizes inside extra
        df = pd.DataFrame(raw)
        merged = []
        for pid, grp in df.groupby("id", sort=False):
            base = grp.iloc[0].to_dict()

            sizes = set()
            category = None
            color_desc = None
            best_seller = None
            out_of_stock = None

            for blob in grp["extra"].dropna():
                try:
                    obj = json.loads(blob)
                    for s in obj.get("sizes") or []:
                        sizes.add(str(s))
                    if not category and obj.get("category"):
                        category = obj["category"]
                    if color_desc is None and obj.get("colorDescription"):
                        color_desc = obj["colorDescription"]
                    if best_seller is None and "best_seller" in obj:
                        best_seller = bool(obj["best_seller"])
                    if out_of_stock is None and "out_of_stock" in obj:
                        out_of_stock = bool(obj["out_of_stock"])
                except Exception:
                    continue

            extra_obj = {"category": category or "", "sizes": sorted(sizes, key=lambda x: float(x.split()[0]))}
            if color_desc is not None:
                extra_obj["colorDescription"] = color_desc
            if best_seller is not None:
                extra_obj["best_seller"] = best_seller
            if out_of_stock is not None:
                extra_obj["out_of_stock"] = out_of_stock
            base["extra"] = json.dumps(extra_obj, ensure_ascii=False)

            base["price_sale"]     = pd.to_numeric(grp["price_sale"], errors="coerce").min()
            base["price_original"] = pd.to_numeric(grp["price_original"], errors="coerce").min()

            merged.append(base)

        return [NikeShoe(**r) for r in pd.DataFrame(merged).to_dict("records")]
