# Create your views here.

from django.template import RequestContext
from django.shortcuts import render_to_response

def sheeple(request):
    return render_to_response('sheeple.html',{},context_instance=RequestContext(request))
