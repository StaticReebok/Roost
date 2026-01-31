"""Roost assumptions and constants (visible in UI). Based on project constants.py."""
from typing import Final

# Down payment model
DEFAULT_TARGET_HOME_PRICE_CAD: Final[float] = 1_316_700.0
DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD: Final[float] = 156_670.0
DOWN_PAYMENT_PCT: Final[float] = DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD / DEFAULT_TARGET_HOME_PRICE_CAD  # compat

# Victoria / Greater Victoria context (CMHC / local data; cite in UI)
VICTORIA_AVG_2BED_RENT_CAD: Final[float] = 2_120.0
VICTORIA_AVG_3BED_RENT_CAD: Final[float] = 2886.0

# Rent growth (for predictive scenarios; annual rate)
DEFAULT_RENT_GROWTH_ANNUAL: Final[float] = 0.03  # 3% per year
OPTIMISTIC_RENT_GROWTH: Final[float] = 0.0  # compat
PESSIMISTIC_RENT_GROWTH: Final[float] = 0.05  # compat

# Hidden costs (monthly, CAD) — per person by household size
UTILITIES_ESTIMATE_PER_PERSON_UNSHARED: Final[float] = 104.86
UTILITIES_ESTIMATE_PER_PERSON_2_SHARED: Final[float] = 74.78
UTILITIES_ESTIMATE_PER_PERSON_3_SHARED: Final[float] = 64.75
TENANT_INSURANCE_PER_PERSON_CAD: Final[float] = 30.0

# Time-cost proxy (CAD per minute one-way commute, rough)
COMMUTE_TIME_COST_CAD_PER_MIN: Final[float] = 0.50

# Ladder Benefit Score weights (sum to 1.0)
WEIGHT_SAVINGS: Final[float] = 0.50
WEIGHT_BUDGET: Final[float] = 0.35
WEIGHT_COMMUTE: Final[float] = 0.15

# Safe bounds for years-to-down-payment
MIN_YEARS: Final[float] = 0.0
MAX_YEARS: Final[float] = 50.0

# Backward compat / other
INCOME_NEEDED_TO_QUALIFY_CAD: Final[float] = 200_000.0  # typical mortgage qual placeholder
LISTINGS_CACHE_TTL: Final[int] = 3600  # 1 hour (craigslist)
