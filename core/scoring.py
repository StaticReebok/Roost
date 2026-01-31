"""
ROOST SCORING ENGINE — based on project scoring.py.
Focus: Cashflow Velocity, Affordability Gradients, and Lifestyle Flags.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.constants import (
    COMMUTE_TIME_COST_CAD_PER_MIN,
    DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD,
    DEFAULT_TARGET_HOME_PRICE_CAD,
    MAX_YEARS,
    TENANT_INSURANCE_PER_PERSON_CAD,
    UTILITIES_ESTIMATE_PER_PERSON_2_SHARED,
    UTILITIES_ESTIMATE_PER_PERSON_3_SHARED,
    UTILITIES_ESTIMATE_PER_PERSON_UNSHARED,
    WEIGHT_BUDGET,
    WEIGHT_COMMUTE,
    WEIGHT_SAVINGS,
)

# --- PART 1: HELPERS ---


def get_all_in_cost(rent_total: float, household_size: int) -> float:
    """
    Standardizes how we calculate the 'All-in' price tag (Rent + Utils + Insurance) per person.
    """
    if household_size == 1:
        utils = UTILITIES_ESTIMATE_PER_PERSON_UNSHARED
    elif household_size == 2:
        utils = UTILITIES_ESTIMATE_PER_PERSON_2_SHARED
    else:
        utils = UTILITIES_ESTIMATE_PER_PERSON_3_SHARED
    return (rent_total / household_size) + utils + TENANT_INSURANCE_PER_PERSON_CAD


def calculate_years_to_buy(monthly_savings: float, current_savings: float = 0) -> float:
    """Calculates time to reach target down payment (fixed from constants)."""
    if monthly_savings <= 0:
        return 99.9
    target_down_payment = DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD
    remaining_needed = max(0, target_down_payment - current_savings)
    if remaining_needed == 0:
        return 0.0
    months_needed = remaining_needed / monthly_savings
    return round(months_needed / 12, 1)


def commute_cost_per_month(commute_mins_one_way: float, round_trips_per_week: int = 5) -> float:
    """Calculates the 'Time Cost' of commuting in dollars."""
    return commute_mins_one_way * 2 * round_trips_per_week * 4.33 * COMMUTE_TIME_COST_CAD_PER_MIN


# --- PART 2: CASHFLOW / LADDER SNAPSHOT ---


def compute_cashflow(
    solo_rent: float,
    shared_rent_total: float,
    household_size: int,
    current_savings: float,
    monthly_income: float,
) -> Dict[str, Any]:
    """
    Compares Solo vs. Roost life using the unified helper.
    """
    solo_expenses = get_all_in_cost(solo_rent, 1)
    shared_expenses = get_all_in_cost(shared_rent_total, household_size)
    solo_monthly_savings = monthly_income - solo_expenses
    shared_monthly_savings = monthly_income - shared_expenses
    years_solo = calculate_years_to_buy(solo_monthly_savings, current_savings)
    years_shared = calculate_years_to_buy(shared_monthly_savings, current_savings)
    return {
        "scenario": f"Sharing with {household_size - 1} Roommates",
        "solo_cost": int(solo_expenses),
        "shared_cost": int(shared_expenses),
        "monthly_cash_freed": int(shared_monthly_savings - solo_monthly_savings),
        "solo_savings_rate": int(solo_monthly_savings),
        "shared_savings_rate": int(shared_monthly_savings),
        "years_solo": years_solo,
        "years_shared": years_shared,
        "years_saved": round(max(0, years_solo - years_shared), 1),
    }


# --- PART 3: MATCHMAKER (SCORING) ---


def calculate_match_score(
    my_current_solo_rent: float,
    match_total_rent: float,
    household_size: int,
    my_budget: float,
    commute_mins: int,
    my_prefs: Dict[str, Any],
    candidate_traits: Dict[str, Any],
) -> Tuple[int, List[Dict[str, Any]], List[str]]:
    factors = []
    flags = []
    current_solo_all_in = get_all_in_cost(my_current_solo_rent, 1)
    potential_shared_all_in = get_all_in_cost(match_total_rent, household_size)
    true_monthly_savings = current_solo_all_in - (
        potential_shared_all_in + (commute_mins * 0.5)
    )
    savings_score = min(100, (true_monthly_savings / 500) * 100)
    factors.append({
        "name": "Savings Rate",
        "value": f"+${int(true_monthly_savings)}/mo",
        "score": int(max(0, savings_score)),
        "weight": WEIGHT_SAVINGS,
    })
    rent_per_person = match_total_rent / household_size
    budget_delta = my_budget - rent_per_person
    if budget_delta >= 400:
        budget_score, budget_text = 100, "Well Under Budget"
    elif budget_delta >= 0:
        budget_score = 100 - ((400 - budget_delta) / 20)
        budget_text = "Within Budget"
    else:
        budget_score = max(0, 80 - (abs(budget_delta) / 10))
        budget_text = f"${int(abs(budget_delta))} Over Budget"
    factors.append({
        "name": "Affordability",
        "value": budget_text,
        "score": int(budget_score),
        "weight": WEIGHT_BUDGET,
    })
    if commute_mins <= 15:
        commute_score = 100
    elif commute_mins <= 30:
        commute_score = 75
    elif commute_mins <= 45:
        commute_score = 50
    elif commute_mins <= 60:
        commute_score = 25
    else:
        commute_score = 0
    factors.append({
        "name": "Commute",
        "value": f"{commute_mins} mins",
        "score": commute_score,
        "weight": WEIGHT_COMMUTE,
    })
    is_compatible, conflicts = check_lifestyle_compatibility(my_prefs, candidate_traits)
    for conflict in conflicts:
        flags.append(f"Lifestyle Mismatch: {conflict}")
    total_weight = WEIGHT_SAVINGS + WEIGHT_BUDGET + WEIGHT_COMMUTE
    weighted_sum = (
        (savings_score * WEIGHT_SAVINGS)
        + (budget_score * WEIGHT_BUDGET)
        + (commute_score * WEIGHT_COMMUTE)
    )
    final_score = weighted_sum / total_weight if total_weight > 0 else 0
    return int(final_score), factors, flags


# --- PART 4: COMPATIBILITY ---


def check_lifestyle_compatibility(
    my_prefs: Dict[str, Any], candidate_traits: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    conflicts = []
    if my_prefs.get("no_smoking") and candidate_traits.get("smokes"):
        conflicts.append("Smoker")
    if my_prefs.get("no_pets") and candidate_traits.get("has_pets"):
        conflicts.append("Has Pets")
    return len(conflicts) == 0, conflicts


# --- COMPATIBILITY WRAPPERS (for Django + backend_api) ---


def monthly_savings_from_rent_and_rate(
    rent: float,
    rate_cad: Optional[float],
    rate_pct: Optional[float],
) -> float:
    """Approximate monthly savings: rate_cad if set, else rent * rate_pct/100, else 15% of rent."""
    if rate_cad is not None and rate_cad >= 0:
        return rate_cad
    if rate_pct is not None and rate_pct > 0:
        return rent * (rate_pct / 100)
    return max(0, rent * 0.15)


def years_to_down_payment(
    monthly_savings: float,
    current_savings: float = 0.0,
    target_home_price: Optional[float] = None,
    down_payment_pct: Optional[float] = None,
) -> float:
    """Wrapper: uses fixed target down payment from constants."""
    return calculate_years_to_buy(monthly_savings, current_savings)


def hidden_costs_household(num_people: int) -> float:
    """Monthly hidden costs for household: (utils per person + insurance) * num_people."""
    if num_people == 1:
        utils = UTILITIES_ESTIMATE_PER_PERSON_UNSHARED
    elif num_people == 2:
        utils = UTILITIES_ESTIMATE_PER_PERSON_2_SHARED
    else:
        utils = UTILITIES_ESTIMATE_PER_PERSON_3_SHARED
    return num_people * (utils + TENANT_INSURANCE_PER_PERSON_CAD)


@dataclass
class LadderSnapshot:
    """Result of onboarding: years solo, improvement range with roommates."""

    years_solo: float
    years_with_1_roommate: Optional[float]
    years_with_2_roommates: Optional[float]
    improvement_range_months: Optional[tuple]
    assumptions: Dict[str, Any]


def compute_ladder_snapshot(
    monthly_rent: float,
    monthly_savings: float,
    preferred_household_size: int = 2,
    target_home_price: float = DEFAULT_TARGET_HOME_PRICE_CAD,
    current_savings: float = 0.0,
) -> LadderSnapshot:
    """
    Build from get_all_in_cost and calculate_years_to_buy.
    Implied income = solo_all_in + monthly_savings; then years shared from shared savings.
    """
    years_solo = calculate_years_to_buy(monthly_savings, current_savings)
    solo_all_in = get_all_in_cost(monthly_rent, 1)
    implied_income = solo_all_in + monthly_savings
    years_2 = years_3 = MAX_YEARS
    if preferred_household_size >= 2:
        shared_rent_2 = monthly_rent  # same total rent, split
        shared_cost_2 = get_all_in_cost(shared_rent_2, 2)
        shared_savings_2 = implied_income - shared_cost_2
        years_2 = calculate_years_to_buy(max(0.1, shared_savings_2), current_savings)
    if preferred_household_size >= 3:
        shared_rent_3 = monthly_rent
        shared_cost_3 = get_all_in_cost(shared_rent_3, 3)
        shared_savings_3 = implied_income - shared_cost_3
        years_3 = calculate_years_to_buy(max(0.1, shared_savings_3), current_savings)
    months_saved_min = max(0, (years_solo - years_3) * 12) if years_3 < years_solo else 0
    months_saved_max = max(0, (years_solo - years_2) * 12) if years_2 < years_solo else 0
    if months_saved_min > months_saved_max:
        months_saved_min, months_saved_max = months_saved_max, months_saved_min
    return LadderSnapshot(
        years_solo=years_solo,
        years_with_1_roommate=years_2 if preferred_household_size >= 2 else None,
        years_with_2_roommates=years_3 if preferred_household_size >= 3 else None,
        improvement_range_months=(months_saved_min, months_saved_max),
        assumptions={
            "target_home_price": target_home_price,
            "down_payment_target": DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD,
            "current_savings": current_savings,
        },
    )


def ladder_benefit_score(
    viewer_rent: float,
    viewer_savings: float,
    viewer_commute_max_mins: int,
    viewer_budget_min: float,
    viewer_budget_max: float,
    viewer_lifestyle: Dict[str, bool],
    other_rent: float,
    other_commute_mins: Optional[int],
    other_lifestyle: Dict[str, bool],
    scenario_rent_split: float,
    scenario_household_size: int,
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Adapter: call calculate_match_score and convert factors to breakdown (name, value, contribution, weight, weighted).
    """
    match_total_rent = scenario_rent_split * scenario_household_size
    my_budget = (viewer_budget_min + viewer_budget_max) / 2 if viewer_budget_max > viewer_budget_min else viewer_budget_max
    commute_mins = other_commute_mins if other_commute_mins is not None else 30
    my_prefs = {
        "no_smoking": not viewer_lifestyle.get("smoking_ok", True),
        "no_pets": not viewer_lifestyle.get("pets_ok", True),
    }
    candidate_traits = {
        "smokes": bool(other_lifestyle.get("smoking_ok", False)),
        "has_pets": bool(other_lifestyle.get("pets_ok", False)),
    }
    score, factors, _flags = calculate_match_score(
        viewer_rent, match_total_rent, scenario_household_size,
        my_budget, commute_mins, my_prefs, candidate_traits,
    )
    breakdown = []
    for f in factors:
        contrib = f.get("score", 0)
        w = f.get("weight", 0)
        breakdown.append({
            "name": f["name"],
            "value": f["value"],
            "contribution": contrib,
            "weight": w,
            "weighted": round(contrib * w, 1),
        })
    return float(score), breakdown


