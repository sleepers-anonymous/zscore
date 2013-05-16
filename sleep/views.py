from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import datetime

def home(request):
    return HttpResponse(render_to_string('index.html'))

def mysleep(request):
    return HttpResponse(render_to_string('mysleep.html'))

def leaderboard(request):
    return HttpResponse(render_to_string('leaderboard.html'))

def submitSleep(request):
    start = datetime(*(map(int, request.POST.getlist("start[]"))))
    end = datetime(*(map(int, request.POST.getlist("end[]"))))
    center = datetime(*(map(int, request.POST.getlist("center[]"))))
    print "start", start
    print "end", end
    print "center", center
    return HttpResponse('')
