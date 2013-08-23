from django import forms
from sleep.models import *
from django.core.exceptions import *

import pytz
import datetime

class GroupForm(forms.ModelForm):
    delete = forms.BooleanField(required=False)

    class Meta:
        model=SleeperGroup
        fields = ['name', 'privacy', 'description']

class SleeperProfileForm(forms.ModelForm):
    idealWakeupWeekend = forms.CharField(max_length=30)
    idealWakeupWeekday = forms.CharField(max_length=30)

    idealSleepTimeWeekend = forms.CharField(max_length=30)
    idealSleepTimeWeekday = forms.CharField(max_length=30)
    
    class Meta:
        model = SleeperProfile
        fields = ['privacy','privacyLoggedIn','privacyFriends', 'use12HourTime', 'idealSleep', 'timezone', 'useGravatar', 'autoAcceptGroups',
                'idealWakeupWeekend', 'idealWakeupWeekday', 'idealSleepTimeWeekday', 'idealSleepTimeWeekend', 'mobile', 'punchInDelay', 'metrics']

    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        super(SleeperProfileForm, self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(SleeperProfileForm, self).clean()
        for k in ['idealWakeupWeekend', 'idealWakeupWeekday', 'idealSleepTimeWeekday', 'idealSleepTimeWeekend']:
            try:
                cleaned_data[k] = datetime.datetime.strptime(cleaned_data[k], self.fmt).time()
            except ValueError:
                self._errors[k] = self.error_class(["The time must be in the format %s" % datetime.time(23,59,59).strftime(self.fmt)])
                del cleaned_data[k]
        return cleaned_data

class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['privacy']

class SleeperSearchForm(forms.Form):
    username = forms.CharField(max_length=30)

class GroupSearchForm(forms.Form):
    group = forms.CharField(max_length=30)

class AllNighterForm(forms.ModelForm):
    delete = forms.BooleanField(required=False)
    class Meta:
        model = Allnighter
        fields = ["date", "comments"]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AllNighterForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AllNighterForm,self).clean()
        s = self.user.sleep_set.filter(date=cleaned_data["date"])
        if len(s) > 0: raise ValidationError({NON_FIELD_ERRORS: ["You have sleeps entered for " + str(cleaned_data["date"]) + "!"]})
        return cleaned_data

class SleepForm(forms.ModelForm):
    start_time = forms.CharField(max_length=30)
    end_time = forms.CharField(max_length=30)
    delete = forms.BooleanField(required=False)
    class Meta:
        model = Sleep
        fields = ['start_time','end_time', 'date', 'comments', 'timezone', 'quality']

    def __init__(self, user, fmt, *args, **kwargs):
        self.fmt = fmt
        self.user = user
        super(SleepForm,self).__init__(*args, **kwargs)

    def clean(self):
        if 'delete' in self.data and self.data['delete'] =='on': return {'delete': 'on' } #Skip validation, I don't actually care if I'm deleting
        cleaned_data = super(SleepForm,self).clean()
        a = self.user.allnighter_set.filter(date=cleaned_data["date"])
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
            if len(a) > 0 : raise ValidationError({NON_FIELD_ERRORS: ["You have an allnighter entered for " + str(cleaned_data["date"]) + "!"]})
            if "start_time" in cleaned_data and "end_time" in cleaned_data and cleaned_data["start_time"] >= cleaned_data["end_time"]: raise ValidationError({NON_FIELD_ERRORS: ["End time must be later than start time!"]})
        return cleaned_data
