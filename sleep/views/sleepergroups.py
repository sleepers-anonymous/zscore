#!/usr/bin/python
#Code that has to do with sleepergroups

from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.core import serializers
from django.db.models import Q
from django.core.exceptions import *
from django.utils.timezone import now
from django.core.cache import cache

from sleep.models import *
from sleep.forms import *

import datetime
import pytz
import csv



@login_required
def groups(request):
    context = {
            'groups' : request.user.sleepergroups.all(),
            'invites' : request.user.groupinvite_set.filter(accepted=None),
            }
    if request.method =="POST":
        form = GroupSearchForm(request.POST)
        if form.is_valid():
            gs=SleeperGroup.objects.filter(name__icontains=form.cleaned_data['group'], privacy__gte=SleeperGroup.REQUEST).exclude(members=request.user)
            context['results']=gs
            if gs.count() == 0 : context["noresults"] = True
    else:
        form = GroupSearchForm()
    context["form"] = form
    return render_to_response('groups.html', context, context_instance=RequestContext(request))

