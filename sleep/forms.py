from django import forms
from sleep.models import SleeperProfile, Sleep, Allnighter
from django.core.exceptions import *

import pytz
import datetime

class SleeperProfileForm(forms.ModelForm):
    idealWakeupWeekend = forms.Charfield(max_length=30)
    idealWakeupWeekday = forms.Charfield(max_length=30)
    idealSleepTimeWeekend = forms.Charfield(max_length=30)
    idealSleepTimeWeekday = forms.Charfield(max_length=30)

    class Meta:
        model = SleeperProfile
        fields = ['privacy',
                'privacyLoggedIn','privacyFriends', 'use12HourTime', 'idealSleep', 'timezone', 'idealWakeupWeekend', 'idealWakeupWeekday', 'idealSleepTimeWeekend', 'idealSleepTimeWeekday']

    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        super(SleepForm, self).__init__(*args, **kwargs)

    
    def clean(self):
        cleaned_data = super(SleepForm, self).clean()
        return cleaned_data

class CreepSearchForm(forms.Form):
    username = forms.CharField(max_length=30)

class FriendSearchForm(forms.Form):
    username = forms.CharField(max_length=30)

class AllNighterForm(forms.ModelForm):
    class Meta:
        model = Allnighter
        fields = ["date", "comments"]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AllNighterForm, self).__init(*args, **kwargs)

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
                    self._errors[k] = self.error_class(["The time must be in the format %s" % datetime.datetime(1999, 12, 31, 23, 59, 59).strftime(self.fmt)])
                    del cleaned_data[k]
            if cleaned_data["start_time"] >= cleaned_data["end_time"]: raise ValidationError({NON_FIELD_ERRORS: ["End time must be later than start time!"]})
        return cleaned_data
