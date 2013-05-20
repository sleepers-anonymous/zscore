from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from sleep.models import Sleep, Sleeper

import datetime

def home(request):
    return render(request, 'index.html')

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('mysleep.html',{},context_instance=RequestContext(request)))

def leaderboard(request):
    ss = Sleeper.objects.sorted_sleepers()
    top = [ s for s in ss if s['rank']<=10 or not request.user.is_anonymous() and s['user'].pk==request.user.pk ]
    context = { 'top' : top }
    return HttpResponse(render_to_string('leaderboard.html',context))

@login_required
def submitSleep(request):
    # TODO: Accept comments
    # Date-ify start, end, and center
    start = datetime.datetime(*(map(int, request.POST.getlist("start[]"))))
    end = datetime.datetime(*(map(int, request.POST.getlist("end[]"))))
    center = datetime.date(*(map(int, request.POST.getlist("center[]"))[:3]))
    # Create the Sleep instance
    Sleep.objects.create(user=request.user, start_time=start, end_time=end, comments="", date=center)
    return HttpResponse('')

@login_required
def deleteSleep(request):
    print "deleteSleep"
    if 'id' in request.POST:
        i = request.POST['id']
        s = Sleep.objects.filter(pk=i)
        if len(s) == 0:
            return HttpResponseNotFound('')
        s = s[0]
        if s.user != request.user:
            return HttpResponseForbidden('')
        s.delete()
        return HttpResponse('')
    return HttpResponseBadRequest('')
