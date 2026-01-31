from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from roost_app.forms import OnboardingForm
from roost_app.models import Profile
from roost_app import services


def home(request):
    return render(request, 'roost_app/home.html')


def onboarding(request):
    if request.method == 'POST':
        form = OnboardingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['savings_rate_cad'] = data.get('savings_cad') if data.get('savings_type') == 'cad' else None
            data['savings_rate_pct'] = data.get('savings_pct') if data.get('savings_type') == 'pct' else None
            profile = services.create_profile_from_form(data)
            monthly_savings = data['savings_rate_cad'] or (data['past_avg_rent'] * (data['savings_rate_pct'] or 0) / 100)
            snap = services.ladder_snapshot_data(
                monthly_rent=data['past_avg_rent'],
                monthly_savings=monthly_savings,
                preferred_household_size=data['preferred_household_size'],
            )
            request.session['profile_id'] = profile.id
            return render(request, 'roost_app/onboarding_result.html', {
                'profile': profile,
                'snap': snap,
            })
    else:
        form = OnboardingForm()
    return render(request, 'roost_app/onboarding.html', {'form': form})


def matches(request):
    profile_id = request.session.get('profile_id')
    if profile_id is None:
        profile_id = 1  # Demo: use profile 1 so matches load automatically (seeded data)
        request.session['profile_id'] = profile_id
    return render(request, 'roost_app/matches.html', {'profile_id': profile_id})


def matches_list_partial(request):
    profile_id = request.GET.get('profile_id') or request.session.get('profile_id')
    if not profile_id:
        return render(request, 'roost_app/partials/match_cards.html', {'cards': [], 'profile_id': None})
    try:
        profile_id = int(profile_id)
    except (TypeError, ValueError):
        return render(request, 'roost_app/partials/match_cards.html', {'cards': [], 'profile_id': None})
    cards = services.get_match_cards(profile_id, skip=0, limit=10)
    return render(request, 'roost_app/partials/match_cards.html', {'cards': cards, 'profile_id': profile_id})


@require_POST
def swipe(request):
    from django.http import HttpResponseBadRequest
    try:
        viewer_id = int(request.POST.get('viewer_profile_id'))
        target_id = int(request.POST.get('target_profile_id'))
        action = request.POST.get('action', 'pass')
    except (TypeError, ValueError):
        return HttpResponseBadRequest('Invalid params')
    if action not in ('like', 'pass'):
        return HttpResponseBadRequest('Invalid action')
    services.record_swipe(viewer_id, target_id, action)
    cards = services.get_match_cards(viewer_id, skip=0, limit=10)
    return render(request, 'roost_app/partials/match_cards.html', {'cards': cards, 'profile_id': viewer_id})


def reality_check(request):
    return render(request, 'roost_app/reality_check.html')


def reality_check_partial(request):
    try:
        monthly_rent = float(request.GET.get('monthly_rent', 2000))
        commute_mins = int(request.GET.get('commute_mins', 30))
    except (TypeError, ValueError):
        monthly_rent, commute_mins = 2000, 30
    data = services.reality_check_data(monthly_rent, commute_mins)
    return render(request, 'roost_app/partials/reality_check_result.html', data)


def insights(request):
    zones = services.get_cmhc_zones()
    return render(request, 'roost_app/insights.html', {'zones': zones})
