from django.template.loader import render_to_string
from django.http import HttpResponse

def home(request):
    return HttpResponse(render_to_string('index.html'))

def mysleep(request):
    return HttpResponse(render_to_string('mysleep.html'))

def leaderboard(request):
    return HttpResponse(render_to_string('leaderboard.html'))
