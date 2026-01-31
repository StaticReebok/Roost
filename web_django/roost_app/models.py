"""
Unmanaged Django models mirroring existing roost.db (SQLAlchemy) schema.
Do not run migrations; these tables already exist.
"""
from django.db import models


class Profile(models.Model):
    """Maps to existing profiles table."""
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    display_name = models.CharField(max_length=100, null=True, blank=True)
    past_avg_rent = models.FloatField(default=0.0)
    savings_rate_cad = models.FloatField(null=True, blank=True)
    savings_rate_pct = models.FloatField(null=True, blank=True)
    commute_tolerance_mins = models.IntegerField(default=30)
    preferred_household_size = models.IntegerField(default=2)
    budget_min = models.FloatField(default=0.0)
    budget_max = models.FloatField(default=3000.0)
    quiet_hours = models.BooleanField(null=True, blank=True)
    pets_ok = models.BooleanField(null=True, blank=True)
    smoking_ok = models.BooleanField(null=True, blank=True)
    guests_ok = models.BooleanField(null=True, blank=True)
    contact_email = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    contact_social = models.CharField(max_length=255, null=True, blank=True)
    commute_destination = models.CharField(max_length=255, null=True, blank=True)
    neighborhood_preference = models.CharField(max_length=100, null=True, blank=True)
    monthly_savings = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'profiles'


class Swipe(models.Model):
    """Maps to existing swipes table."""
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    viewer_profile_id = models.IntegerField()
    target_profile_id = models.IntegerField()
    action = models.CharField(max_length=10)  # 'like' | 'pass'

    class Meta:
        managed = False
        db_table = 'swipes'
        unique_together = [['viewer_profile_id', 'target_profile_id']]


class Match(models.Model):
    """Maps to existing matches table."""
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    profile_id_1 = models.IntegerField()
    profile_id_2 = models.IntegerField()
    attached_listing_json = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'matches'
