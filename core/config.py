"""Roost configuration: env, API base URLs, paths."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "roost.db"
CACHE_DIR = PROJECT_ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# Google Maps (optional)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
USE_GOOGLE_MAPS = bool(GOOGLE_MAPS_API_KEY)

# API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Craigslist
CRAIGSLIST_VICTORIA_APT = "https://victoria.craigslist.org/search/apa"
