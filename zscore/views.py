from sleep.models import SleeperProfile
from django.contrib.auth.models import User
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from zscore.forms import *

def css(request):
    return render(request, 'zscore.css')

@login_required
def emailConfirm(request, sha):
    return render_to_response('activateEmail.html', {"success": request.user.sleeperprofile.activateEmail(sha)}, context_instance=RequestContext(request))

@login_required
def editEmail(request, success=False):
    user = request.user
    context = {}
    if request.method == 'POST':
        form = genEmailShaForm(request.POST)
        if form.is_valid():
            if user.sleeperprofile.genEmailSha(newemail = form.cleaned_data["email"]): return HttpResponseRedirect("/editemail/success/")
            context["timeout"] = True
            print "hi"
    else:
        form = genEmailShaForm(initial = {"email": user.email})
    context.update({"form": form,
            "success": success})
    return render_to_response('editEmail.html', context, context_instance=RequestContext(request))



