from django import forms
from sleep.models import *
from django.core.exceptions import *

class genEmailShaForm(forms.Form):
    email = forms.EmailField()
