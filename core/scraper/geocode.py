"""Geocode addresses to lat/lon (Google or fallback). Victoria boundary check."""
from typing import Optional, Tuple

import httpx

from core.config import GOOGLE_MAPS_API_KEY, USE_GOOGLE_MAPS
from core.victoria import in_victoria_boundary, normalize_neighborhood
from core.scraper.cache import get_cached_geocode, set_cached_geocode


def geocode_place(place: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Geocode place string to (lat, lon, neighborhood).
    Uses Google Geocoding if key set, else returns None and neighborhood from text.
    Checks Victoria boundary; if outside, returns (None, None, None).
    """
    if not place or not place.strip():
        return None, None, None
    place = place.strip()
    cached = get_cached_geocode(place)
    if cached is not None:
        lat, lon = cached.get("lat"), cached.get("lon")
        if lat is not None and lon is not None and in_victoria_boundary(lat, lon):
            return lat, lon, cached.get("neighborhood")
        if lat is not None and lon is not None:
            return None, None, None  # outside Victoria
        return None, None, None

    if USE_GOOGLE_MAPS and GOOGLE_MAPS_API_KEY:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            r = httpx.get(url, params={"address": f"{place}, Victoria, BC, Canada", "key": GOOGLE_MAPS_API_KEY}, timeout=10)
            data = r.json()
            if data.get("status") == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                lat, lon = loc["lat"], loc["lng"]
                if not in_victoria_boundary(lat, lon):
                    set_cached_geocode(place, {"lat": lat, "lon": lon, "neighborhood": None})
                    return None, None, None
                # Try to get neighborhood from address_components
                neighborhood = None
                for comp in data["results"][0].get("address_components", []):
                    if "neighborhood" in comp.get("types", []):
                        neighborhood = comp.get("long_name") or comp.get("short_name")
                        break
                neighborhood = normalize_neighborhood(neighborhood) or normalize_neighborhood(place)
                out = {"lat": lat, "lon": lon, "neighborhood": neighborhood}
                set_cached_geocode(place, out)
                return lat, lon, neighborhood
        except Exception:
            pass
    # Fallback: no API; try to infer neighborhood from text only (no lat/lon)
    neighborhood = normalize_neighborhood(place)
    if neighborhood:
        # Use centroid of Victoria for display (approximate)
        lat, lon = 48.4284, -123.3656
        return lat, lon, neighborhood
    return None, None, None
