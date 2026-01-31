"""City of Victoria boundary and neighborhoods (Victoria, BC, Canada)."""
from typing import List, Optional, Tuple

# City of Victoria approximate bounding box (lat/lon)
# Conservative box covering City of Victoria (not Greater Victoria)
VICTORIA_LAT_MIN = 48.40
VICTORIA_LAT_MAX = 48.46
VICTORIA_LON_MIN = -123.42
VICTORIA_LON_MAX = -123.32

# Victoria neighborhoods (City of Victoria only)
VICTORIA_NEIGHBORHOODS: List[str] = [
    "Burnside-Gorge",
    "Downtown",
    "Fairfield",
    "Fernwood",
    "Harris Green",
    "Hillside-Quadra",
    "James Bay",
    "North Park",
    "Oaklands",
    "Rockland",
    "Victoria West",
]


def in_victoria_boundary(lat: float, lon: float) -> bool:
    """Return True if (lat, lon) is inside City of Victoria bounding box."""
    return (
        VICTORIA_LAT_MIN <= lat <= VICTORIA_LAT_MAX
        and VICTORIA_LON_MIN <= lon <= VICTORIA_LON_MAX
    )


def normalize_neighborhood(name: Optional[str]) -> Optional[str]:
    """Normalize neighborhood string to a known Victoria neighborhood or None."""
    if not name or not isinstance(name, str):
        return None
    cleaned = name.strip()
    if not cleaned:
        return None
    for n in VICTORIA_NEIGHBORHOODS:
        if n.lower() in cleaned.lower() or cleaned.lower() in n.lower():
            return n
    # Try common variants
    variants = {
        "downtown victoria": "Downtown",
        "james bay": "James Bay",
        "fairfield": "Fairfield",
        "fernwood": "Fernwood",
        "rockland": "Rockland",
        "oaklands": "Oaklands",
        "north park": "North Park",
        "burnside": "Burnside-Gorge",
        "gorge": "Burnside-Gorge",
        "quadra": "Hillside-Quadra",
        "hillside": "Hillside-Quadra",
        "harris green": "Harris Green",
        "vic west": "Victoria West",
        "victoria west": "Victoria West",
    }
    return variants.get(cleaned.lower()) or None


def get_bounds() -> Tuple[float, float, float, float]:
    """Return (lat_min, lat_max, lon_min, lon_max) for Victoria."""
    return (VICTORIA_LAT_MIN, VICTORIA_LAT_MAX, VICTORIA_LON_MIN, VICTORIA_LON_MAX)
