# extractors/hoka.py  (Lambda-friendly)

import time
import requests
import json
import html
import re
import concurrent.futures
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup

from logger import logger
from base.base import BaseShoe, BaseExtractor

DOMAIN_BASE = "https://www.hoka.com"
BASE_URL    = f"{DOMAIN_BASE}/en/ph"
HEADERS     = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MAX_SZ      = 200  # pull many items per listing

# Keep ONLY numeric sizes 6 .. 13 (with halves)
SIZE_VALUES: List[str] = [
    "6", "6.5", "7", "7.5", "8", "8.5",
    "9", "9.5", "10", "10.5", "11", "11.5", "12", "13"
]
SIZE_SET = set(SIZE_VALUES)

PRODUCT_LISTS = [
    # MEN
    "/mens-road",
    "/mens-trail",
    "/mens-trail-hiking-shoes",
    "/mens-walking",
    "/mens-fitness",
    "/mens-recovery-comfort-shoes",
    "/mens-stability-shoes",
    "/mens-wides",
    "/mens-sandals",
    "/mens-lifestyle",
    # WOMEN
    "/womens-road",
    "/womens-trail",
    "/womens-trail-hiking-shoes",
    "/womens-walking",
    "/womens-fitness",
    "/womens-recovery-comfort-shoes",
    "/womens-stability-shoes",
    "/womens-wides",
    "/womens-sandals",
    "/womens-lifestyle",
    # KIDS
    "/kids",
]

CATEGORY_CONFIG: Dict[str, Dict[str, Any]] = {
    "/mens-road":    {"gender": ["male"],   "age_group": "adult", "subTitle": "road"},
    "/mens-trail":   {"gender": ["male"],   "age_group": "adult", "subTitle": "trail"},
    "/mens-trail-hiking-shoes": {"gender": ["male"], "age_group": "adult", "subTitle": "trail-hiking"},
    "/mens-walking": {"gender": ["male"],   "age_group": "adult", "subTitle": "walking"},
    "/mens-fitness": {"gender": ["male"],   "age_group": "adult", "subTitle": "fitness"},
    "/mens-recovery-comfort-shoes": {"gender": ["male"], "age_group": "adult", "subTitle": "recovery-comfort"},
    "/mens-stability-shoes": {"gender": ["male"],   "age_group": "adult", "subTitle": "stability"},
    "/mens-wides":   {"gender": ["male"],   "age_group": "adult", "subTitle": "wides"},
    "/mens-sandals": {"gender": ["male"],   "age_group": "adult", "subTitle": "sandals"},
    "/mens-lifestyle": {"gender": ["male"], "age_group": "adult", "subTitle": "lifestyle"},

    "/womens-road":    {"gender": ["female"], "age_group": "adult", "subTitle": "road"},
    "/womens-trail":   {"gender": ["female"], "age_group": "adult", "subTitle": "trail"},
    "/womens-trail-hiking-shoes": {"gender": ["female"], "age_group": "adult", "subTitle": "trail-hiking"},
    "/womens-walking": {"gender": ["female"], "age_group": "adult", "subTitle": "walking"},
    "/womens-fitness": {"gender": ["female"], "age_group": "adult", "subTitle": "fitness"},
    "/womens-recovery-comfort-shoes": {"gender": ["female"], "age_group": "adult", "subTitle": "recovery-comfort"},
    "/womens-stability-shoes": {"gender": ["female"], "age_group": "adult", "subTitle": "stability"},
    "/womens-wides":   {"gender": ["female"], "age_group": "adult", "subTitle": "wides"},
    "/womens-sandals": {"gender": ["female"], "age_group": "adult", "subTitle": "sandals"},
    "/womens-lifestyle": {"gender": ["female"], "age_group": "adult", "subTitle": "lifestyle"},

    "/kids": {"gender": ["unisex"], "age_group": "youth", "subTitle": "kids"},
}

@dataclass
class HokaShoe(BaseShoe):
    brand: str = "hoka"


# ---------------- helpers ----------------

