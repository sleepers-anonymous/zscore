#!/usr/bin/python

#For any forms that have to do with groups or memberships

from django import forms
from sleep.models import *
from django.core.exceptions import *

class GroupForm(forms.ModelForm):
    delete = forms.BooleanField(required=False)

    class Meta:
        model=SleeperGroup
        fields = ['name', 'privacy', 'description']

class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['privacy']

class GroupSearchForm(forms.Form):
    group = forms.CharField(max_length=30)

