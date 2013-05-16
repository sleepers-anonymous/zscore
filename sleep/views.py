from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from sleep.models import Sleep

import datetime

def home(request):
    return HttpResponse(render_to_string('index.html'))

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('mysleep.html'))

def leaderboard(request):
    return HttpResponse(render_to_string('leaderboard.html'))

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