def _abs_url(href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return f"{DOMAIN_BASE}{href}"
    return f"{BASE_URL}/{href}"

def _abs_asset(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("http"):
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return f"{DOMAIN_BASE}{url}"
    return url

def _strip_gender_prefix(text: str) -> str:
    return re.sub(r"^\s*(Men['’]s|Women['’]s|Kids['’]?|Kid['’]s)\s+", "", text or "", flags=re.IGNORECASE).strip()

def _title_from_url(url: str) -> str:
    try:
        path = url.split("://", 1)[-1].split("/", 1)[-1]
        path = path.split("?", 1)[0]
        parts = [p for p in path.split("/") if p]
        slug = parts[-2] if parts and parts[-1].endswith(".html") and len(parts) >= 2 else (parts[-1] if parts else "")
        return re.sub(r"\s+", " ", slug.replace("-", " ").strip()).title()
    except Exception:
        return ""

def _sizes_from_data_attr(prod: BeautifulSoup) -> List[str]:
    raw = prod.get("data-all-sizes")
    if not raw:
        return []
    try:
        txt = html.unescape(raw)
        data = json.loads(txt) if txt.strip().startswith("{") else {}
        vals = [k for k in data.keys() if k in SIZE_SET]
        def _key(x: str):
            try: return (float(x), x)
            except: return (9999.0, x)
        return sorted(set(vals), key=_key)
    except Exception:
        return []

def _parse_price_text(tag: Optional[BeautifulSoup]) -> Optional[float]:
    if not tag:
        return None
    txt = tag.get_text(" ", strip=True)
    if not txt:
        return None
    m = re.search(r"[\d,]+(?:\.\d+)?", txt.replace("₱", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except Exception:
        return None

def _extract_prices_from_tile(prod: BeautifulSoup) -> (Optional[float], Optional[float]):
    sale = _parse_price_text(prod.find("span", class_="sales")) \
        or _parse_price_text(prod.select_one(".price-sales, .ProductPrice"))
    orig = _parse_price_text(prod.find("span", class_="original-price")) \
        or _parse_price_text(prod.select_one(".price-standard, .Price--compareAt"))
    return sale, orig

def _fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def _fetch_sizes_from_detail(product_url: str) -> List[str]:
    try:
        soup = BeautifulSoup(_fetch(product_url), "html.parser")
        sizes = set()
        containers = soup.select('[data-attribute-id="size"], .size, .product-size, .swatches.size, [data-attr="size"]') or [soup]
        for cont in containers:
            for t in cont.find_all(["button", "a", "label", "span", "option"]):
                val = (t.get("data-attr-value") or t.get("data-value") or t.get("value") or t.get_text(strip=True) or "").strip()
                if not val:
                    val = (t.get("aria-label") or t.get("title") or "").strip()
                if "/" in val or any(ch.isalpha() for ch in val):
                    continue
                if val in SIZE_SET:
                    sizes.add(val)
        return sorted(sizes, key=lambda x: (float(x), x))
    except Exception:
        return []


def _extract_image(prod: BeautifulSoup) -> str:
    img = prod.find("img", class_="tile-image")
    cand = None
    if img:
        for k in ("src", "data-src"):
            if img.get(k):
                cand = img.get(k).strip(); break
        if not cand:
            for k in ("srcset", "data-srcset"):
                srcset = img.get(k)
                if srcset:
                    parts = [p.strip().split()[0] for p in srcset.split(",") if p.strip()]
                    if parts:
                        cand = parts[-1]
                        break
    return _abs_asset(cand or "")

def _clean_title_from_tile(prod: BeautifulSoup, url: str) -> str:
    img = prod.find("img", class_="tile-image")
    if img:
        for k in ("title", "alt"):
            if img.get(k) and img.get(k).strip():
                return img.get(k).strip()
    ln = prod.find("a", class_="js-pdp-link")
    if ln:
        pg = ln.find("span", class_="product-group")
        if pg: pg.extract()
        t = _strip_gender_prefix(ln.get_text(" ", strip=True))
        if t: return t
    return _strip_gender_prefix(_title_from_url(url))


# --------------- main pieces ----------------

def _parse_listing(html_str: str, path: str) -> List[dict]:
    soup  = BeautifulSoup(html_str, "html.parser")
    tiles = soup.find_all("div", class_="product", attrs={"data-pid": True})
    cfg   = CATEGORY_CONFIG.get(path, {})
    out: List[dict] = []

    for prod in tiles:
        pid = prod.get("data-pid")
        if not pid:
            continue
        ln = prod.find("a", class_="js-pdp-link")
        href = ln["href"].strip() if ln and ln.has_attr("href") else ""
        url  = _abs_url(href)

        record = {
            "id":             pid,
            "title":          _clean_title_from_tile(prod, url),
            "subTitle":       cfg.get("subTitle"),
            "url":            url,
            "image":          _extract_image(prod),
            "gender":         cfg.get("gender", []),
            "age_group":      cfg.get("age_group", ""),
            "brand":          "hoka",
        }

        ps, po = _extract_prices_from_tile(prod)
        record["price_sale"]     = ps if ps is not None else 0.0
        record["price_original"] = (po if po is not None else (ps if ps is not None else 0.0))

        # sizes from tile; PDP fallback filled later for empties
        sizes = _sizes_from_data_attr(prod)
        record["extra"] = json.dumps(
            {"category": path.lstrip("/"), "sizes": sizes},
            ensure_ascii=False
        )

        out.append(record)
    return out


class HokaExtractor(BaseExtractor):
    def __init__(self, category: str = "all", num_pages: int = -1):
        self.category  = category
        self.num_pages = num_pages

    def _scrape_category(self, path: str) -> List[dict]:
        url = f"{BASE_URL}{path}/?sz={MAX_SZ}"
        logger.info(f"[Hoka] Fetch: {url}")
        try:
            html_str = _fetch(url)
            return _parse_listing(html_str, path)
        except Exception as e:
            logger.error(f"[Hoka] Failed {path}: {e}")
            return []

    def extract(self) -> List[HokaShoe]:
        paths    = PRODUCT_LISTS if self.category.lower() == "all" else [self.category]
        all_recs: List[dict] = []

        # fetch categories concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(self._scrape_category, p): p for p in paths}
            for fut in concurrent.futures.as_completed(futs):
                try:
                    all_recs.extend(fut.result() or [])
                except Exception as e:
                    logger.error(f"[Hoka] cat error: {e}")

        if not all_recs:
            return []

        # PDP size fallback for records with empty sizes
        needs_sizes = [r for r in all_recs if not json.loads(r.get("extra") or "{}").get("sizes")]
        if needs_sizes:
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
                futs = {ex.submit(_fetch_sizes_from_detail, r["url"]): i for i, r in enumerate(needs_sizes)}
                for fut in concurrent.futures.as_completed(futs):
                    idx = futs[fut]
                    try:
                        sz = fut.result() or []
                    except Exception:
                        sz = []
                    rec = needs_sizes[idx]
                    extra = json.loads(rec["extra"])
                    extra["sizes"] = [s for s in sz if s in SIZE_SET]
                    rec["extra"] = json.dumps(extra, ensure_ascii=False)

        return [HokaShoe(**r) for r in all_recs]
