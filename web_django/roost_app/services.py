"""
Bridge to core scoring, scraper, and Victoria. Uses existing roost.db via Django ORM.
"""
from roost_app.models import Profile, Swipe, Match

def _monthly_savings(profile):
    from core.scoring import monthly_savings_from_rent_and_rate
    return monthly_savings_from_rent_and_rate(
        profile.past_avg_rent, profile.savings_rate_cad, profile.savings_rate_pct
    )

def create_profile_from_form(cleaned):
    from roost_app.models import Profile
    p = Profile(
        display_name=cleaned.get('display_name') or None,
        past_avg_rent=float(cleaned['past_avg_rent']),
        savings_rate_cad=cleaned.get('savings_rate_cad'),
        savings_rate_pct=cleaned.get('savings_rate_pct'),
        commute_tolerance_mins=int(cleaned['commute_tolerance_mins']),
        preferred_household_size=int(cleaned['preferred_household_size']),
        budget_min=float(cleaned['budget_min']),
        budget_max=float(cleaned['budget_max']),
        quiet_hours=cleaned.get('quiet_hours'),
        pets_ok=cleaned.get('pets_ok'),
        smoking_ok=cleaned.get('smoking_ok'),
        guests_ok=cleaned.get('guests_ok'),
    )
    p.monthly_savings = _monthly_savings(p)
    p.save()
    return p

def ladder_snapshot_data(monthly_rent, monthly_savings, preferred_household_size=2, target_home_price=750000, current_savings=0):
    from core.scoring import compute_ladder_snapshot
    snap = compute_ladder_snapshot(
        monthly_rent=monthly_rent,
        monthly_savings=monthly_savings,
        preferred_household_size=preferred_household_size,
        target_home_price=target_home_price,
        current_savings=current_savings,
    )
    return {
        'years_solo': snap.years_solo,
        'years_with_1_roommate': snap.years_with_1_roommate,
        'years_with_2_roommates': snap.years_with_2_roommates,
        'improvement_range_months': snap.improvement_range_months,
        'assumptions': snap.assumptions,
    }

def get_match_cards(viewer_profile_id, skip=0, limit=10):
    from core.scoring import ladder_benefit_score, years_to_down_payment, hidden_costs_household, months_saved_vs_solo
    viewer = Profile.objects.filter(pk=viewer_profile_id).first()
    if not viewer:
        return []
    passed_ids = set(Swipe.objects.filter(viewer_profile_id=viewer_profile_id, action='pass').values_list('target_profile_id', flat=True))
    match_ids = set()
    for m in Match.objects.filter(profile_id_1=viewer_profile_id) | Match.objects.filter(profile_id_2=viewer_profile_id):
        match_ids.add(m.profile_id_1)
        match_ids.add(m.profile_id_2)
    match_ids.discard(viewer_profile_id)
    others = Profile.objects.exclude(pk=viewer_profile_id)
    if passed_ids:
        others = others.exclude(pk__in=passed_ids)
    cards = []
    for other in others:
        household = viewer.preferred_household_size or 2
        scenario_rent = (viewer.past_avg_rent + other.past_avg_rent) / 2
        rent_split = scenario_rent / household
        v_lifestyle = {'quiet_hours': viewer.quiet_hours, 'pets_ok': viewer.pets_ok, 'smoking_ok': viewer.smoking_ok, 'guests_ok': viewer.guests_ok}
        o_lifestyle = {'quiet_hours': other.quiet_hours, 'pets_ok': other.pets_ok, 'smoking_ok': other.smoking_ok, 'guests_ok': other.guests_ok}
        score, breakdown = ladder_benefit_score(
            viewer.past_avg_rent, viewer.monthly_savings or 0, viewer.commute_tolerance_mins or 30,
            viewer.budget_min or 0, viewer.budget_max or 3000, v_lifestyle,
            other.past_avg_rent, None, o_lifestyle,
            rent_split, household,
        )
        years_solo = years_to_down_payment(viewer.monthly_savings or 0, 0)
        hidden_solo_per = hidden_costs_household(1) / 1
        hidden_shared_per = hidden_costs_household(household) / household
        monthly_savings_shared = (viewer.monthly_savings or 0) + (viewer.past_avg_rent - rent_split) - (hidden_shared_per - hidden_solo_per)
        years_shared = years_to_down_payment(max(0.1, monthly_savings_shared), 0)
        months_saved = months_saved_vs_solo(years_solo, years_shared)
        chips = []
        if other.pets_ok:
            chips.append('Pets OK')
        if other.quiet_hours:
            chips.append('Quiet hours')
        if other.guests_ok:
            chips.append('Guests OK')
        why = [b['name'] + ': ' + str(b['value']) for b in breakdown[:3]]
        is_mutual = other.id in match_ids
        cards.append({
            'profile': other,
            'ladder_benefit_score': score,
            'breakdown': breakdown,
            'rent_split_min': rent_split * 0.9,
            'rent_split_max': rent_split * 1.1,
            'months_saved': months_saved,
            'compatibility_chips': chips,
            'why_this_match': why,
            'is_mutual_match': is_mutual,
        })
    cards.sort(key=lambda c: c['ladder_benefit_score'], reverse=True)
    return cards[skip:skip + limit]

