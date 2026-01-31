from django import forms

class OnboardingForm(forms.Form):
    past_avg_rent = forms.FloatField(min_value=800, max_value=5000, initial=1800, widget=forms.NumberInput(attrs={'class': 'input', 'step': '50'}))
    savings_type = forms.ChoiceField(choices=[('cad', 'Monthly (CAD)'), ('pct', '% of rent')], initial='cad', widget=forms.RadioSelect())
    savings_cad = forms.FloatField(required=False, min_value=0, max_value=3000, initial=300, widget=forms.NumberInput(attrs={'class': 'input', 'step': '50'}))
    savings_pct = forms.FloatField(required=False, min_value=5, max_value=50, initial=15, widget=forms.NumberInput(attrs={'class': 'input'}))
    commute_tolerance_mins = forms.IntegerField(min_value=10, max_value=60, initial=30, widget=forms.NumberInput(attrs={'class': 'input'}))
    preferred_household_size = forms.TypedChoiceField(choices=[(2, '2 people'), (3, '3 people')], coerce=int, initial=2, widget=forms.Select(attrs={'class': 'input'}))
    budget_min = forms.FloatField(min_value=0, initial=800, widget=forms.NumberInput(attrs={'class': 'input'}))
    budget_max = forms.FloatField(min_value=0, initial=1600, widget=forms.NumberInput(attrs={'class': 'input'}))
    quiet_hours = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-roost-600'}))
    pets_ok = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-roost-600'}))
    smoking_ok = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-roost-600'}))
    guests_ok = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'rounded border-slate-300 text-roost-600'}))
    display_name = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g. Alex'}))

    def clean(self):
        data = super().clean()
        if data.get('savings_type') == 'cad':
            data['savings_rate_cad'] = data.get('savings_cad')
            data['savings_rate_pct'] = None
        else:
            data['savings_rate_cad'] = None
            data['savings_rate_pct'] = data.get('savings_pct')
        return data
