"""Simple file-based cache for API and scrape results."""
import json
import time
from pathlib import Path
from typing import Any, Optional

from core.config import CACHE_DIR

CACHE_FILE = CACHE_DIR / "listings_cache.json"
CACHE_META = CACHE_DIR / "listings_cache_meta.json"


def _read_meta() -> dict:
    if not CACHE_META.exists():
        return {}
    try:
        return json.loads(CACHE_META.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_meta(meta: dict) -> None:
    CACHE_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def get_cached_listings(ttl_seconds: int = 3600) -> Optional[list]:
    """Return cached listings if fresh, else None."""
    meta = _read_meta()
    ts = meta.get("timestamp", 0)
    if time.time() - ts > ttl_seconds:
        return None
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def set_cached_listings(data: list) -> None:
    """Write listings to cache with current timestamp."""
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_meta({"timestamp": time.time()})


def get_cached_geocode(key: str, ttl_seconds: int = 86400 * 7) -> Optional[dict]:
    """Key = normalized address or place string."""
    path = CACHE_DIR / "geocode"
    path.mkdir(exist_ok=True)
    # Simple file per key (sanitize key for filename)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:100]
    f = path / f"{safe}.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("_ts", 0) + ttl_seconds < time.time():
            return None
        return data
    except Exception:
        return None


def set_cached_geocode(key: str, data: dict) -> None:
    path = CACHE_DIR / "geocode"
    path.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:100]
    data["_ts"] = time.time()
    (path / f"{safe}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
