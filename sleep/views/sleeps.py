#!/usr/bin/python
#code that just deals with sleeps

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
def editOrCreateAllnighter(request, allNighter = None, success=False):
    context = {'success': success}
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if allNighter: #We're editing an allnighter
        context = {"editing": True}
        try:
            a = Allnighter.objects.get(pk=allNighter)
        except Allnighter.MultipleObjectsReturned:
            return HttpResponseBadRequest('')
        except Allnighter.DoesNotExist:
            raise Http404
        else:
            if a.user != request.user: raise PermissionDenied
            context['allnighter'] = a

        if request.method == 'POST':
            form = AllNighterForm(request.user, request.POST, instance = a)
        else:
            form = AllNighterForm(request.user, instance=a, initial={"date": a.date})
        context["date"] = a.date.strftime("%x")
    else: #we're creating a new allnighter
        if request.method == "POST":
            form = AllNighterForm(request.user, request.POST, instance = Allnighter(user=request.user))
        else:
            if "withdate" in request.GET:
                try:
                    defaultdate = datetime.datetime.strptime(request.GET["withdate"], "%Y%m%d").date()
                except:
                    defaultdate = prof.today()
            else:
                defaultdate = prof.today()
            form = AllNighterForm(request.user, initial={"date": str(defaultdate)})
    if request.method == "POST":
        if form.is_valid():
            if "delete" in form.data and form.data["delete"] == "on":
                if allNighter: a.delete()
                return HttpResponseRedirect('/mysleep/')
            new = form.save(commit=False)
            if allNighter == None:
                new.user = request.user
                new.save()
                form = AllNighterForm(request.user, instance=new)
                return HttpResponseRedirect('/sleep/allnighter/success/')
            else:
                new.save()
                return HttpResponseRedirect('/mysleep/')
    context['form']=form
    return render_to_response('editallnighter.html', context, context_instance=RequestContext(request))


@login_required
def editOrCreateSleep(request,sleep = None,success=False):
    context = {'success': success}
    if "from" in request.GET and request.GET["from"] == "partial": context["fromPartial"] = True
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if prof.use12HourTime: fmt = "%I:%M %p %x"
    else: fmt = "%H:%M %x"
    if sleep: # we're editing a sleep
        try:
            s = Sleep.objects.get(pk=sleep)
        except Sleep.MultipleObjectsReturned:
            return HttpResponseBadRequest('')
        except Sleep.DoesNotExist:
            raise Http404
        else:
            if s.user != request.user: raise PermissionDenied
            context['sleep'] = s
 
        if request.method == 'POST': form = SleepForm(request.user, fmt, request.POST, instance=s)
        else:
            initial = {
                    "start_time" : s.start_local_time().strftime(fmt),
                    "end_time" : s.end_local_time().strftime(fmt),
                    "date" : s.date.strftime("%x"),
                    }
            form = SleepForm(request.user, fmt, instance=s, initial=initial)
        context.update({"start": s.start_local_time().strftime(fmt), "end": s.end_local_time().strftime(fmt), "tz": s.timezone})
    else: # we're creating a new sleep
        if request.method == 'POST':
            form = SleepForm(request.user, fmt, request.POST, instance=Sleep(user=request.user))
        else:
            today = now().astimezone(pytz.timezone(defaulttz)).replace(hour=0,minute=0,second=0,microsecond=0)
            initial = {
                    "start_time" : today.strftime(fmt),
                    "end_time" : today.strftime(fmt),
                    "date" : today.date().strftime("%x"),
                    "timezone" : defaulttz,
                    }
            if "error" in request.GET:
                if request.GET["error"] == "partial":
                    context["partialError"] = True
                    try:
                        p = request.user.partialsleep
                        initial.update({"timezone": p.timezone, "start_time": p.start_local_time().strftime(fmt)})
                    except PartialSleep.DoesNotExist: pass
            form = SleepForm(request.user, fmt, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
            if "delete" in form.data and form.data["delete"] == "on":
                if sleep: s.delete()
                return HttpResponseRedirect('/mysleep/')
            new = form.save(commit=False)
            if sleep == None:
                new.user = request.user
                new.save()
                form = SleepForm(request.user, fmt, instance=new)
                return HttpResponseRedirect('/sleep/simple/success/')
            else:
                new.save()
                return HttpResponseRedirect('/mysleep/')
    context['form']=form
    return render_to_response('editsleep.html', context, context_instance=RequestContext(request))

