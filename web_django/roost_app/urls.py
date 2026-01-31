from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('onboarding/', views.onboarding, name='onboarding'),
    path('matches/', views.matches, name='matches'),
    path('matches/partial/', views.matches_list_partial, name='matches_partial'),
    path('swipe/', views.swipe, name='swipe'),
    path('reality-check/', views.reality_check, name='reality_check'),
    path('reality-check/partial/', views.reality_check_partial, name='reality_check_partial'),
    path('insights/', views.insights, name='insights'),
]
