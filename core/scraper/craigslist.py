"""Lightweight Craigslist Victoria apartment scraper; cached; Victoria-only."""
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from core.constants import LISTINGS_CACHE_TTL
from core.scraper.cache import get_cached_listings, set_cached_listings
from core.scraper.geocode import geocode_place
from core.victoria import VICTORIA_NEIGHBORHOODS, in_victoria_boundary, normalize_neighborhood

CRAIGSLIST_BASE = "https://victoria.craigslist.org"
SEARCH_URL = "https://victoria.craigslist.org/search/apa"
USER_AGENT = "Roost/1.0 (Victoria co-housing; educational)"


def _extract_rent(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"\$?\s*(\d{3,5})\s*(?:/?\s*mo|month)?", str(text), re.I)
    if m:
        return float(m.group(1))
    return None


def _extract_beds(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d)\s*br|(\d)\s*bed|bedroom\s*(\d)", str(text), re.I)
    if m:
        return int(m.group(1) or m.group(2) or m.group(3))
    return None


def _parse_listing_row(row, base_url: str) -> Optional[Dict[str, Any]]:
    """Parse one listing row from search results."""
    try:
        link_el = row.find("a", class_=re.compile(r"posting-title|result-title"))
        if not link_el:
            return None
        href = link_el.get("href", "")
        if not href.startswith("http"):
            href = base_url.rstrip("/") + href if href.startswith("/") else base_url + "/" + href
        title = (link_el.get_text() or "").strip()
        price_el = row.find("span", class_=re.compile(r"price|result-price"))
        rent = _extract_rent(price_el.get_text() if price_el else title) if price_el or title else None
        if not rent or rent < 500 or rent > 15000:
            return None
        # Housing attributes (beds, etc.)
        housing = row.find("span", class_=re.compile(r"housing|bed"))
        beds = _extract_beds(housing.get_text() if housing else "") or _extract_beds(title)
        location_el = row.find("span", class_=re.compile(r"result-hood|location"))
        location = (location_el.get_text() or "").strip().strip("()") if location_el else ""
        # Posting date
        time_el = row.find("time") or row.find("span", class_=re.compile(r"date"))
        posted = (time_el.get("datetime") or (time_el.get_text() if time_el else ""))[:50] if time_el else ""
        return {
            "url": href,
            "title": title[:200],
            "rent": rent,
            "beds": beds or 1,
            "location_raw": location[:100],
            "posted": posted,
            "utilities_included": "util" in (title + " " + location).lower() or "incl" in (title + " " + location).lower(),
        }
    except Exception:
        return None


def _fetch_search_page(session: httpx.Client, max_listings: int = 50) -> List[Dict[str, Any]]:
    """Fetch one or more search pages (lightweight)."""
    results: List[Dict[str, Any]] = []
    start = 0
    while len(results) < max_listings:
        params = {"s": start} if start else {}
        try:
            r = session.get(SEARCH_URL, params=params, timeout=15)
            r.raise_for_status()
        except Exception:
            break
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("li.result-row, .cl-static-search-result")
        if not rows:
            rows = soup.find_all("li", class_=re.compile(r"result"))
        for row in rows:
            if len(results) >= max_listings:
                break
            parsed = _parse_listing_row(row, CRAIGSLIST_BASE)
            if parsed:
                results.append(parsed)
        if len(rows) < 25:
            break
        start += 25
        time.sleep(0.5)
    return results


def scrape_and_geocode(max_listings: int = 50, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Return Victoria-only listings. Uses cache if fresh; otherwise scrapes, geocodes, filters.
    Never stores exact address; only neighborhood + approximate pin.
    """
    if use_cache:
        cached = get_cached_listings(ttl_seconds=LISTINGS_CACHE_TTL)
        if cached:
            return cached[:max_listings]

    with httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as session:
        raw = _fetch_search_page(session, max_listings=max_listings)

    out: List[Dict[str, Any]] = []
    for item in raw:
        loc_str = (item.get("location_raw") or item.get("title") or "").strip()
        if not loc_str:
            loc_str = "Victoria, BC"
        lat, lon, neighborhood = geocode_place(loc_str)
        if lat is None and neighborhood:
            lat, lon = 48.4284, -123.3656
        if lat is not None and lon is not None and not in_victoria_boundary(lat, lon):
            continue
        item["lat"] = lat
        item["lon"] = lon
        item["neighborhood"] = neighborhood or normalize_neighborhood(loc_str) or "Victoria"
        if item["neighborhood"] not in VICTORIA_NEIGHBORHOODS:
            item["neighborhood"] = "Victoria"
        # Sanitize: no exact address
        item.pop("location_raw", None)
        out.append(item)
        if len(out) >= max_listings:
            break

    if out:
        set_cached_listings(out)
    return out


def get_listings(max_listings: int = 50, use_cache: bool = True) -> List[Dict[str, Any]]:
    """Public API: get Victoria-only listings (cached when possible)."""
    return scrape_and_geocode(max_listings=max_listings, use_cache=use_cache)
