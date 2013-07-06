from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.core import serializers
from django.db.models import Q
from django.db import IntegrityError
from django.core.exceptions import *

from sleep.models import *
from sleep.forms import *

from zscore import settings

import datetime
import pytz

def home(request):
    context = {}
    try:
        p = request.user.partialsleep
        context["Partial"] = '<a style="text-decoration:none;" href="/sleep/finishPartial"><input type="submit" value="Waking Up!" /></a>'
    except PartialSleep.DoesNotExist:
        context["Partial"] = '<a style="text-decoration:none;" href="/sleep/createPartial"><input type="submit" value="Going to Sleep!" /></a>'
    return render_to_response('index.html', context, context_instance=RequestContext(request))

def faq(request):
    return render(request, 'faq.html')

@login_required
def mysleep(request):
    return render_to_response('sleep/mysleep.html',{},context_instance=RequestContext(request))

@login_required
def editOrCreateAllnighter(request, allNighter = None, success=False):
    context = {'success': success}
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if allNighter: #We're editing an allnighter
        context = {"editing": True}
        try:
            a = Allnighter.objects.get(pk=allNighter)
            if a.user != request.user: raise PermissionDenied
            context['allnighter'] = a
        except Allnighter.MultipleObjectsReturned: return HttpResponseBadRequest('')
        except Allnighter.DoesNotExist: raise Http404
        if request.method == 'POST':
            form = AllNighterForm(request.user, request.POST, instance = a)
        else:
            form = AllNighterForm(request.user, instance=a, initial={"date": a.date})
        context["date"] = a.date.strftime("%x")
    else: #we're creating a new allnighter
        if request.method == "POST":
            form = AllNighterForm(request.user, request.POST, instance = Allnighter(user=request.user))
        else:
            today = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone(defaulttz)).replace(hour=0,minute=0,second=0,microsecond=0)
            form = AllNighterForm(request.user, initial={"date": str(today.date())})
    if request.method == "POST":
        if form.is_valid():
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
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if prof.use12HourTime: fmt = "%I:%M %p %x"
    else: fmt = "%H:%M %x"
    if sleep: # we're editing a sleep
        try:
            s = Sleep.objects.get(pk=sleep)
            if s.user != request.user: raise PermissionDenied
            context['sleep'] = s
        except Sleep.MultipleObjectsReturned:
            return HttpResponseBadRequest('')
        except Sleep.DoesNotExist:
            raise Http404
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
            today = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone(defaulttz)).replace(hour=0,minute=0,second=0,microsecond=0)
            initial = {
                    "start_time" : today.strftime(fmt),
                    "end_time" : today.strftime(fmt),
                    "date" : today.date().strftime("%x"),
                    "timezone" : defaulttz,
                    }
            form = SleepForm(request.user, fmt, initial=initial)
    if request.method == 'POST':
        if form.is_valid():
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

def leaderboardLegacy(request,sortBy):
    return HttpResponsePermanentRedirect('/leaderboard/?sort=%s' % sortBy)

@login_required
def graph(request):
    return render_to_response('graph.html', {"user": request.user, "sleeps": request.user.sleep_set.all().order_by('-end_time')}, context_instance=RequestContext(request))

def leaderboard(request):
    if 'sort' not in request.GET or request.GET['sort'] not in ['zScore','avg','avgSqrt','avgLog','avgRecip','stDev', 'idealDev']:
        sortBy='zScore'
    else:
        sortBy=request.GET['sort']
    ss = Sleeper.objects.sorted_sleepers(sortBy,request.user)
    top = [ s for s in ss if s['rank']<=10 or request.user.is_authenticated() and s['user'].pk==request.user.pk ]
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    lastDayWinner = Sleeper.objects.bestByTime(now-datetime.timedelta(1),now,request.user)[0]
    context = {
            'top' : top,
            'lastDayWinner' : lastDayWinner,
            'total' : Sleep.objects.totalSleep(),
            'number' : Sleep.objects.all().values_list('user').distinct().count(),
            'leaderboard_valid': len(ss),
            }
    return render_to_response('leaderboard.html',context,context_instance=RequestContext(request))

