from django import forms
from sleep.models import SleeperProfile, Sleep

import pytz
import datetime

class SleeperProfileForm(forms.ModelForm):
    class Meta:
        model = SleeperProfile
        fields = ['privacy','privacyLoggedIn','privacyFriends', 'use12HourTime', 'idealSleep', 'timezone']

class CreepSearchForm(forms.Form):
    username = forms.CharField(max_length=30)

class FriendSearchForm(forms.Form):
    username = forms.CharField(max_length=30)

class SleepForm(forms.ModelForm):
    start_time = forms.CharField(max_length=30)
    end_time = forms.CharField(max_length=30)
    class Meta:
        model = Sleep
        fields = ['start_time','end_time', 'date', 'comments', 'timezone']

    def __init__(self, user, fmt, *args, **kwargs):
        self.fmt = fmt
        self.user = user
        super(SleepForm,self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SleepForm,self).clean()
        if 'timezone' in cleaned_data and 'start_time' in cleaned_data and 'end_time' in cleaned_data:
            tz = pytz.timezone(cleaned_data['timezone'])
            for k in ['start_time','end_time']:
                #manually convert the strf-ed time to a datetime.datetime so we can make sure to do it in the right timezone
                try:
                    dt = datetime.datetime.strptime(cleaned_data[k],self.fmt)
                    cleaned_data[k]=tz.localize(dt)
                except ValueError:
                    self._errors[k] = self.error_class(["The time must be in the format %s" % datetime.datetime.now().strftime(self.fmt)])
                    del cleaned_data[k]
            if 'start_time' in cleaned_data and 'end_time' in cleaned_data:
                overlaps = Sleep.objects.filter(start_time__lt=cleaned_data['end_time'],end_time__gt=cleaned_data['start_time'],user=self.user)
                if overlaps:
                    raise forms.ValidationError("This sleep overlaps with %s!" % overlaps[0])
        return cleaned_data