def record_swipe(viewer_profile_id, target_profile_id, action):
    Swipe.objects.update_or_create(
        viewer_profile_id=viewer_profile_id,
        target_profile_id=target_profile_id,
        defaults={'action': action},
    )
    if action == 'like':
        other = Swipe.objects.filter(
            viewer_profile_id=target_profile_id,
            target_profile_id=viewer_profile_id,
            action='like',
        ).first()
        if other:
            id1, id2 = min(viewer_profile_id, target_profile_id), max(viewer_profile_id, target_profile_id)
            Match.objects.get_or_create(profile_id_1=id1, profile_id_2=id2)

def get_cmhc_zones():
    """CMHC Rental Market Survey Victoria 2025: average rents by zone (from Excel)."""
    from core.rmr_data import get_rmr_zones
    raw = get_rmr_zones()
    return [
        {
            "zone": z["zone"],
            "studio": z.get("studio"),
            "onebed": z.get("1bed"),
            "twobed": z.get("2bed"),
            "threebed": z.get("3bed"),
            "total": z.get("total"),
        }
        for z in raw
    ]

def reality_check_data(monthly_rent=2000, commute_mins=30):
    from core.scoring import all_in_monthly_cost, commute_cost_per_month, income_needed_to_qualify
    from core.constants import (
        DEFAULT_TARGET_HOME_PRICE_CAD,
        DOWN_PAYMENT_PCT,
        VICTORIA_AVG_2BED_RENT_CAD,
        INCOME_NEEDED_TO_QUALIFY_CAD,
    )
    all_in = all_in_monthly_cost(monthly_rent, 1)
    commute_cost = commute_cost_per_month(commute_mins)
    income_needed = income_needed_to_qualify(DEFAULT_TARGET_HOME_PRICE_CAD, DOWN_PAYMENT_PCT)
    return {
        'all_in_monthly_cost_solo': all_in,
        'commute_cost_per_month': commute_cost,
        'victoria_avg_2bed_rent': VICTORIA_AVG_2BED_RENT_CAD,
        'income_needed_to_qualify_typical': INCOME_NEEDED_TO_QUALIFY_CAD,
        'down_payment_10_pct_750k': DEFAULT_TARGET_HOME_PRICE_CAD * DOWN_PAYMENT_PCT,
        'note_city_vs_greater_victoria': 'Roost focuses on the City of Victoria boundary. Greater Victoria (Saanich, Oak Bay, Esquimalt, etc.) may have different rent and commute tradeoffs.',
    }


