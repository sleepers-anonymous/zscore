#!/usr/bin/python
#This file is for all the static pages

from django.shortcuts import render
from django.http import HttpResponseRedirect

def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/mysleep/')
    else:
        return render(request, 'index.html')
