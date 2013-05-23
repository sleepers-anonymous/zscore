from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from sleep.models import *
from sleep.forms import *

import datetime

def home(request):
    return render(request, 'index.html')

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('mysleep.html',{},context_instance=RequestContext(request)))

def leaderboard(request,sortBy='zScore'):
    if sortBy not in ['zScore','avg','avgSqrt']:
        sortBy='zScore'
    ss = Sleeper.objects.sorted_sleepers(sortBy)
    if not request.user.is_anonymous() and request.user.pk not in [ s['user'].pk for s in ss ]:
        s = Sleeper.objects.get(pk=request.user.pk)
        d = s.movingStats()
        d['rank']='n/a'
        p=s.getOrCreateProfile()
        if p.privacy<=p.PRIVACY_REDACTED:
            s.displayName="[redacted]"
        else:
            s.displayName=sleeper.username
        d['user']=s
        ss.append(d)
    top = [ s for s in ss if s['rank']<=10 or not request.user.is_anonymous() and s['user'].pk==request.user.pk ]
    context = {
            'top' : top,
            'total' : Sleep.objects.totalSleep(),
            'number' : Sleep.objects.all().values_list('user').distinct().count(),
            }
    return HttpResponse(render_to_string('leaderboard.html',context,context_instance=RequestContext(request)))

def creep(request,username=None):
    if not username:
        total=Sleeper.objects.filter(sleeperprofile__privacy__gte=SleeperProfile.PRIVACY_STATS).count()
        if request.method == 'POST':
            form=CreepSearchForm(request.POST)
            if form.is_valid():
                users = Sleeper.objects.filter(username__icontains=form.cleaned_data['username'],sleeperprofile__privacy__gte=SleeperProfile.PRIVACY_STATS)
                count = users.count()
                if count==1:
                    return HttpResponseRedirect('/creep/%s/' % users[0].username)
                else: 
                    context = {
                            'results' : users,
                            'count' : count,
                            'form' : form,
                            'new' : False,
                            'total' : total,
                            }
                    return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
        else:
            form = CreepSearchForm()
        context = {
                'form' : form,
                'new' : True,
                'total' : total,
                }
        return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
    else:
        try:
            user=Sleeper.objects.get(username=username)
            p = user.getOrCreateProfile()
            if p.privacy<=p.PRIVACY_NORMAL:
                return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        except:
            return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        context = {
                'user' : user,
                'global' : user.movingStats(),
                }
        if p.privacy>=p.PRIVACY_PUBLIC:
            context['sleeps']=user.sleep_set.all().order_by('-end_time')
        return HttpResponse(render_to_string('creep.html',context,context_instance=RequestContext(request)))

@login_required
def editProfile(request):
    sleeper = Sleeper.objects.get(pk=request.user.pk)
    p = sleeper.getOrCreateProfile()
    if request.method == 'POST':
        form = SleeperProfileForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/editprofile/')
    else:
        form = SleeperProfileForm(instance=p)

    return HttpResponse(render_to_string('editprofile.html', {'form': form},context_instance=RequestContext(request)))
            

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