def creep(request,username=None):
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
            followed = request.user.sleeperprofile.follows.order_by('username')
        total=creepable.distinct().count()
        if request.method == 'POST':
            form=CreepSearchForm(request.POST)
            if form.is_valid():
                users = creepable.filter(username__icontains=form.cleaned_data['username']).distinct()
                count = users.count()
                if count==1: return HttpResponseRedirect('/creep/%s/' % users[0].username)
                else:
                    context = {
                            'results' : users,
                            'count' : count,
                            'form' : form,
                            'new' : False,
                            'total' : total,
                            'followed' : followed,
                            }
                    return render_to_response('creepsearch.html',context,context_instance=RequestContext(request))
        else:
            form = CreepSearchForm()
        context = {
                'form' : form,
                'new' : True,
                'total' : total,
                'followed' : followed,
                }
        return render_to_response('creepsearch.html',context,context_instance=RequestContext(request))
    else:
        context = {}
        try:
            user=Sleeper.objects.get(username=username)
            p = user.sleeperprofile
            priv = p.getPermissions(request.user, request.GET.get("as", None))
            if not(request.user.is_anonymous()) and request.user.pk == user.pk: context["isself"] =True
            if priv<=p.PRIVACY_NORMAL: return render_to_response('creepfailed.html',{},context_instance=RequestContext(request))
        except:
            return render_to_response('creepfailed.html',{},context_instance=RequestContext(request))
        context.update({'user' : user,'global' : user.decayStats()})
        if priv>=p.PRIVACY_PUBLIC: context['sleeps']=user.sleep_set.all().order_by('-end_time')
        if priv>=p.PRIVACY_GRAPHS:
            if "type" in request.GET and request.GET["type"] == "graph": return render_to_response('graph.html',context,context_instance=RequestContext(request))
            context["graphs"] = True
        return render_to_response('creep.html',context,context_instance=RequestContext(request))

@login_required
def editProfile(request):
    p = request.user.sleeperprofile
    if p.use12HourTime: fmt = "%I:%M %p"
    else: fmt = "%H:%M"
    if request.method == 'POST':
        form = SleeperProfileForm(fmt, request.POST, instance=p)
        context = {"form":form}
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/editprofile/?success=True')
        else:
            print form.errors.viewkeys()
            for k in form.errors.viewkeys():
                if "ideal" in k:
                    context["page"] = 2
                    break
    else:
        initial = {"idealWakeupWeekend": p.idealWakeupWeekend.strftime(fmt),
                "idealWakeupWeekday": p.idealWakeupWeekday.strftime(fmt),
                "idealSleepTimeWeekend": p.idealSleepTimeWeekend.strftime(fmt),
                "idealSleepTimeWeekday": p.idealSleepTimeWeekday.strftime(fmt),}
        form = SleeperProfileForm(fmt, instance=p, initial = initial)
        context = {"form":form}
        if "success" in request.GET and request.GET["success"] == "True": context["success"] = True
    return render_to_response('editprofile.html', context ,context_instance=RequestContext(request))

@login_required
def friends(request):
    prof = request.user.sleeperprofile
    friendfollow = (prof.friends.all() | prof.follows.all()).distinct().order_by('username')
    requests = request.user.requests.filter(friendrequest__accepted=None).order_by('user__username')
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
                    'friendfollow' : friendfollow,
                    'requests' : requests,
                    }
            return render_to_response('friends.html',context,context_instance=RequestContext(request))
    else:
        form = FriendSearchForm()
    context = {
            'form' : form,
            'new' : True,
            'friendfollow' : friendfollow,
            'requests' : requests,
            }
    return render_to_response('friends.html',context,context_instance=RequestContext(request))
            
