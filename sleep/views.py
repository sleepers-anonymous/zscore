from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core import serializers
from django.db.models import Q
from django.core.exceptions import *

from sleep.models import *
from sleep.forms import *

import datetime
import pytz

def home(request):
    return render(request, 'index.html')

def faq(request):
    return render(request, 'faq.html')

@login_required
def mysleep(request):
    return HttpResponse(render_to_string('sleep/mysleep.html',{},context_instance=RequestContext(request)))

@login_required
def editOrCreateSleep(request,sleep = None,success=False):
    context = {'success': success}
    prof = request.user.sleeperprofile
    defaulttz = prof.timezone
    if prof.use12HourTime:
        fmt = "%I:%M %p %x"
    else:
        fmt = "%H:%M %x"
    if sleep: # we're editing a sleep
        try:
            s = Sleep.objects.get(pk=sleep)
            if s.user != request.user:
                raise PermissionDenied
            context['sleep'] = s
        except Sleep.MultipleObjectsReturned:
            return HttpResponseBadRequest('')
        except Sleep.DoesNotExist:
            raise Http404
        if request.method == 'POST':
            form = SleepForm(request.user, fmt, request.POST, instance=s)
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
    return HttpResponse(render_to_string('editsleep.html', context, context_instance=RequestContext(request)))


def leaderboard(request,sortBy='zScore'):
    if sortBy not in ['zScore','avg','avgSqrt','avgLog','avgRecip','stDev']:
        sortBy='zScore'
    ss = Sleeper.objects.sorted_sleepers(sortBy,request.user)
    top = [ s for s in ss if s['rank']<=10 or request.user.is_authenticated() and s['user'].pk==request.user.pk ]
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    lastDayWinner = Sleeper.objects.bestByTime(now-datetime.timedelta(1),now,request.user)[0]
    context = {
            'top' : top,
            'lastDayWinner' : lastDayWinner,
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
            followed = request.user.sleeperprofile.follows.order_by('username')
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
            p = user.sleeperprofile
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
    p = request.user.sleeperprofile
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
    prof = request.user.sleeperprofile
    friendfollow = (prof.friends.all() | prof.follows.all()).distinct().order_by('username')
    requests = sleeper.requests.filter(friendrequest__accepted=None).order_by('user__username')
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
            return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
    else:
        form = FriendSearchForm()
    context = {
            'form' : form,
            'new' : True,
            'friendfollow' : friendfollow,
            'requests' : requests,
            }
    return HttpResponse(render_to_string('friends.html',context,context_instance=RequestContext(request)))
            
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
            FriendRequest.objects.create(requestor=prof,requestee=them,accepted=accept)
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
