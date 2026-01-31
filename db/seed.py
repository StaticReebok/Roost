"""Seed script: create DB and 30–50 synthetic user profiles for demo."""
import random
import sys
from pathlib import Path
from typing import Optional

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.session import init_db, SessionLocal
from db.models import Profile

VICTORIA_NEIGHBORHOODS = [
    "Burnside-Gorge", "Downtown", "Fairfield", "Fernwood", "Harris Green",
    "Hillside-Quadra", "James Bay", "North Park", "Oaklands", "Rockland", "Victoria West",
]
DISPLAY_NAMES = [
    "Alex", "Jordan", "Sam", "Casey", "Riley", "Morgan", "Quinn", "Avery",
    "Taylor", "Jamie", "Drew", "Reese", "Blake", "Cameron", "Finley", "Skyler",
    "Parker", "River", "Sage", "Charlie", "Dakota", "Emery", "Hayden", "Kai",
    "Logan", "Peyton", "Rowan", "Sawyer", "Sydney", "Reed", "Jesse", "Robin",
]


def monthly_savings_from_rent_and_rate(rent: float, rate_cad: Optional[float], rate_pct: Optional[float]) -> float:
    """Approximate monthly savings: if rate_cad use it; else rent * rate_pct/100."""
    if rate_cad is not None and rate_cad >= 0:
        return rate_cad
    if rate_pct is not None and rate_pct > 0:
        return rent * (rate_pct / 100)
    return max(0, rent * 0.15)  # default 15% of rent


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        count = db.query(Profile).count()
        if count >= 30:
            print(f"Already seeded ({count} profiles). Skip.")
            return
        to_create = 50 - count
        if to_create <= 0:
            return
        for _ in range(to_create):
            rent = random.uniform(1200, 2800)
            rate_pct = random.choice([None, None, 10, 15, 20, 25])
            rate_cad = random.choice([None, None, 200, 400, 600]) if rate_pct is None else None
            savings = monthly_savings_from_rent_and_rate(rent, rate_cad, rate_pct)
            commute = random.choice([15, 20, 25, 30, 35, 40, 45])
            household = random.choice([2, 3])
            budget_min = random.uniform(600, 1200)
            budget_max = random.uniform(1400, 2200)
            if budget_max < budget_min:
                budget_max = budget_min + 400
            p = Profile(
                display_name=random.choice(DISPLAY_NAMES),
                past_avg_rent=round(rent, 2),
                savings_rate_cad=rate_cad,
                savings_rate_pct=rate_pct,
                commute_tolerance_mins=commute,
                preferred_household_size=household,
                budget_min=round(budget_min, 2),
                budget_max=round(budget_max, 2),
                quiet_hours=random.choice([True, False]),
                pets_ok=random.choice([True, False]),
                smoking_ok=random.choice([True, False]),
                guests_ok=random.choice([True, False]),
                contact_email=f"demo{random.randint(1000, 9999)}@example.com",
                contact_phone="***-***-" + str(random.randint(1000, 9999)),
                neighborhood_preference=random.choice(VICTORIA_NEIGHBORHOODS),
                monthly_savings=round(savings, 2),
            )
            db.add(p)
        db.commit()
        print(f"Seeded {to_create} synthetic profiles. Total: {db.query(Profile).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