@login_required
def requestFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        them = Sleeper.objects.get(pk=i)
        if not FriendRequest.objects.filter(requestor=request.user.sleeperprofile,requestee=them):
            if request.user in them.sleeperprofile.friends.all():
                accept = True
            else:
                accept = None
            FriendRequest.objects.create(requestor=request.user.sleeperprofile,requestee=them,accepted=accept)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def hideRequest(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        frs = FriendRequest.objects.filter(requestor__user__pk=i,requestee=request.user)
        for fr in frs:
            fr.accepted=False
            fr.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def addFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        prof = request.user.sleeperprofile
        prof.friends.add(i)
        prof.save()
        frs = FriendRequest.objects.filter(requestor__user__pk=i,requestee=request.user)
        for fr in frs:
            fr.accepted=True
            fr.save()
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def removeFriend(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        prof = request.user.sleeperprofile
        prof.friends.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def follow(request):
    if 'id' in request.POST:
        i = request.POST['id']
        if i==request.user.pk or len(User.objects.filter(pk=i))!=1:
            raise Http404
        prof = request.user.sleeperprofile
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
            raise Http404
        prof = request.user.sleeperprofile
        prof.follows.remove(i)
        return HttpResponse('')
    else:
        return HttpResponseBadRequest('')

@login_required
def createSleep(request):
    # Date-ify start, end, and center
    timezone = pytz.timezone(request.POST['timezone'])
    start = datetime.datetime(*(map(int, request.POST.getlist("start[]"))))
    start=timezone.localize(start)
    end = datetime.datetime(*(map(int, request.POST.getlist("end[]"))))
    end=timezone.localize(end)
    date = datetime.date(*(map(int, request.POST.getlist("date[]"))[:3]))
    # Pull out comments
    if "comments" in request.POST:
        comments = request.POST["comments"]
    else:
        comments = ""
    # Create the Sleep instance
    Sleep.objects.create(user=request.user, start_time=start, end_time=end, comments=comments, date=date,timezone=timezone)
    return HttpResponse('')

@login_required
def createPartialSleep(request):
    timezone = request.user.sleeperprofile.timezone
    start = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.now()).astimezone(pytz.timezone(timezone))
    try:
        p = PartialSleep(user = request.user, start_time = start,timezone = timezone)
        p.save()
        return HttpResponseRedirect("/")
    except IntegrityError:
        return HttpResponseBadRequest('')

@login_required
def finishPartialSleep(request):
    timezone = request.user.sleeperprofile.timezone
    pytztimezone = pytz.timezone(timezone)
    try:
        p = request.user.partialsleep
        start = p.start_time.astimezone(pytztimezone)
        end = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.now()).astimezone(pytz.timezone(timezone))
        date = end.date()
        s = Sleep(user = request.user, start_time = start, end_time = end, date = date, timezone = timezone, comments = "")
        s.save()
        p.delete()
        return HttpResponseRedirect("/sleep/edit/" + str(s.pk) + "/?from=partial")
    except PartialSleep.DoesNotExist:
        return HttpResponseBadRequest('')

@login_required
def deleteSleep(request):
    if 'id' in request.POST:
        i = request.POST['id']
        s = Sleep.objects.filter(pk=i)
        if len(s) == 0:
            raise Http404
        s = s[0]
        if s.user != request.user:
            raise PermissionDenied
        s.delete()
        return HttpResponse('')
    return HttpResponseBadRequest('')

@login_required
def deleteAllnighter(request):
    if 'id' in request.POST:
        i = request.POST['id']
        a = request.user.allnighter_set.objects.filter(pk=i)
        if len(a) == 0: raise Http404
        a = a[0]
        print "hi"
        a.delete()
        return HttpResponse('')
    return HttpResponseBadRequest('')

@login_required
def getSleepsJSON(request):
    u = request.user
    sleeps = list(Sleep.objects.filter(user=u))
    for sleep in sleeps:
        tz = pytz.timezone(sleep.timezone)
        #warning: the following is kind of hacky but it's better than dealing with the timezones in JS.  JS doesn't understand timezones, so we convert the timezone server-side, then pass it through to JS without telling the JS what timezone it's in.  JS interprets it as local time, which is slightly incorrect but works since all we want to do is get the hours/minutes/seconds back out as local time.
        sleep.start_time=sleep.start_time.astimezone(tz).replace(tzinfo=None)
        sleep.end_time=sleep.end_time.astimezone(tz).replace(tzinfo=None)
    data = serializers.serialize('json', sleeps)
    return HttpResponse(data, mimetype='application/json')
