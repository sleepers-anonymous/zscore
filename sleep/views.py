from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core import serializers
from django.db.models import Q

from sleep.models import *
from sleep.forms import *

import datetime

def home(request):
    return render(request, 'index.html')

def faq(request):
    return render(request, 'faq.html')

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('sleep/mysleep.html',{},context_instance=RequestContext(request)))

@login_required
def editSleep(request,sleep):
    context = {}
    sleep = Sleep.objects.filter(pk=sleep)
    if sleep.count() != 1:
        print sleep.count()
        return render(request, "editsleepfailed.html")
    user = Sleeper.objects.get(pk=request.user.pk)
    tformat = "%I:%M %p %x" if user.getOrCreateProfile().use12HourTime else "%H:%M %x" 
    if sleep[0].user.pk != user.pk:
        return render(request, "editsleepfailed.html")
    if request.method == 'POST':
        form = UpdateSleepForm(request.POST, instance=sleep[0])
        try:
            form.is_valid()
            form.save()
            context["successfulSave"] = True
            context["sleep"] = sleep[0]
            context["form"] = form
            context.update({ "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
            return HttpResponse(render_to_string('editsleep.html',context,context_instance=RequestContext(request)))
        except:
            context["successfulSave"] = False
            context["saveError"] = "overlapping"
            context.update({ "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
            return HttpResponse(render_to_string('editsleep.html', context, context_instance=RequestContext(request)))
    else:
        form = UpdateSleepForm(instance = sleep[0])
        context.update({"form":form, "sleep": sleep[0], "start": sleep[0].start_time.strftime(tformat), "end": sleep[0].end_time.strftime(tformat)})
        return HttpResponse(render_to_string('editsleep.html', context, context_instance=RequestContext(request)))

def leaderboard(request,sortBy='zScore'):
    if sortBy not in ['zScore','avg','avgSqrt']:
        sortBy='zScore'
    ss = Sleeper.objects.sorted_sleepers(sortBy,request.user)
    top = [ s for s in ss if s['rank']<=10 or request.user.is_authenticated() and s['user'].pk==request.user.pk ]
    context = {
            'top' : top,
            'total' : Sleep.objects.totalSleep(),
            'number' : Sleep.objects.all().values_list('user').distinct().count(),
            }
    return HttpResponse(render_to_string('leaderboard.html',context,context_instance=RequestContext(request)))

def creep(request,username=None, asOther=None):
    if not username:
        if request.user.is_anonymous():
            creepable=Sleeper.objects.filter(sleeperprofile__privacy__gte=SleeperProfile.PRIVACY_STATS)
            followed = []
        else:
            creepable=Sleeper.objects.filter(
                    Q(sleeperprofile__privacyLoggedIn__gte=SleeperProfile.PRIVACY_STATS) | 
                    (
                        Q(sleeperprofile__privacyFriends__gte=SleeperProfile.PRIVACY_STATS) &
                        Q(sleeperprofile__friends=request.user)
                    )
                )
            sleeper = Sleeper.objects.get(pk=request.user.pk)
            prof = sleeper.getOrCreateProfile()
            followed = prof.follows.all()
        total=creepable.distinct().count()
        if request.method == 'POST':
            form=CreepSearchForm(request.POST)
            if form.is_valid():
                users = creepable.filter(username__icontains=form.cleaned_data['username']).distinct()
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
                            'followed' : followed,
                            }
                    return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
        else:
            form = CreepSearchForm()
        context = {
                'form' : form,
                'new' : True,
                'total' : total,
                'followed' : followed,
                }
        return HttpResponse(render_to_string('creepsearch.html',context,context_instance=RequestContext(request)))
    else:
        context = {}
        try:
            user=Sleeper.objects.get(username=username)
            p = user.getOrCreateProfile()
            if user.is_anonymous():
                priv = p.privacy
            elif request.user.pk == user.pk:
                priv = p.PRIVACY_PUBLIC
                context["isself"] =True
            elif request.user in p.friends.all():
                priv = p.privacyFriends
            else:
                priv = p.privacyLoggedIn
            if asOther:
                otherD = {"friends":p.privacyFriends, "user": p.privacyLoggedIn,"anon": p.privacy}
                if asOther in otherD: priv = min(priv, otherD[asOther])
            if priv<=p.PRIVACY_NORMAL:
                return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        except:
            return HttpResponse(render_to_string('creepfailed.html',{},context_instance=RequestContext(request)))
        context.update({'user' : user,'global' : user.decayStats()})
        if priv>=p.PRIVACY_PUBLIC:
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
def friends(request):
    sleeper = Sleeper.objects.get(pk=request.user.pk)
    prof = sleeper.getOrCreateProfile()
    friended = prof.friends.all()
    followed = prof.follows.all()
    if request.method == 'POST':
        form=FriendSearchForm(request.POST)
        if form.is_valid():
            users = User.objects.filter(username__icontains=form.cleaned_data['username']).exclude(pk=request.user.pk).distinct()
            count = users.count()
            context = {
                    'results' : users,
                    'count' : count,
                    'form' : form,
                    'new' : False,
                    'friended' : friended,
                    'followed' : followed,
                    }
            return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
    else:
        form = FriendSearchForm()
    context = {
            'form' : form,
            'new' : True,
            'friended' : friended,
            'followed' : followed,
            }
    return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
            
@login_required
def addFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.friends.add(i)
        prof.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def removeFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.friends.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def follow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.follows.add(i)
        prof.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def unfollow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            return HttpResponseNotFound('')
        sleeper = Sleeper.objects.get(pk=request.user.pk)
        prof = sleeper.getOrCreateProfile()
        prof.follows.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def createSleep(request):
    # Date-ify start, end, and center
    start = datetime.datetime(*(map(int, request.POST.getlist("start[]"))))
    end = datetime.datetime(*(map(int, request.POST.getlist("end[]"))))
    date = datetime.date(*(map(int, request.POST.getlist("date[]"))[:3]))
    # Pull out comments
    if "comments" in request.POST:
        comments = request.POST["comments"]
    else:
        comments = ""
    # Create the Sleep instance
    Sleep.objects.create(user=request.user, start_time=start, end_time=end, comments=comments, date=date)
    return HttpResponse('')

@login_required
def deleteSleep(request):
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

@login_required
def getSleepsJSON(request):
    u = request.user
    sleeps = Sleep.objects.filter(user=u)
    data = serializers.serialize('json', sleeps)
    return HttpResponse(data, mimetype='application/json')
