#!/usr/bin/python

#This file is for anything related to sleeperprofiles

from django import forms
from sleep.models import *
from django.core.exceptions import *

import pytz
import datetime

from widgets import * #custom widgets

class SleeperProfileForm(forms.ModelForm):
    idealWakeupWeekend = forms.CharField(max_length=30)
    idealWakeupWeekday = forms.CharField(max_length=30)

    idealSleepTimeWeekend = forms.CharField(max_length=30)
    idealSleepTimeWeekday = forms.CharField(max_length=30)
    
    class Meta:
        model = SleeperProfile
        fields = ['privacy','privacyLoggedIn','privacyFriends', 'partyMode', 'use12HourTime', 'idealSleep', 'timezone', 'useGravatar', 'autoAcceptGroups',
                'idealWakeupWeekend', 'idealWakeupWeekday', 'idealSleepTimeWeekday', 'idealSleepTimeWeekend', 'mobile', 'punchInDelay', 'metrics']

        widgets = {'metrics': CheckboxSelectMultipleULAttrs(ulattrs={'class':'checkboxselectmultiple'})}

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

