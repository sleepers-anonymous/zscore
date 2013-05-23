from django.forms import ModelForm
from sleep.models import SleeperProfile

class SleeperProfileForm(ModelForm):
    class Meta:
        model = SleeperProfile
        fields = ['privacy']