def months_saved_vs_solo(years_solo: float, years_shared: float) -> float:
    """Months saved on timeline when sharing vs solo."""
    return max(0, (years_solo - years_shared) * 12)


def all_in_monthly_cost(rent: float, num_people: int = 1) -> float:
    """All-in monthly cost per person (compat name for get_all_in_cost)."""
    return get_all_in_cost(rent, num_people)


def income_needed_to_qualify(
    target_home_price: float,
    down_payment_pct: Optional[float] = None,
    gds_ratio: float = 0.39,
) -> float:
    """Rough income needed to qualify for mortgage (stress-tested). Stub using target price."""
    from core.constants import DOWN_PAYMENT_PCT
    pct = down_payment_pct if down_payment_pct is not None else DOWN_PAYMENT_PCT
    down = target_home_price * pct
    principal = target_home_price - down
    if principal <= 0:
        return 0.0
    r = 0.05 / 12
    n = 25 * 12
    monthly_payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    annual_debt = monthly_payment * 12
    return annual_debt / gds_ratio


def years_to_down_payment_with_rent_growth(
    initial_monthly_savings: float,
    initial_rent: float,
    rent_growth_annual: float,
    current_savings: float,
    target_home_price: float,
    down_payment_pct: float = 0.10,
    max_years: int = 50,
) -> float:
    """Years to down payment if rent grows annually (simplified)."""
    from core.constants import DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD
    target_dp = DEFAULT_TARGET_HOME_DOWNPAYMENT_CAD
    remaining = max(0.0, target_dp - current_savings)
    if remaining <= 0:
        return 0.0
    total = current_savings
    for year in range(1, max_years + 1):
        rent_t = initial_rent * ((1 + rent_growth_annual) ** year)
        savings_monthly = initial_monthly_savings - (rent_t - initial_rent)
        if savings_monthly <= 0:
            return float(MAX_YEARS)
        total += savings_monthly * 12
        if total >= target_dp:
            return min(MAX_YEARS, float(year))
    return MAX_YEARS
